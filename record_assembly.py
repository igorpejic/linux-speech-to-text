#!/usr/bin/env python3
import os
import sys
import signal
import subprocess
from pathlib import Path
import assemblyai as aai
from datetime import datetime
import threading
import time

def log_time(message):
    """Log message with timestamp"""
    timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
    print(f"[{timestamp}] {message}")

class TranscriptionManager:
    def __init__(self):
        self.home = Path.home()
        self.pid_file = self.home / '.assemblypid'
        self.i3status_file = Path('/tmp/voice_typing_active')
        self.transcriber = None
        self.stream = None
        self.is_running = False
        self.current_text = ""
        
        # Read API key from .zshenv
        self.api_key = self.read_api_key()
        if not self.api_key:
            log_time("Error: ASSEMBLY_API_KEY is not set in ~/.zshenv")
            sys.exit(1)
            
        # Configure AssemblyAI
        aai.settings.api_key = self.api_key

    def read_api_key(self):
        """Read API key from .zshenv file"""
        zshenv_path = self.home / '.zshenv'
        if zshenv_path.exists():
            with open(zshenv_path, 'r') as f:
                for line in f:
                    if line.startswith('export ASSEMBLY_API_KEY='):
                        return line.split('=', 1)[1].strip().strip("'\"")
        return None

    def on_open(self, session_opened: aai.RealtimeSessionOpened):
        """Called when the connection has been established."""
        log_time(f"Session opened - ID: {session_opened.session_id}")

    def on_data(self, transcript: aai.RealtimeTranscript):
        """Called when a new transcript has been received."""
        if not transcript.text:
            return

        if isinstance(transcript, aai.RealtimeFinalTranscript):
            self.current_text = transcript.text
            # Type out the final transcript
            subprocess.run(['xdotool', 'type', '--clearmodifiers', transcript.text + "\n"])
            log_time(f"Final transcript: {transcript.text}")
        else:
            # Update the current partial transcript
            self.current_text = transcript.text
            log_time(f"Partial: {transcript.text}")

    def on_error(self, error: aai.RealtimeError):
        """Called when an error occurs."""
        log_time(f"Error occurred: {error}")
        self.stop_recording()

    def on_close(self):
        """Called when the connection has been closed."""
        log_time("Session closed")
        self.is_running = False

    def start_recording(self):
        """Start the transcription stream"""
        try:
            log_time("Starting transcription")
            
            # Create transcriber
            self.transcriber = aai.RealtimeTranscriber(
                on_data=self.on_data,
                on_error=self.on_error,
                sample_rate=44_100,
                on_open=self.on_open,
                on_close=self.on_close,
            )

            # Start the connection
            self.transcriber.connect()

            # Open microphone stream
            self.stream = aai.extras.MicrophoneStream()
            
            # Save the process ID
            self.pid_file.write_text(str(os.getpid()))
            
            # Update i3status
            self.i3status_file.write_text("recording🎤")
            subprocess.run(['killall', '-USR1', 'i3status'], check=False)
            
            # Start streaming in a separate thread
            self.is_running = True
            self.stream_thread = threading.Thread(target=self._stream_audio)
            self.stream_thread.start()
            
            subprocess.run(['notify-send', 'Voice Typing', 'Real-time transcription started'])
            log_time("Transcription started successfully")
            
        except Exception as e:
            log_time(f"Error starting transcription: {e}")
            subprocess.run(['notify-send', 'Voice Typing Error', f"Failed to start transcription: {e}"])
            self.stop_recording()

    def _stream_audio(self):
        """Stream audio in a separate thread"""
        try:
            self.transcriber.stream(self.stream)
        except Exception as e:
            log_time(f"Streaming error: {e}")
            self.stop_recording()

    def stop_recording(self):
        """Stop the transcription stream"""
        log_time("Stopping transcription")
        
        self.is_running = False
        
        if self.transcriber:
            try:
                self.transcriber.close()
            except Exception as e:
                log_time(f"Error closing transcriber: {e}")
        
        if self.stream:
            try:
                self.stream.close()
            except Exception as e:
                log_time(f"Error closing stream: {e}")
        
        # Clean up files
        self.pid_file.unlink(missing_ok=True)
        self.i3status_file.unlink(missing_ok=True)
        subprocess.run(['killall', '-USR1', 'i3status'], check=False)
        
        subprocess.run(['notify-send', 'Voice Typing', 'Transcription stopped'])
        log_time("Transcription stopped")

def main():
    manager = TranscriptionManager()
    
    if manager.pid_file.exists():
        # Stop recording if already running
        try:
            pid = int(manager.pid_file.read_text().strip())
            os.kill(pid, signal.SIGTERM)
        except (ProcessLookupError, ValueError) as e:
            log_time(f"Warning when stopping: {e}")
        manager.stop_recording()
    else:
        # Start new recording
        manager.start_recording()
        try:
            # Keep the main thread alive
            while manager.is_running:
                time.sleep(0.1)
        except KeyboardInterrupt:
            manager.stop_recording()

if __name__ == '__main__':
    main()
