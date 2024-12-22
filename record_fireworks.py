#!/usr/bin/env python3
import os
import sys
import signal
import subprocess
import requests
import time
from pathlib import Path
from requests.exceptions import RequestException, Timeout

class AudioRecorder:
    def __init__(self):
        self.home = Path.home()
        self.pid_file = self.home / '.recordpid'
        self.recording_dir = self.home / '.voice-type'
        self.recording_file = self.recording_dir / 'recording.wav'
        self.i3status_file = Path('/tmp/voice_typing_active')
        self.audio_input = os.getenv('AUDIO_INPUT', 'hw:0,6')  # Make audio input configurable
        self.max_duration = 120  # Maximum recording duration in seconds
        self.api_key = self.read_api_key()
        
        if not self.api_key:
            print("Error: FIREWORKS_API_KEY is not set in ~/.zshenv")
            sys.exit(1)

    def read_api_key(self):
        zshenv_path = self.home / '.zshenv'
        if zshenv_path.exists():
            with open(zshenv_path, 'r') as f:
                for line in f:
                    if line.startswith('export FIREWORKS_API_KEY='):
                        return line.split('=', 1)[1].strip().strip("'\"")
        return None

    def start_recording(self):
        """Start recording audio"""
        try:
            self.recording_dir.mkdir(parents=True, exist_ok=True)
            
            cmd = [
                'arecord',
                f'--device={self.audio_input}',
                '--format=cd',
                str(self.recording_file),
                f'--duration={self.max_duration}'
            ]
            
            process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
            
            # Check if process started successfully
            time.sleep(0.1)
            if process.poll() is not None:
                error = process.stderr.read().decode()
                print(f"Error starting recording: {error}")
                subprocess.run(['notify-send', 'Voice Typing Error', f"Failed to start recording: {error}"])
                return
            
            self.pid_file.write_text(str(process.pid))
            
            self.i3status_file.write_text("recording🎤")
            subprocess.run(['killall', '-USR1', 'i3status'], check=False)
            
            print(f"Recording started. PID: {process.pid}")
            subprocess.run(['notify-send', 'Voice Typing', 'Recording started. Speak now.'])
            
        except Exception as e:
            print(f"Error starting recording: {e}")
            subprocess.run(['notify-send', 'Voice Typing Error', f"Failed to start recording: {e}"])

    def stop_recording(self):
        """Stop recording and transcribe the audio"""
        if not self.pid_file.exists():
            return
        
        try:
            pid = int(self.pid_file.read_text().strip())
            os.kill(pid, signal.SIGTERM)
        except (ProcessLookupError, ValueError) as e:
            print(f"Warning: {e}")
        except Exception as e:
            print(f"Error stopping recording: {e}")
        
        self.pid_file.unlink(missing_ok=True)
        self.i3status_file.unlink(missing_ok=True)
        subprocess.run(['killall', '-USR1', 'i3status'], check=False)
        
        
        if self.recording_file.exists():
            if self.recording_file.stat().st_size > 0:
                text = self.transcribe_audio()
                if text:
                    self.write_transcript(text)
            else:
                print("Error: Recording file is empty")
                subprocess.run(['notify-send', 'Voice Typing Error', 'Recording file is empty'])
            self.recording_file.unlink(missing_ok=True)

    def transcribe_audio(self):
        """Transcribe audio using Fireworks Whisper V3 API"""
        print("Transcribing audio...")
        subprocess.run(['notify-send', 'Voice Typing', 'Transcribing audio...'])
        
        try:
            with open(self.recording_file, 'rb') as f:
                response = requests.post(
                    "https://audio-prod.us-virginia-1.direct.fireworks.ai/v1/audio/transcriptions",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    files={"file": f},
                    data={
                        "model": "whisper-v3",
                        "temperature": "0",
                        "vad_model": "silero"
                    },
                    timeout=30  # Set timeout to 30 seconds
                )
            
            response.raise_for_status()
            result = response.json()
            return result.get('text', '').strip()
            
        except Timeout:
            error_msg = "Transcription timed out after 30 seconds"
            print(error_msg)
            subprocess.run(['notify-send', 'Voice Typing Error', error_msg])
        except RequestException as e:
            error_msg = f"Transcription failed: {str(e)}"
            print(error_msg)
            subprocess.run(['notify-send', 'Voice Typing Error', error_msg])
        except Exception as e:
            error_msg = f"Unexpected error during transcription: {str(e)}"
            print(error_msg)
            subprocess.run(['notify-send', 'Voice Typing Error', error_msg])
        return None

    def write_transcript(self, text):
        """Write transcript using xdotool"""
        if not text:
            return
            
        subprocess.run(['xdotool', 'type', '--clearmodifiers', text])
        print(f"Transcribed text: {text}")

def main():
    recorder = AudioRecorder()
    
    if recorder.pid_file.exists():
        recorder.stop_recording()
    else:
        recorder.start_recording()

if __name__ == '__main__':
    main()