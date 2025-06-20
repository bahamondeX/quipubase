#!/bin/bash

# Define the JSON payload for music generation
# Prompts are adjusted for a tropical house track with epic bass drops.
JSON_PAYLOAD='{
  "prompts": [
    {
      "text": "Tropical house with vibrant synths, catchy melody, and an overall sunny, relaxed beach club vibe.",
      "weight": 1.0
    }
  ],
  "config": {
    "temperature": 0.2
}
}'

echo "Sending music generation request and piping audio directly to speakers..."

# Use curl to POST the JSON payload and pipe the streaming audio to ffplay.
# The '-s' flag makes curl silent.
# The '-N' flag disables buffered output, crucial for continuous streaming.
# 'ffplay' is used to play the raw audio stream.
# '-i pipe:' specifies input from stdin.
# '-f s16le' specifies the input format as signed 16-bit little-endian PCM, a common raw audio format.
# '-ar 24000' specifies the audio sample rate as 24000 Hz. Adjust if your API output differs.
# '-nodisp' prevents ffplay from opening a video display window.
curl -s -N -X POST \
     -H "Content-Type: application/json" \
     -d "$JSON_PAYLOAD" \
     http://127.0.0.1:8080/v1/music/generations \
     | ffplay -i pipe: -f s16le -ar 24000 -nodisp