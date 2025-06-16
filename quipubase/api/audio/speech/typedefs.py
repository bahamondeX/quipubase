import os
import sys
from typing import Dict, Literal
from openai.types.audio import SpeechCreateParams

from dotenv import load_dotenv
# Import the async client specifically
from google.cloud import \
    texttospeech_v1 as texttospeech  # Using v1 for async client

# Load environment variables from .env file
load_dotenv()

# --- Configuration from Environment Variables ---
PROJECT_ID = os.getenv("GOOGLE_PROJECT_ID")
if not PROJECT_ID:
    print(
        "Error: GOOGLE_PROJECT_ID environment variable not set. Please set it to your Google Cloud Project ID."
    )
    sys.exit(1)

# Assuming SpeechModel is defined as in your previous request
SpeechModel = Literal["tts-1", "tts-1-hd"]

class GoogleTTSService:
    """
    A service class to generate speech using Google Cloud Text-to-Speech API,
    with an interface similar to OpenAI's TTS endpoint.
    """

    _voice_mapping: Dict[str, Dict[str, str]] = {
        "alloy": {"language_code": "en-US", "name": "en-US-Neural2-D"},
        "echo": {"language_code": "en-US", "name": "en-US-Neural2-F"},
        "fable": {"language_code": "en-US", "name": "en-US-Neural2-J"},
        "onyx": {"language_code": "en-US", "name": "en-US-Neural2-A"},
        "nova": {"language_code": "en-US", "name": "en-US-Neural2-C"},
        "shimmer": {"language_code": "en-US", "name": "en-US-Neural2-E"},
        "es-es-standard-a": {"language_code": "es-ES", "name": "es-ES-Standard-A"},
        "fr-fr-wavenet-b": {"language_code": "fr-FR", "name": "fr-FR-Wavenet-B"},
        "de-de-neural2-c": {"language_code": "de-DE", "name": "de-DE-Neural2-C"},
        "ja-jp-neural2-a": {"language_code": "ja-JP", "name": "ja-JP-Neural2-A"},
    }

    _audio_encoding_mapping: Dict[str, texttospeech.AudioEncoding] = {
        "mp3": texttospeech.AudioEncoding.MP3,
        "opus": texttospeech.AudioEncoding.OGG_OPUS,
        "aac": texttospeech.AudioEncoding.MP3,  # Often used as a fallback for AAC
        "flac": texttospeech.AudioEncoding.LINEAR16,
        "wav": texttospeech.AudioEncoding.LINEAR16,
        "pcm": texttospeech.AudioEncoding.LINEAR16,
    }

    def __init__(self):
        # Use the asynchronous client
        self.client = texttospeech.TextToSpeechAsyncClient()

    async def create_speech(self, params: SpeechCreateParams) -> bytes:
        """
        Synthesizes speech from text using Google Cloud TTS based on OpenAI-like parameters.

        Args:
            params: An instance of SpeechCreateParams containing the audio generation request.

        Returns:
            The generated audio content as bytes.
        """
        synthesis_input = texttospeech.SynthesisInput(text=params['input'])

        google_voice_config = self._voice_mapping.get(params['voice'])
        if not google_voice_config:
            raise ValueError(
                f"Unsupported voice: '{params['voice']}'. No Google Cloud mapping found."
            )

        voice_params = texttospeech.VoiceSelectionParams(
            language_code=google_voice_config["language_code"],
            name=google_voice_config["name"],
        )

        audio_encoding = self._audio_encoding_mapping.get(
            params.get('response_format') or 'mp3'  # Default to mp3 if not specified
        )  # Default to mp3
        audio_config = texttospeech.AudioConfig(
            audio_encoding=audio_encoding,
            speaking_rate=params.get('speed') or 1.0,
        )

        # Await the asynchronous call to the Google Cloud TTS API
        response = await self.client.synthesize_speech(  # type: ignore
            input=synthesis_input, voice=voice_params, audio_config=audio_config
        )

        return response.audio_content
