from typing import Optional, Union

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse, PlainTextResponse, Response
from pydantic import BaseModel

from .service import TranscriptionService
from .typedefs import (GoogleSTTService, TranscriptionCreateParams,
                       TranscriptionResponse, VerboseTranscriptionResponse)

# Create an instance of the transcription service
transcription_service = TranscriptionService()


def route():
    transcription_router = APIRouter(prefix="/audio")

    @transcription_router.post(
        "/transcriptions", summary="Transcribes audio into the input language."
    )
    async def _(
        file: UploadFile = File(..., description="The audio file object to transcribe"),
        model: str = Form(
            ...,
            description="ID of the model to use. Only 'whisper-1' is currently available.",
        ),
        language: Optional[str] = Form(
            None, description="The language of the input audio in ISO-639-1 format"
        ),
        prompt: Optional[str] = Form(
            None, description="An optional text to guide the model's style"
        ),
        response_format: str = Form(
            "text", description="The format of the transcript output"
        ),
        temperature: float = Form(
            0, ge=0, le=1, description="The sampling temperature"
        ),
    ):
        """
        Transcribes audio into the input language using Google Cloud Speech-to-Text.
        """
        # Validate model
        if model != "whisper-1":
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported model: {model}. Only 'whisper-1' is currently available.",
            )

        # Validate response format
        valid_formats = ["json", "text", "srt", "verbose_json", "vtt"]
        if response_format not in valid_formats:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported response_format: {response_format}. "
                f"Supported formats are {valid_formats}.",
            )

        try:
            # Read the uploaded file content
            audio_content = await file.read()

            # Create params object
            params = TranscriptionCreateParams(
                file=file.filename or "",
                model=model,
                language=language,
                prompt=prompt,
                response_format=response_format,
                temperature=temperature,
            )

            # Perform transcription
            result = await transcription_service.create_transcription(
                params, audio_content
            )

            # Return appropriate response based on format
            if response_format == "text":
                if isinstance(result, str):
                    return PlainTextResponse(content=result, media_type="text/plain")
                else:
                    return JSONResponse(
                        content=(
                            result.model_dump()
                            if hasattr(result, "model_dump")
                            else {"text": result}
                        )
                    )
            elif response_format == "srt":
                if isinstance(result, str):
                    return PlainTextResponse(
                        content=result, media_type="application/x-subrip"
                    )
                else:
                    return Response(content=result, media_type="application/x-subrip")
            elif response_format == "vtt":
                if isinstance(result, str):
                    return PlainTextResponse(content=result, media_type="text/vtt")
                else:
                    return Response(content=result, media_type="text/vtt")
            else:  # json or verbose_json
                if isinstance(result, str):
                    return PlainTextResponse(content=result, media_type="text/plain")
                else:
                    return JSONResponse(
                        content=(
                            result.model_dump()
                            if hasattr(result, "model_dump")
                            else {"text": result}
                        )
                    )

        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Internal server error: {e}")

    return transcription_router
