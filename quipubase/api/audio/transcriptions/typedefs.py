import os
import sys
from typing import Literal, Optional, Union, List
from pydantic import BaseModel, Field
from google.cloud import speech
from dotenv import load_dotenv

load_dotenv()

PROJECT_ID = os.getenv("GOOGLE_PROJECT_ID")
if not PROJECT_ID:
    print("Error: GOOGLE_PROJECT_ID environment variable not set. Please set it to your Google Cloud Project ID.")
    sys.exit(1)

TranscriptionModel = Literal["whisper-1"]

class TranscriptionCreateParams(BaseModel):
    """
    Parameters for audio transcription using a Speech-to-Text service,
    mimicking the OpenAI Transcription API's create endpoint.
    """
    file: str = Field(
        ..., description="The audio file object (not file name) to transcribe, in one of these formats: flac, m4a, mp3, mp4, mpeg, mpga, oga, ogg, wav, or webm."
    )
    model: TranscriptionModel = Field(
        ..., description="ID of the model to use. Only `whisper-1` is currently available."
    )
    language: Optional[str] = Field(
        None, description="The language of the input audio. Supplying the input language in ISO-639-1 format will improve accuracy and latency."
    )
    prompt: Optional[str] = Field(
        None, description="An optional text to guide the model's style or continue a previous audio segment. The prompt should match the audio language."
    )
    response_format: Optional[Literal["json", "text", "srt", "verbose_json", "vtt"]] = Field(
        "json", description="The format of the transcript output, in one of these options: json, text, srt, verbose_json, or vtt."
    )
    temperature: Optional[float] = Field(
        0, ge=0, le=1, description="The sampling temperature, between 0 and 1. Higher values like 0.8 will make the output more random, while lower values like 0.2 will make it more focused and deterministic."
    )

class TranscriptionResponse(BaseModel):
    """Response from the transcription API"""
    text: str = Field(..., description="The transcribed text")

class VerboseTranscriptionResponse(BaseModel):
    """Verbose response from the transcription API"""
    text: str = Field(..., description="The transcribed text")
    task: str = Field(..., description="The type of task performed")
    language: str = Field(..., description="The detected or provided language")
    duration: float = Field(..., description="The duration of the audio file")
    segments: List[dict] = Field(..., description="List of segments with timestamps")

class GoogleSTTService:
    """
    A service class to transcribe speech using Google Cloud Speech-to-Text API,
    with an interface similar to OpenAI's Transcription endpoint.
    """
    
    _language_mapping = {
        "af": "af-ZA",
        "ar": "ar-XA", 
        "hy": "hy-AM",
        "az": "az-AZ",
        "be": "be-BY",
        "bs": "bs-BA",
        "bg": "bg-BG",
        "ca": "ca-ES",
        "zh": "zh-CN",
        "hr": "hr-HR",
        "cs": "cs-CZ",
        "da": "da-DK",
        "nl": "nl-NL",
        "en": "en-US",
        "et": "et-EE",
        "fi": "fi-FI",
        "fr": "fr-FR",
        "gl": "gl-ES",
        "de": "de-DE",
        "el": "el-GR",
        "he": "he-IL",
        "hi": "hi-IN",
        "hu": "hu-HU",
        "is": "is-IS",
        "id": "id-ID",
        "it": "it-IT",
        "ja": "ja-JP",
        "kn": "kn-IN",
        "kk": "kk-KZ",
        "ko": "ko-KR",
        "lv": "lv-LV",
        "lt": "lt-LT",
        "mk": "mk-MK",
        "ms": "ms-MY",
        "mr": "mr-IN",
        "mi": "mi-NZ",
        "ne": "ne-NP",
        "no": "no-NO",
        "fa": "fa-IR",
        "pl": "pl-PL",
        "pt": "pt-PT",
        "ro": "ro-RO",
        "ru": "ru-RU",
        "sr": "sr-RS",
        "sk": "sk-SK",
        "sl": "sl-SI",
        "es": "es-ES",
        "sw": "sw-KE",
        "sv": "sv-SE",
        "tl": "tl-PH",
        "ta": "ta-IN",
        "th": "th-TH",
        "tr": "tr-TR",
        "uk": "uk-UA",
        "ur": "ur-PK",
        "vi": "vi-VN",
        "cy": "cy-GB"
    }

    def __init__(self):
        self.client = speech.SpeechClient()

    def create_transcription(self, params: TranscriptionCreateParams, audio_content: bytes) -> Union[TranscriptionResponse, VerboseTranscriptionResponse, str]:
        """
        Transcribes audio using Google Cloud Speech-to-Text based on OpenAI-like parameters.

        Args:
            params: An instance of TranscriptionCreateParams containing the transcription request.
            audio_content: The audio file content as bytes.

        Returns:
            The transcription result in the requested format.
        """
        # Map language code if provided
        language_code = "en-US"  # Default
        if params.language:
            language_code = self._language_mapping.get(params.language, params.language)

        # Configure recognition
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.ENCODING_UNSPECIFIED,
            sample_rate_hertz=16000,
            language_code=language_code,
            enable_automatic_punctuation=True,
            enable_word_time_offsets=params.response_format == "verbose_json",
            speech_contexts=[speech.SpeechContext(phrases=[params.prompt])] if params.prompt else None
        )

        audio = speech.RecognitionAudio(content=audio_content)

        # Perform recognition
        response = self.client.recognize(config=config, audio=audio)

        # Process results
        if not response.results:
            return TranscriptionResponse(text="")

        transcript = " ".join([result.alternatives[0].transcript for result in response.results])

        # Return based on response format
        if params.response_format == "text":
            return transcript
        elif params.response_format == "verbose_json":
            segments = []
            for result in response.results:
                if result.alternatives[0].words:
                    for word in result.alternatives[0].words:
                        segments.append({
                            "id": len(segments),
                            "start": word.start_time.total_seconds(),
                            "end": word.end_time.total_seconds(),
                            "text": word.word,
                            "tokens": [word.word],
                            "temperature": params.temperature,
                            "avg_logprob": result.alternatives[0].confidence,
                            "compression_ratio": 1.0,
                            "no_speech_prob": 0.0
                        })
            
            return VerboseTranscriptionResponse(
                text=transcript,
                task="transcribe",
                language=language_code.split("-")[0],
                duration=0.0,  # Google STT doesn't provide duration directly
                segments=segments
            )
        elif params.response_format in ["srt", "vtt"]:
            # Format as subtitle file
            return self._format_as_subtitle(response.results, params.response_format)
        else:  # json format (default)
            return TranscriptionResponse(text=transcript)

    def _format_as_subtitle(self, results, format_type):
        """Format transcription results as SRT or VTT subtitle format"""
        if format_type == "srt":
            output = []
            for i, result in enumerate(results, 1):
                if result.alternatives[0].words:
                    start_time = result.alternatives[0].words[0].start_time
                    end_time = result.alternatives[0].words[-1].end_time
                    
                    start_str = self._seconds_to_srt_time(start_time.total_seconds())
                    end_str = self._seconds_to_srt_time(end_time.total_seconds())
                    
                    output.append(f"{i}\n{start_str} --> {end_str}\n{result.alternatives[0].transcript}\n")
            return "\n".join(output)
        elif format_type == "vtt":
            output = ["WEBVTT\n"]
            for result in results:
                if result.alternatives[0].words:
                    start_time = result.alternatives[0].words[0].start_time
                    end_time = result.alternatives[0].words[-1].end_time
                    
                    start_str = self._seconds_to_vtt_time(start_time.total_seconds())
                    end_str = self._seconds_to_vtt_time(end_time.total_seconds())
                    
                    output.append(f"{start_str} --> {end_str}\n{result.alternatives[0].transcript}\n")
            return "\n".join(output)

    def _seconds_to_srt_time(self, seconds):
        """Convert seconds to SRT time format (HH:MM:SS,mmm)"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millisecs = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millisecs:03d}"

    def _seconds_to_vtt_time(self, seconds):
        """Convert seconds to VTT time format (HH:MM:SS.mmm)"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millisecs = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millisecs:03d}"