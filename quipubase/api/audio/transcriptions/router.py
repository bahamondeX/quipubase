import os
import io
import os
import typing as tp
from fastapi import FastAPI, APIRouter, UploadFile, Form, HTTPException, status
from groq import AsyncGroq
from typing import Optional

def route():
	# Initialize Google Cloud Speech-to-Text client
	# This will automatically use GOOGLE_APPLICATION_CREDENTIALS environment variable
	# or other default authentication methods configured for Google Cloud.
	try:
		speech_client = AsyncGroq()
	except Exception as e:
		raise HTTPException(
			status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
			detail=f"Failed to initialize Groq client: {str(e)}"
		)
	
	# Create an API router for audio-related endpoints
	app = APIRouter(
		prefix="/audio/transcriptions", # OpenAI's audio endpoints are typically under /v1/audio
		tags=["audio"],
	)

	@app.post("")
	async def _(
		file: UploadFile,
		model: tp.Literal["whisper-large-v3","whisper-large-v3-turbo"] = Form(..., description="The name of the model to use for transcription. Currently ignored as Google Cloud Speech-to-Text handles model selection internally or via configuration. OpenAI models like 'whisper-1' are for compatibility."),
		language: str = Form(default="en", description="The language of the input audio. Supplying the input language in ISO-639-1 format (e.g., 'en', 'es', 'fr'). This will be converted to a BCP-47 language code for Google (e.g., 'en-US', 'es-ES')."),
		response_format: tp.Literal["text","json","verbose_json"] = Form("json", description="The format of the transcript output. Only 'json' is fully supported, 'text' will return plain text. Other OpenAI formats like 'srt', 'vtt', 'verbose_json' are not directly supported and will default to 'json' behavior."),
		temperature: float= Form(1, description="The sampling temperature, between 0 and 1. Higher values like 0.8 will make the output more random, while lower values like 0.2 will make it more focused and deterministic. Not directly used by Google Cloud Speech-to-Text."),
		prompt: Optional[str] = Form(None, description="An optional text to guide the model's style or continue a previous audio segment. Not directly used by Google Cloud Speech-to-Text.")
	  ):
		"""
		Creates a transcription of the provided audio file using Google Cloud Speech-to-Text.

		Args:
			file
				: UploadFile - The audio file to transcribe.
			model
				: str - The name of the model to use for transcription. Currently ignored as Google Cloud Speech-to-Text handles model selection internally or via configuration. OpenAI models like 'whisper-1' are for compatibility.
			language	
				: Optional[str] - The language of the input audio. Supplying the input language in ISO-639-1 format (e.g., 'en', 'es', 'fr'). This will be converted to a BCP-47 language code for Google (e.g., 'en-US', 'es-ES').
			response_format
				: tp.Literal["text","json","verbose_json"] - The format of the transcript output. Only 'json' is fully supported, 'text' will return plain text. Other OpenAI formats like 'srt', 'vtt', 'verbose_json' are not directly supported and will default to 'json' behavior.
			temperature
				: Optional[float] - The sampling temperature, between 0 and 1. Higher values like 0.8 will make the output more random, while lower values like 0.2 will make it more focused and deterministic. Not directly used by Google Cloud Speech-to-Text.
			prompt
				: Optional[str] - An optional text to guide the model's style or continue a previous audio segment. Not directly used by Google Cloud Speech-to-Text.
		Returns:		
			: dict - The transcription result in the requested format.
		"""
		assert file.content_type, "File must have a content type"
		assert file.content_type.startswith("audio/"), "File must be an audio type"
		assert file.filename, "File must have a filename"
		audio_content = await file.read()

		# Convert language to BCP-47 format if provided
		if language:
			language = language.replace("-", "_")  # Convert to BCP-47 format
			language_code = f"{language}-US"  # Default to US region, can be adjusted
		else:
			language_code = "en-US"  # Default to English US if no language provided
		try:
			# Call the Google Cloud Speech-to-Text API
			response = await speech_client.audio.transcriptions.create(
				file=audio_content,
				model=model,
				language=language_code,
				response_format=response_format,
				temperature=temperature,
				prompt=prompt or ""
			)
			return response
		except Exception as e:
			raise HTTPException(
				status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
				detail=f"Transcription failed: {str(e)}"
			)

	return app	