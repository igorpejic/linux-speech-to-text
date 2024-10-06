#!/usr/bin/env bash
# Usage: Execute this script to start or stop recording
# Dependencies: curl, jq, arecord, xdotool, killall, notify-send

source "${HOME}/.zshenv"
set -euo pipefail
IFS=$'\n\t'

# Configuration
readonly PID_FILE="${HOME}/.recordpid"
readonly FILE="${HOME}/.voice-type/recording"
readonly MAX_DURATION=30
readonly AUDIO_INPUT='hw:0,6' # Use `arecord -l` to list available devices
readonly NOTIFICATION_ID_FILE="${HOME}/.voice-type-notification-id"
readonly I3STATUS_INDICATOR_FILE="/tmp/voice_typing_active"

# Check for OPENAI_API_KEY
if [[ -z "${OPENAI_API_KEY:-}" ]]; then
  echo "Error: OPENAI_API_KEY is not set"
  exit 1
fi

# Function to check if a process is running
is_process_running() {
  local pid="$1"
  if kill -0 "$pid" 2>/dev/null; then
    return 0
  else
    return 1
  fi
}

# Function to start recording
start_recording() {
  mkdir -p "$(dirname "$FILE")"
  echo "Starting new recording..."
  nohup arecord --device="$AUDIO_INPUT" --format cd "$FILE.wav" --duration="$MAX_DURATION" &>/dev/null &
  local pid=$!
  echo "$pid" >"$PID_FILE"
  echo "recording🎤" > "$I3STATUS_INDICATOR_FILE"
  killall -USR1 i3status
  echo "Recording started. PID: $pid"
  notify-send "Voice Typing" "Recording started. Speak now."
}

# Function to stop recording
stop_recording() {
  echo "Stopping recording..."
  notify-send "Voice Typing" "Stopping recording..."
  
  if [[ -s "$PID_FILE" ]]; then
    local pid
    pid=$(<"$PID_FILE")
    if is_process_running "$pid"; then
      kill "$pid"
      echo "Recording stopped."
      notify-send "Voice Typing" "Recording stopped. Transcribing..."
    else
      echo "Recording process not found. It may have already stopped."
      notify-send "Voice Typing" "Recording process not found."
    fi
    rm -f "$PID_FILE"
    echo "" > "$I3STATUS_INDICATOR_FILE"
    killall -USR1 i3status
  else
    echo "No active recording found."
    notify-send "Voice Typing" "No active recording to stop."
  fi
}

# Function to write transcript using xdotool
write_transcript() {
  if [[ -f "$FILE.txt" ]]; then
    perl -pi -e 'chomp if eof' "$FILE.txt"
    echo "Typing transcript..."
    xdotool type --clearmodifiers --file "$FILE.txt"
    echo "Transcript typed."
  else
    echo "Error: Transcript file not found."
    notify-send "Voice Typing" "Error: Transcript file not found."
  fi
}

# Function to transcribe audio using OpenAI API
transcribe_with_openai() {
  echo "Transcribing audio..."
  if [[ ! -f "$FILE.wav" ]]; then
    echo "Error: Audio file not found."
    notify-send "Voice Typing" "Error: Audio file not found."
    return 1
  fi

  local response
  local error_log="${FILE}_error.log"
  response=$(curl --silent --fail --request POST \
    --url https://api.openai.com/v1/audio/transcriptions \
    --header "Authorization: Bearer $OPENAI_API_KEY" \
    --header 'Content-Type: multipart/form-data' \
    --form file="@$FILE.wav" \
    --form model=whisper-1 \
    --form response_format=text \
    --output "${FILE}.txt" \
    --write-out "%{http_code}" \
    2>"$error_log")

  if [[ "$response" -eq 200 ]]; then
    echo "Transcription successful."
    notify-send "Voice Typing" "Transcription successful!"
  else
    echo "Error: Transcription failed with HTTP status $response"
    notify-send "Voice Typing" "Error: Transcription failed with status $response"
    echo "Error details:" >> "$error_log"
    cat "$error_log"
    return 1
  fi
}

# Main function
main() {
  if [[ -f "$PID_FILE" ]]; then
    stop_recording
    if [[ -f "$FILE.wav" ]]; then
      transcribe_with_openai && write_transcript
      rm -f "$NOTIFICATION_ID_FILE" "$FILE.wav" "${FILE}.txt"  # Clean up files after successful transcription
    else
      echo "Error: Audio file not found. The recording may not have been successful."
      notify-send "Voice Typing" "Error: Audio file not found."
      rm -f "$PID_FILE" "$NOTIFICATION_ID_FILE"
      exit 1
    fi
  else
    start_recording
  fi
}

# Execute main function
main