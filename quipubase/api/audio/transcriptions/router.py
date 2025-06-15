import io
import os
from fastapi import FastAPI, APIRouter, UploadFile, Form, HTTPException, status
from fastapi.responses import JSONResponse, PlainTextResponse
from google.cloud import speech_v1p1beta1 as speech
from google.api_core.exceptions import GoogleAPIError
from typing import Optional

def route():
	# Initialize Google Cloud Speech-to-Text client
	# This will automatically use GOOGLE_APPLICATION_CREDENTIALS environment variable
	# or other default authentication methods configured for Google Cloud.
	try:
		speech_client = speech.SpeechClient()
		print("Google Cloud Speech-to-Text client initialized successfully.")
	except Exception as e:
		print(f"Error initializing Google Cloud Speech-to-Text client: {e}")
		print("Please ensure GOOGLE_APPLICATION_CREDENTIALS environment variable is set correctly.")
		speech_client = None # Set to None if initialization fails to handle later

	# Create an API router for audio-related endpoints
	app = APIRouter(
		prefix="/audio/transcriptions", # OpenAI's audio endpoints are typically under /v1/audio
		tags=["audio"],
	)

	@app.post("")
	async def create_transcription(
		file: UploadFile,
		model: str = Form(..., description="The name of the model to use for transcription. Currently ignored as Google Cloud Speech-to-Text handles model selection internally or via configuration. OpenAI models like 'whisper-1' are for compatibility."),
		language: Optional[str] = Form(None, description="The language of the input audio. Supplying the input language in ISO-639-1 format (e.g., 'en', 'es', 'fr'). This will be converted to a BCP-47 language code for Google (e.g., 'en-US', 'es-ES')."),
		response_format: str = Form("json", description="The format of the transcript output. Only 'json' is fully supported, 'text' will return plain text. Other OpenAI formats like 'srt', 'vtt', 'verbose_json' are not directly supported and will default to 'json' behavior."),
		temperature: Optional[float] = Form(1, description="The sampling temperature, between 0 and 1. Higher values like 0.8 will make the output more random, while lower values like 0.2 will make it more focused and deterministic. Not directly used by Google Cloud Speech-to-Text."),
		prompt: Optional[str] = Form(None, description="An optional text to guide the model's style or continue a previous audio segment. Not directly used by Google Cloud Speech-to-Text.")
	):
		"""
		Transcribes audio into text using Google Cloud Speech-to-Text,
		mimicking OpenAI's `/v1/audio/transcriptions` endpoint.

		Args:
			file (UploadFile): The audio file to transcribe. Supported formats
							are determined by Google Cloud Speech-to-Text
							(e.g., FLAC, WAV, MP3, AAC).
			model (str): Dummy parameter for OpenAI compatibility. Google Cloud
						Speech-to-Text handles its own model selection.
			language (Optional[str]): ISO-639-1 language code (e.g., 'en', 'es').
									Will be converted to BCP-47 for Google.
			response_format (str): Desired output format. 'json' returns
									`{"text": "..."}`, 'text' returns plain text.
			temperature (Optional[float]): Dummy parameter for OpenAI compatibility.
			prompt (Optional[str]): Dummy parameter for OpenAI compatibility.

		Returns:
			JSONResponse: A JSON object with the transcribed text,
						or plain text if `response_format='text'`.
		"""
		if speech_client is None:
			raise HTTPException(
				status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
				detail="Google Cloud Speech-to-Text client not initialized. Check server logs for details."
			)

		# Read audio file content
		audio_content = await file.read()

		# Determine Google-compatible language code
		# Google generally prefers BCP-47 codes (e.g., 'en-US', 'es-ES').
		# We'll do a simple mapping for common ISO-639-1 codes.
		# For more robust mapping, a dedicated library or comprehensive lookup
		# would be needed. Default to 'en-US' if no match.
		google_language_code = "en-US" # Default
		if language:
			lang_map = {
				"en": "en-US",
				"es": "es-ES",
				"fr": "fr-FR",
				"de": "de-DE",
				"it": "it-IT",
				"ja": "ja-JP",
				"ko": "ko-KR",
				"zh": "zh-CN", # Simplified Chinese
				"pt": "pt-BR", # Brazilian Portuguese
				"ru": "ru-RU",
				"ar": "ar-XA",
				# Add more mappings as needed
			}
			google_language_code = lang_map.get(language.lower(), f"{language.lower()}-{language.upper()}")
			# If the language code is not in the map, try to construct a BCP-47
			# from the ISO-639-1, e.g., 'fr' -> 'fr-FR', which might work for Google
			# but could also be invalid for less common languages.

		# Configure the recognition request
		audio = speech.RecognitionAudio(content=audio_content)
		config = speech.RecognitionConfig(
			language_code=google_language_code,
			# Google Cloud Speech-to-Text can often auto-detect encoding and sample rate.
			# If specific encoding/sample rate are known, they can be set here:
			# encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
			# sample_rate_hertz=16000,
			enable_automatic_punctuation=True,
			# Can specify model for Google, e.g., 'default', 'command_and_search', 'phone_call'
			# model="default"
		)

		try:
			# Perform synchronous speech recognition using long_running_recognize
			# This is more robust for potentially larger audio files uploaded in a single go.
			operation = speech_client.streaming_recognize(config=config, audio=audio)
			response = operation.result(timeout=300)  # Wait for up to 5 minutes

			transcript = ""
			if response.results:
				# Get the first alternative of the first result (most confident transcription)
				transcript = response.results[0].alternatives[0].transcript
			else:
				print(f"No transcription results found for {file.filename}")

			if response_format == "text":
				return PlainTextResponse(content=transcript) # Return plain text directly
			else: # Default to json
				return JSONResponse(content={"text": transcript})

		except GoogleAPIError as e:
			print(f"Google Cloud Speech-to-Text API error: {e}")
			raise HTTPException(
				status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
				detail=f"Google Cloud Speech-to-Text API error: {e.message}"
			)
		except Exception as e:
			print(f"An unexpected error occurred: {e}")
			raise HTTPException(
				status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
				detail=f"An unexpected error occurred: {e}"
			)
	return app