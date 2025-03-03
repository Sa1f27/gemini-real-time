# Gemini Voice Assistant

A practical tool for interacting with Google's AI through voice, camera, screen, and text. This project creates a seamless experience for communicating with an AI assistant using multiple input methods.

## What This Tool Does

- Talk to the AI using your microphone
- Type messages and get both text and voice responses
- Share your screen for visual assistance
- Use your camera for visual queries
- Works quickly with minimal delay
- Easily adjust settings to your preferences
- Keeps track of conversations for reference

## Before You Start

You'll need:

- A computer running Windows, Mac, or Linux
- Python 3.8 or newer
- Internet connection
- Microphone (for voice features)
- Google API credentials

## Setting Up

Follow these steps to get started:

1. **Download the code**
   ```bash
   git clone https://github.com/yourusername/gemini-voice-assistant.git
   ```

2. **Go to the project folder**
   ```bash
   cd gemini-voice-assistant
   ```

3. **Create a separate environment** (recommended)
   ```bash
   python -m venv env
   env\Scripts\activate
   ```

4. **Install required packages**
   ```bash
   pip install -r requirements.txt
   ```

5. **Set up your credentials**
   - Create a file named `.env` in the main folder
   - Add your Google API key:
     ```
     GOOGLE_API_KEY = your_api_key_here
     ```

6. In the main.py file, hash all mode examples and unhash just one at a time to use a specific feature:

```bash
# Examples:
# To run audio mode:
main(input_mode=INPUT_MODE_AUDIO)
    
# To run text mode:
# main(input_mode=INPUT_MODE_TEXT)
    
# To run camera mode:
# main(input_mode=INPUT_MODE_CAMERA)

# To run screen mode with monitor index:
# main(input_mode=INPUT_MODE_SCREEN, monitor_index=DEFAULT_MONITOR_INDEX)
```

## Using the Assistant

To talk with the assistant:
```bash
python main.py
```

## How It's Organized

```
gemini-real-time/
├── .env
├── .gitignore
├── main.py
├── requirements.txt
├── src/
    ├── config.py
    ├── handlers/
    │   ├── audio_handler.py
    │   ├── camera_handler.py
    │   ├── screen_handler.py
    │   └── text_handler.py
    ├── logs/
    │   └── app.log
    └── utils/
        └── logger.py
```

## Adjusting Settings

You can change how the assistant works by editing the `src/config.py` file:

- Change the AI model version
- Adjust audio quality settings
- Modify input/output preferences

## Common Problems

- **Audio not working**: Check your microphone connections and system permissions
- **Missing packages**: Run `pip install -r requirements.txt` again
- **API errors**: Verify your Google API key is correct and has proper permissions