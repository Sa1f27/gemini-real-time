import asyncio
import base64
import io
import traceback
import pyaudio
import PIL.Image
import mss
from google import genai
from src.config import (
    FORMAT,
    CHANNELS,
    SEND_SAMPLE_RATE,
    RECEIVE_SAMPLE_RATE,
    CHUNK_SIZE,
    MODEL,
    API_VERSION
)

# Import TaskGroup for compatibility with Python versions below 3.11
try:
    from asyncio import TaskGroup
except ImportError:
    from taskgroup import TaskGroup

SCREEN_HANDLER_PROMPT = (
    "You are an AI examiner assigning and evaluating a coding task for the user."
    "Start by greeting the user and providing a specific coding problem to solve (e.g., 'Write a Python function to reverse a string')."
    "Instruct them to write the code in a designated editor while you monitor their screen activity. "
    "Check their submitted code for correctness and efficiency, providing feedback on errors or improvements."
    "Simultaneously, watch for cheating behaviors, such as opening other tabs, copying code from external sources, or asking another AI for help."
    "If you detect suspicious activity, issue a polite warning like 'I noticed you opened another tab—please focus on your task' or 'It seems you’re seeking external help;"
    "please solve this independently.' Log violations internally and provide a final evaluation of their work."
)

class ScreenHandler:
    def __init__(self, logger, monitor_index=1):
        self.logger = logger
        self.monitor_index = monitor_index  # Store the monitor index
        self.audio_out_queue = asyncio.Queue()
        self.out_queue = asyncio.Queue(maxsize=5)
        self.ai_speaking = False
        self.client = genai.Client(http_options={"api_version": API_VERSION})
        self.CONFIG = {"generation_config": {
                            "response_modalities": ["AUDIO"],
                            "system_instruction": SCREEN_HANDLER_PROMPT
                            }}
        self.pya = pyaudio.PyAudio()

    async def _get_screen(self):
        with mss.mss() as sct:
            monitors = sct.monitors
            if self.monitor_index < 1 or self.monitor_index >= len(monitors):
                print(f"Monitor index {self.monitor_index} is out of range. Available monitors:")
                for idx, monitor in enumerate(monitors[1:], start=1):
                    print(f"Monitor {idx}: {monitor}")
                raise ValueError(f"Invalid monitor index: {self.monitor_index}")

            monitor = monitors[self.monitor_index]
            sct_img = sct.grab(monitor)

            # Convert the screenshot to a PIL Image
            img = PIL.Image.frombytes('RGB', sct_img.size, sct_img.rgb)
            img.thumbnail([1024, 1024])

            image_io = io.BytesIO()
            img.save(image_io, format="jpeg")
            image_io.seek(0)

            mime_type = "image/jpeg"
            image_bytes = image_io.read()
            return {"mime_type": mime_type, "data": base64.b64encode(image_bytes).decode()}

    async def get_frames(self):
        try:
            print(f"Capturing screenshots from monitor {self.monitor_index}...")
            while True:
                frame = await self._get_screen()
                if frame is not None:
                    await self.out_queue.put(frame)
                await asyncio.sleep(1.0)  # Adjust the capture rate as needed
        except Exception as e:
            traceback.print_exc()
        finally:
            print("Stopped capturing screenshots.")

    async def send_realtime(self, session):
        try:
            while True:
                msg = await self.out_queue.get()
                await session.send(input = msg)
        except Exception as e:
            traceback.print_exc()

    async def listen_audio(self):
        mic_info = self.pya.get_default_input_device_info()
        audio_stream = self.pya.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=SEND_SAMPLE_RATE,
            input=True,
            input_device_index=mic_info["index"],
            frames_per_buffer=CHUNK_SIZE,
        )
        try:
            print("Listening... You can speak now.")
            while True:
                if not self.ai_speaking:
                    data = await asyncio.to_thread(
                        audio_stream.read, CHUNK_SIZE, exception_on_overflow=False
                    )
                    await self.out_queue.put({"data": data, "mime_type": "audio/pcm"})
                else:
                    await asyncio.sleep(0.1)
        except Exception as e:
            traceback.print_exc()
        finally:
            audio_stream.stop_stream()
            audio_stream.close()
            print("Stopped Listening.")

    async def receive_audio(self, session):
        """Receives audio responses from the AI session and queues them for playback."""
        try:
            while True:
                turn = session.receive()
                async for response in turn:
                    if data := response.data:
                        await self.audio_out_queue.put(data)
                    if text := response.text:
                        print(f"Assistant: {text}")
                # After the turn is complete, clear the audio queue to stop any ongoing playback
                while not self.audio_out_queue.empty():
                    self.audio_out_queue.get_nowait()
        except Exception as e:
            traceback.print_exc()

    async def play_audio(self):
        """Plays audio data received from the AI session."""
        audio_stream = self.pya.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RECEIVE_SAMPLE_RATE,
            output=True,
        )
        try:
            while True:
                data = await self.audio_out_queue.get()
                if not self.ai_speaking:
                    self.ai_speaking = True  # AI starts speaking
                    print("Assistant is speaking...")
                await asyncio.to_thread(audio_stream.write, data)
                if self.audio_out_queue.empty():
                    self.ai_speaking = False  # AI has finished speaking
                    print("You can speak now.")
        except Exception as e:
            traceback.print_exc()
        finally:
            audio_stream.stop_stream()
            audio_stream.close()

    async def run(self):
        """Initializes the AI session and starts all asynchronous tasks."""
        try:
            async with (
                self.client.aio.live.connect(model=MODEL, config=self.CONFIG) as session,
                TaskGroup() as tg,
            ):
                self.session = session

                # Create asynchronous tasks
                tg.create_task(self.get_frames())
                tg.create_task(self.listen_audio())
                tg.create_task(self.send_realtime(session))
                tg.create_task(self.receive_audio(session))
                tg.create_task(self.play_audio())

                # Keep the main coroutine alive
                await asyncio.Event().wait()

        except asyncio.CancelledError:
            pass
        except Exception as e:
            traceback.print_exc()

    def close(self):
        """Closes resources."""
        self.pya.terminate()