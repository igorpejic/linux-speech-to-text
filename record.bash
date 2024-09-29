#!/usr/bin/env bash
# Usage: Execute this script twice to start and stop recording
# Dependencies: curl, jq, arecord, xdotool, killall, notify-send

set -euo pipefail
IFS=$'\n\t'

# Configuration
readonly PID_FILE="${HOME}/.recordpid"
readonly FILE="${HOME}/.voice-type/recording"
readonly MAX_DURATION=30
readonly AUDIO_INPUT='hw:0,6' # Use `arecord -l` to list available devices
readonly NOTIFICATION_ID_FILE="${HOME}/.voice-type-notification-id"

# Check for OPENAI_API_KEY
[[ -z "${OPENAI_API_KEY:-}" ]] && { echo "Error: OPENAI_API_KEY is not set"; exit 1; }

# Function to start recording
start_recording() {
  mkdir -p "$(dirname "$FILE")"
  echo "Starting new recording..."
  nohup arecord --device="$AUDIO_INPUT" --format cd "$FILE.wav" --duration="$MAX_DURATION" &>/dev/null &
  echo $! >"$PID_FILE"
  echo "Recording started. PID: $!"
  notify-send -p "Voice Typing" "Recording started. Speak now." > "$NOTIFICATION_ID_FILE"
}

# Function to stop recording
stop_recording() {
  echo "Stopping recording..."
  if [ -s "$PID_FILE" ]; then
    local pid
    pid=$(<"$PID_FILE")
    if ! kill "$pid" 2>/dev/null; then
      echo "Warning: Unable to kill process $pid" >&2
    else
      wait "$pid" 2>/dev/null
    fi
    rm -f "$PID_FILE"
    echo "Recording stopped."
    notify-send -r $(cat "$NOTIFICATION_ID_FILE") "Voice Typing" "Recording stopped. Transcribing..."
    return 0
  fi
  echo "No recording process found."
}

# Function to write transcript using xdotool
write_transcript() {
  if [ -f "$FILE.txt" ]; then
    perl -pi -e 'chomp if eof' "$FILE.txt"
    echo "Typing transcript..."
    xdotool type --clearmodifiers --file "$FILE.txt"
    echo "Transcript typed."
  else
    echo "Error: Transcript file not found."
  fi
}

# Function to transcribe audio using OpenAI API
transcribe_with_openai() {
  echo "Transcribing audio..."
  if [ ! -f "$FILE.wav" ]; then
    echo "Error: Audio file not found."
    notify-send -r $(cat "$NOTIFICATION_ID_FILE") "Voice Typing" "Error: Audio file not found."
    return 1
  fi
  
  local response
  response=$(curl --silent --fail --request POST \
    --url https://api.openai.com/v1/audio/transcriptions \
    --header "Authorization: Bearer $OPENAI_API_KEY" \
    --header 'Content-Type: multipart/form-data' \
    --form file="@$FILE.wav" \
    --form model=whisper-1 \
    --form response_format=text \
    -o "${FILE}.txt" -w "%{http_code}")
  
  if [ "$response" = "200" ]; then
    echo "Transcription successful."
    notify-send -r $(cat "$NOTIFICATION_ID_FILE") "Voice Typing" "Transcription successful!"
  else
    echo "Error: Transcription failed with HTTP status $response"
    notify-send -r $(cat "$NOTIFICATION_ID_FILE") "Voice Typing" "Error: Transcription failed."
    return 1
  fi
}

# Main function
main() {
  if [[ -f "$PID_FILE" ]]; then
    stop_recording
    transcribe_with_openai || { echo "Transcription failed. Exiting."; exit 1; }
    write_transcript
    rm -f "$NOTIFICATION_ID_FILE"  # Clean up the notification ID file
  else
    start_recording
  fi
}

# Execute main function
main
