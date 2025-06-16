import typing as tp
from fastapi import APIRouter, UploadFile, Form, HTTPException, status
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
		size:str=Form("auto", description="The size of the model to use for transcription. Currently ignored as Google Cloud Speech-to-Text handles model selection internally."),
		response_format: tp.Literal["text","json","verbose_json"] = Form("verbose_json", description="The format of the transcript output. Only 'json' is fully supported, 'text' will return plain text. Other OpenAI formats like 'srt', 'vtt', 'verbose_json' are not directly supported and will default to 'json' behavior."),
		temperature: float= Form(0.0, description="The sampling temperature, between 0 and 1. Higher values like 0.8 will make the output more random, while lower values like 0.2 will make it more focused and deterministic. Not directly used by Google Cloud Speech-to-Text."),
		prompt: Optional[str] = Form(None, description="An optional text to guide the model's style or continue a previous audio segment. Not directly used by Google Cloud Speech-to-Text.")
	  ):
		"""
		Creates a transcription of the provided audio file using Google Cloud Speech-to-Text.

		Args:
			file
				: UploadFile - The audio file to transcribe.
			model
				: str - The name of the model to use for transcription. Currently ignored as Google Cloud Speech-to-Text handles model selection internally or via configuration. OpenAI models like 'whisper-1' are for compatibility.
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
		if not audio_content:
			raise HTTPException(
				status_code=status.HTTP_400_BAD_REQUEST,
				detail="Audio file is empty or not readable."
			)
		content_type = file.content_type.split("/")[1].split(";")[0]  # Extract the main type (e.g., "mp3", "wav", etc.)
		if content_type not in ["mp3", "wav", "flac", "aac", "opus","pcm","ogg","mpeg"]:
			raise HTTPException(
				status_code=status.HTTP_400_BAD_REQUEST,
				detail=f"Unsupported audio format: {content_type}. Supported formats are mp3, wav, flac, aac, opus."
			)
		# Convert language to BCP-47 format if provided
	
		# Set the response format
		if response_format not in ["text", "json", "verbose_json"]:
			raise HTTPException(
				status_code=status.HTTP_400_BAD_REQUEST,
				detail=f"Unsupported response format: {response_format}. Supported formats are text, json, verbose_json."
			)
		try:
			# Call the Google Cloud Speech-to-Text API
			return await speech_client.audio.transcriptions.create(
				file=(file.filename,audio_content,content_type),
				model=model,
				response_format=response_format,
				temperature=temperature,
				prompt=prompt or ""
			)
			
		except Exception as e:
			raise HTTPException(
				status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
				detail=f"Transcription failed: {str(e)}"
			)

	return app	