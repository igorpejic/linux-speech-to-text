# Speech-to-Text Keyboard Button

This project provides a script to add a speech-to-text functionality to your keyboard, allowing you to transcribe your voice into text. It's particularly useful for those who have difficulty typing or want to experiment with voice input.

## How It Works

The script combines several components to achieve speech-to-text functionality:

1. **Recording**: Uses `arecord` to capture audio from your microphone.
2. **Transcription**: Sends the recorded audio to OpenAI's Whisper API for transcription.
3. **Text Input**: Uses `xdotool` to type the transcribed text into the active window.

The script is designed to be triggered twice:
- First execution: Starts the recording
- Second execution: Stops the recording, transcribes the audio, and types the result

## Requirements

- Linux operating system
- `curl`
- `jq`
- `arecord`
- `xdotool`
- `killall`
- An OpenAI API key (for the Whisper transcription service)

## Configuration

Before using the script, you need to set up a few configuration variables:

Required:

- `AUDIO_INPUT`: Your microphone device (use `arecord -l` to list available devices)
- `OPEN_AI_TOKEN`: Your OpenAI API key (should be set as an environment variable)

Optional: 

- `PID_FILE`: Location to store the process ID of the recording
- `FILE`: Base path for temporary files
- `MAX_DURATION`: Maximum recording duration in seconds

## Usage

1. Save the script to a file (e.g., `record.bash`).
2. Make it executable: `chmod +x record.bash`
3. Set up a keyboard shortcut in your Linux distribution to execute the script.
4. Press the shortcut once to start recording.
5. Press it again to stop recording and transcribe the audio.

The transcribed text will be automatically typed into the active window.

## Customization

You can modify the script to use different transcription services or adjust the recording parameters. The original author mentions using Deepgram as an alternative to OpenAI's Whisper for faster transcriptions.

## Limitations

- The script is designed for Linux systems and may require modifications for other operating systems.
- Transcription accuracy depends on the quality of the audio input and the performance of the chosen API.
- There's a maximum recording duration to prevent excessively large files.

## Setting Up a Hotkey

To call the script using a hotkey from anywhere in Linux, you can follow these steps:

1. Ensure your script is saved in a convenient location, e.g., `/home/username/scripts/record.bash`.

2. Open your system's keyboard settings. This varies depending on your Linux distribution:
   - For GNOME: Go to Settings > Keyboard > View and Customize Shortcuts > Custom Shortcuts
   - For KDE: Go to System Settings > Shortcuts > Custom Shortcuts
   - For XFCE: Go to Settings Manager > Keyboard > Application Shortcuts

3. Add a new custom shortcut:
   - Set the command to the full path of your script, e.g., `/home/username/scripts/record.bash`
   - Assign F10 as the hotkey for this shortcut

4. Save the new shortcut.

Now you can use F10 from any application to start and stop the voice typing process.

Note: Make sure the script has executable permissions (`chmod +x /home/username/scripts/record.bash`).

For distributions that don't have a GUI for custom shortcuts, you can use tools like `xbindkeys` to achieve the same result:

1. Install xbindkeys: `sudo apt-get install xbindkeys`
2. Create a configuration file: `xbindkeys --defaults > ~/.xbindkeysrc`
3. Edit `~/.xbindkeysrc` and add a line like:
   ```
   "/home/username/scripts/record.bash"
     F10
   ```
4. Run `xbindkeys` to apply the configuration.

Remember to adjust the script path according to your system setup.


## Credits

This script is inspired by the work of Jérémie Chauvel, as described in his blog post ["Whisper to your keyboard: Setting up a speech-to-text button"](https://blog.theodo.com/2023/11/speech-to-text-keyboard-button/). 