import os
import sys
from typing import Dict, Literal, Optional

from dotenv import load_dotenv
# Import the async client specifically
from google.cloud import \
    texttospeech_v1 as texttospeech  # Using v1 for async client
from pydantic import BaseModel, Field

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


class SpeechCreateParams(BaseModel):
    """
    Parameters for generating audio using a Text-to-Speech service,
    mimicking the OpenAI Speech API's create endpoint.
    """

    input: str = Field(
        ...,
        description="The text to generate audio for. The maximum length is 4096 characters.",
    )
    model: SpeechModel = Field(
        ..., description="One of the available TTS models: `tts-1` or `tts-1-hd`."
    )
    voice: Literal[
        "alloy",
        "echo",
        "fable",
        "onyx",
        "nova",
        "shimmer",
        "es-es-standard-a",
        "fr-fr-wavenet-b",
        "de-de-neural2-c",
        "ja-jp-neural2-a",
    ] = Field(
        ...,
        description=(
            "The voice to use when generating the audio. Supported voices are "
            "standard OpenAI voices and new multilingual mappings."
        ),
    )
    response_format: Optional[Literal["mp3", "opus", "aac", "flac", "wav", "pcm"]] = (
        Field(
            None,
            description=(
                "The format to audio in. Supported formats are `mp3`, `opus`, `aac`, `flac`, `wav`, and `pcm`."
            ),
        )
    )
    speed: Optional[float] = Field(
        None,
        ge=0.25,
        le=4.0,
        description="The speed of the generated audio. Select a value from `0.25` to `4.0`. `1.0` is the default.",
    )


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
        synthesis_input = texttospeech.SynthesisInput(text=params.input)

        google_voice_config = self._voice_mapping.get(params.voice)
        if not google_voice_config:
            raise ValueError(
                f"Unsupported voice: '{params.voice}'. No Google Cloud mapping found."
            )

        voice_params = texttospeech.VoiceSelectionParams(
            language_code=google_voice_config["language_code"],
            name=google_voice_config["name"],
        )

        audio_encoding = self._audio_encoding_mapping.get(
            params.response_format or "mp3"
        )  # Default to mp3
        if not audio_encoding:
            raise ValueError(f"Unsupported response_format: '{params.response_format}'")

        audio_config = texttospeech.AudioConfig(
            audio_encoding=audio_encoding,
            speaking_rate=params.speed or 1.0,
        )

        # Await the asynchronous call to the Google Cloud TTS API
        response = await self.client.synthesize_speech(  # type: ignore
            input=synthesis_input, voice=voice_params, audio_config=audio_config
        )

        return response.audio_content
