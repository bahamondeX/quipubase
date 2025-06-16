# app.py (or could be combined into a single file with the above class)
from io import BytesIO
from typing import AsyncGenerator

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from .typedefs import GoogleTTSService, SpeechCreateParams

# Create an instance of the TTS service
tts_service = GoogleTTSService()


# FastAPI application setup
def route():
    tts_router = APIRouter(prefix="/audio")

    # Define a chunk size for streaming the generated audio bytes
    # This controls how many bytes are sent at a time to the client.
    AUDIO_CHUNK_SIZE = 4096  # 4KB chunks

    # Mapping for FastAPI media types
    MEDIA_TYPES = {
        "mp3": "audio/mpeg",
        "opus": "audio/ogg; codecs=opus",  # Specific codec for OGG Opus
        "aac": "audio/aac",
        "flac": "audio/flac",
        "wav": "audio/wav",
        "pcm": "audio/x-pcm",  # Or audio/L16, might need additional headers for sample rate etc.
        # For simple PCM, WAV is often preferred as a container.
    }

    @tts_router.post("/speech", summary="Generates audio from the input text.")
    async def _(params: SpeechCreateParams) -> StreamingResponse:
        """
        Generates audio from the input text using Google Cloud Text-to-Speech.
        """
        response_format = params.get("response_format", "mp3")
        # Validate the response format against supported media types
        if response_format not in MEDIA_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported response_format: {         response_format}. "
                f"Supported formats are {list(MEDIA_TYPES.keys())}.",
            )

        try:
            # Generate the full audio content asynchronously
            audio_content_bytes = await tts_service.create_speech(params)

            # Get the appropriate media type
            media_type = MEDIA_TYPES.get(
                response_format, "application/octet-stream"
            )

            # Generator function to stream chunks of audio bytes
            async def audio_streamer() -> AsyncGenerator[bytes, None]:
                # Use BytesIO to treat the bytes as a file-like object for chunking
                audio_io = BytesIO(audio_content_bytes)
                while chunk := audio_io.read(AUDIO_CHUNK_SIZE):
                    yield chunk
                # Close the BytesIO object (optional, but good practice)
                audio_io.close()

            EXT_MAPPING = {
                "mp3": "mp3",
                "opus": "ogg",
                "aac": "aac",
                "flac": "flac",
                "wav": "wav",
                "pcm": "pcm",
            }
            # Return a StreamingResponse
            return StreamingResponse(
                audio_streamer(),
                media_type=media_type,
                headers={
                    "Content-Disposition": f"attachment; filename=audio.{EXT_MAPPING.get(response_format, 'mp3')}"
                },
            )

        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            # Catch any other unexpected errors from the TTS service
            raise HTTPException(status_code=500, detail=f"Internal server error: {e}")

    return tts_router
