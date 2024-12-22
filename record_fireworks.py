#!/usr/bin/env python3
import os
import sys
import signal
import subprocess
import requests
import time
from pathlib import Path
from requests.exceptions import RequestException, Timeout
from datetime import datetime

def log_time(message):
    """Log message with timestamp"""
    timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
    print(f"[{timestamp}] {message}")

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
        start_time = time.time()
        log_time("Starting recording process")
        try:
            self.recording_dir.mkdir(parents=True, exist_ok=True)
            
            cmd = [
                'arecord',
                f'--device={self.audio_input}',
                '--format=cd',
                str(self.recording_file),
                f'--duration={self.max_duration}'
            ]
            
            log_time(f"Executing command: {' '.join(cmd)}")
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Check if process started successfully
            time.sleep(0.1)
            if process.poll() is not None:
                error = process.stderr.read().decode()
                log_time(f"Error starting recording: {error}")
                subprocess.run(['notify-send', 'Voice Typing Error', f"Failed to start recording: {error}"])
                return
            
            self.pid_file.write_text(str(process.pid))
            
            self.i3status_file.write_text("recording🎤")
            subprocess.run(['killall', '-USR1', 'i3status'], check=False)
            
            duration = time.time() - start_time
            log_time(f"Recording started. PID: {process.pid} (took {duration:.2f}s)")
            subprocess.run(['notify-send', 'Voice Typing', 'Recording started. Speak now.'])
            
        except Exception as e:
            log_time(f"Error starting recording: {e}")
            subprocess.run(['notify-send', 'Voice Typing Error', f"Failed to start recording: {e}"])

    def stop_recording(self):
        """Stop recording and transcribe the audio"""
        if not self.pid_file.exists():
            return
        
        start_time = time.time()
        log_time("Stopping recording")
        
        try:
            pid = int(self.pid_file.read_text().strip())
            os.kill(pid, signal.SIGTERM)
            log_time(f"Sent SIGTERM to process {pid}")
        except (ProcessLookupError, ValueError) as e:
            log_time(f"Warning: {e}")
        except Exception as e:
            log_time(f"Error stopping recording: {e}")
        
        self.pid_file.unlink(missing_ok=True)
        self.i3status_file.unlink(missing_ok=True)
        subprocess.run(['killall', '-USR1', 'i3status'], check=False)
        
        if self.recording_file.exists():
            file_size = self.recording_file.stat().st_size
            log_time(f"Recording file size: {file_size/1024/1024:.2f}MB")
            
            if file_size > 0:
                text = self.transcribe_audio()
                if text:
                    self.write_transcript(text)
            else:
                log_time("Error: Recording file is empty")
                subprocess.run(['notify-send', 'Voice Typing Error', 'Recording file is empty'])
            self.recording_file.unlink(missing_ok=True)
        
        duration = time.time() - start_time
        log_time(f"Stop recording completed (took {duration:.2f}s)")

    def transcribe_audio(self):
        """Transcribe audio using Fireworks Whisper V3 API"""
        start_time = time.time()
        log_time("Starting transcription")
        subprocess.run(['notify-send', 'Voice Typing', 'Transcribing audio...'])
        
        try:
            with open(self.recording_file, 'rb') as f:
                log_time("Sending request to Fireworks API")
                response = requests.post(
                    # "https://audio-turbo.us-virginia-1.direct.fireworks.ai/v1/audio/transcriptions",
                    "https://audio-prod.us-virginia-1.direct.fireworks.ai/v1/audio/transcriptions",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    files={"file": f},
                    data={
                        # "model": "whisper-v3-turbo",
                        "model": "whisper-v3",
                        "temperature": "0",
                        "vad_model": "silero",
                        "language": "en",
                    },
                    timeout=30  # Set timeout to 30 seconds
                )
            
            api_duration = time.time() - start_time
            log_time(f"API request completed (took {api_duration:.2f}s)")
            
            response.raise_for_status()
            result = response.json()
            text = result.get('text', '').strip()
            
            total_duration = time.time() - start_time
            log_time(f"Transcription completed (total time: {total_duration:.2f}s)")
            return text
            
        except Timeout:
            error_msg = "Transcription timed out after 30 seconds"
            log_time(error_msg)
            subprocess.run(['notify-send', 'Voice Typing Error', error_msg])
        except RequestException as e:
            error_msg = f"Transcription failed: {str(e)}"
            log_time(error_msg)
            subprocess.run(['notify-send', 'Voice Typing Error', error_msg])
        except Exception as e:
            error_msg = f"Unexpected error during transcription: {str(e)}"
            log_time(error_msg)
            subprocess.run(['notify-send', 'Voice Typing Error', error_msg])
        return None

    def write_transcript(self, text):
        """Write transcript using xdotool"""
        if not text:
            return
        
        start_time = time.time()
        log_time("Writing transcript")
        subprocess.run(['xdotool', 'type', '--clearmodifiers', text])
        duration = time.time() - start_time
        log_time(f"Transcript written (took {duration:.2f}s)")
        print(f"Transcribed text: {text}")

def main():
    recorder = AudioRecorder()
    
    if recorder.pid_file.exists():
        recorder.stop_recording()
    else:
        recorder.start_recording()

if __name__ == '__main__':
    main()