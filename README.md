# Speech-to-Text Keyboard Button

This project provides scripts to add speech-to-text functionality to your keyboard, allowing you to transcribe your voice into text. It's particularly useful for those who have difficulty typing or want to experiment with voice input.

## How It Works

The project provides two implementations:

### Bash Implementation (`record.bash`)
Uses OpenAI's Whisper API for transcription.

### Python Implementation (`record_fireworks.py`)
Uses Fireworks AI's Whisper V3 API for transcription.

Both scripts combine several components:

1. **Recording**: Uses `arecord` to capture audio from your microphone
2. **Transcription**: Sends the recorded audio to the chosen API for transcription
3. **Text Input**: Uses `xdotool` to type the transcribed text into the active window

The scripts are designed to be triggered twice:
- First execution: Starts the recording
- Second execution: Stops the recording, transcribes the audio, and types the result

## Requirements

- Linux operating system
- `arecord`
- `xdotool`
- `killall`
- Python 3.6+ (for `record_fireworks.py`)
- `requests` Python package (for `record_fireworks.py`)
- API key (either OpenAI or Fireworks AI)
- `curl`
- `jq`

## Configuration

Before using either script, you need to set up:

1. Set your API key in `~/.zshenv`:
   ```bash
   # For OpenAI implementation
   export OPENAI_API_KEY="your-openai-key"
   # For Fireworks implementation
   export FIREWORKS_API_KEY="your-fireworks-key"
   ```

2. Configure your audio input device:
   - Use `arecord -l` to list available devices
   - Update `AUDIO_INPUT` in the script (default: `hw:0,6`)

Optional settings in both scripts:
- `MAX_DURATION`: Maximum recording duration (default: 120 seconds)
- Recording file locations and temporary files
- `PID_FILE`: Location to store the process ID of the recording
- `FILE`: Base path for temporary files

## Usage

1. Make the scripts executable:
   ```bash
   chmod +x record.bash record_fireworks.py
   ```

2. Run either script:
   ```bash
   # OpenAI implementation
   ./record.bash
   
   # Fireworks implementation
   ./record_fireworks.py
   ```

3. Press once to start recording, press again to stop and transcribe.

The transcribed text will be automatically typed into the active window.

## Security Notes

1. Never commit your API keys to the repository
2. The `.zshenv` file is ignored by git to prevent accidental exposure of secrets
3. Temporary recording files are automatically cleaned up after transcription

## Troubleshooting

1. If recording doesn't work:
   - Check your microphone device ID with `arecord -l`
   - Update the `AUDIO_INPUT` variable in the script

2. If transcription fails:
   - Verify your API key is correctly set in `~/.zshenv`
   - Check your internet connection
   - Ensure the audio recording is not empty

## Customization

You can modify the scripts to use different transcription services or adjust the recording parameters.

## Limitations

- The scripts are designed for Linux systems and may require modifications for other operating systems.
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
3. Edit `~/.xbindkeysrc` and add a line like (find the keycode of your button using `xev`):
   ```
   "/home/username/scripts/record.bash"
      m:0x0 + c:76
   ```
4. Run `xbindkeys` to apply the configuration.

Remember to adjust the script path according to your system setup.


## Credits

This project is inspired by the work of Jérémie Chauvel, as described in his blog post ["Whisper to your keyboard: Setting up a speech-to-text button"](https://blog.theodo.com/2023/11/speech-to-text-keyboard-button/).