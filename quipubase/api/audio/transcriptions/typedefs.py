import os
import sys
from typing import List, Literal, Optional, Union

from dotenv import load_dotenv
from google.cloud import speech
from pydantic import BaseModel, Field

load_dotenv()

PROJECT_ID = os.getenv("GOOGLE_PROJECT_ID")
if not PROJECT_ID:
    print("Error: GOOGLE_PROJECT_ID environment variable not set. Please set it to your Google Cloud Project ID.")
    sys.exit(1)

TranscriptionModel = Literal["whisper-1"]


class TranscriptionCreateParams(BaseModel):
    file: str = Field(..., description="Audio file to transcribe in formats like flac, mp3, wav, etc.")
    file_format: Literal["flac", "mp3", "wav", "ogg", "webm", "mp4", "m4a"] = Field(..., description="Audio format extension.")
    model: TranscriptionModel = Field(..., description="Only `whisper-1` is supported.")
    language: Optional[str] = Field(None, description="ISO-639-1 language code.")
    prompt: Optional[str] = Field(None, description="Optional guidance text.")
    response_format: Optional[Literal["json", "text", "srt", "verbose_json", "vtt"]] = Field("json")
    temperature: Optional[float] = Field(0, ge=0, le=1)


class TranscriptionResponse(BaseModel):
    text: str


class VerboseTranscriptionResponse(BaseModel):
    text: str
    task: str
    language: str
    duration: float
    segments: List[dict]


class GoogleSTTService:
    _language_mapping = {
        "en": "en-US", "es": "es-ES", "fr": "fr-FR", "de": "de-DE", "it": "it-IT",
        # ... extend as needed
    }

    _encoding_map = {
        "flac": speech.RecognitionConfig.AudioEncoding.FLAC,
        "mp3": speech.RecognitionConfig.AudioEncoding.MP3,
        "wav": speech.RecognitionConfig.AudioEncoding.LINEAR16,
        "ogg": speech.RecognitionConfig.AudioEncoding.OGG_OPUS,
        "webm": speech.RecognitionConfig.AudioEncoding.OGG_OPUS,
    }

    def __init__(self):
        self.client = speech.SpeechClient()

    def create_transcription(
        self, params: TranscriptionCreateParams, audio_content: bytes
    ) -> Union[TranscriptionResponse, VerboseTranscriptionResponse, str]:
        lang_code = self._language_mapping.get(params.language if params.language else "en-US") or "en-US"
        encoding = self._encoding_map.get(params.file_format, speech.RecognitionConfig.AudioEncoding.ENCODING_UNSPECIFIED)

        config = speech.RecognitionConfig(
            encoding=encoding,
            sample_rate_hertz=16000,
            language_code=lang_code,
            enable_automatic_punctuation=True,
            enable_word_time_offsets=params.response_format == "verbose_json",
            speech_contexts=[speech.SpeechContext(phrases=[params.prompt])] if params.prompt else None,
        )

        audio = speech.RecognitionAudio(content=audio_content)
        response = self.client.streaming_recognize(config=config)
        

        if not response.results:
            return TranscriptionResponse(text="")

        transcript = " ".join([result.alternatives[0].transcript for result in response.results])

        if params.response_format == "text":
            return transcript
        if params.response_format == "verbose_json":
            return self._build_verbose_response(response, transcript, lang_code, params.temperature)
        if params.response_format in ["srt", "vtt"]:
            return self._format_subtitles(response.results, params.response_format)

        return TranscriptionResponse(text=transcript)

    def _build_verbose_response(self, response, transcript: str, lang: str, temp: Optional[float]) -> VerboseTranscriptionResponse:
        segments = []
        for result in response.results:
            for word in result.alternatives[0].words:
                segments.append({
                    "id": len(segments),
                    "start": word.start_time.total_seconds(),
                    "end": word.end_time.total_seconds(),
                    "text": word.word,
                    "tokens": [word.word],
                    "temperature": temp,
                    "avg_logprob": result.alternatives[0].confidence,
                    "compression_ratio": 1.0,
                    "no_speech_prob": 0.0,
                })
        return VerboseTranscriptionResponse(
            text=transcript,
            task="transcribe",
            language=lang.split("-")[0],
            duration=0.0,
            segments=segments,
        )

    def _format_subtitles(self, results, fmt: str) -> str:
        if fmt == "srt":
            return "\n".join([
                f"{i+1}\n{self._srt_time(w[0])} --> {self._srt_time(w[-1])}\n{r.alternatives[0].transcript}\n"
                for i, r in enumerate(results) if (w := r.alternatives[0].words)
            ])
        if fmt == "vtt":
            return "WEBVTT\n\n" + "\n".join([
                f"{self._vtt_time(w[0])} --> {self._vtt_time(w[-1])}\n{r.alternatives[0].transcript}\n"
                for r in results if (w := r.alternatives[0].words)
            ])

    def _srt_time(self, t):
        return f"{int(t.total_seconds()//3600):02}:{int(t.total_seconds()%3600//60):02}:{int(t.total_seconds()%60):02},{int((t.total_seconds()%1)*1000):03}"

    def _vtt_time(self, t):
        return f"{int(t.total_seconds()//3600):02}:{int(t.total_seconds()%3600//60):02}:{int(t.total_seconds()%60):02}.{int((t.total_seconds()%1)*1000):03}"
