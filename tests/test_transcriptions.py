"""
Tests for the audio transcriptions API using OpenAI client compatibility.

This module tests the transcriptions endpoint to ensure it's compatible
with the OpenAI client library.
"""

import io
import json
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from quipubase.api.audio.transcriptions.router import route
from quipubase.api.audio.transcriptions.service import TranscriptionService
from quipubase.api.audio.transcriptions.typedefs import (
    TranscriptionCreateParams,
    TranscriptionResponse,
    VerboseTranscriptionResponse,
)


@pytest.fixture
def client():
    """Create a test client with the transcriptions router"""
    from fastapi import FastAPI
    
    app = FastAPI()
    app.include_router(route())
    return TestClient(app)


@pytest.fixture
def mock_audio_file():
    """Create a mock audio file for testing"""
    # Create a simple WAV file header for testing
    wav_header = b'RIFF\x24\x08\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x44\xac\x00\x00\x88X\x01\x00\x02\x00\x10\x00data\x00\x08\x00\x00'
    audio_data = wav_header + b'\x00' * 1000  # Add some dummy audio data
    
    return io.BytesIO(audio_data)


class TestTranscriptionCreateParams:
    """Test cases for TranscriptionCreateParams validation"""

    def test_valid_params(self):
        """Test creating valid transcription parameters"""
        params = TranscriptionCreateParams(
            file="test.mp3",
            model="whisper-1",
            language="en",
            prompt="Test prompt",
            response_format="json",
            temperature=0.5
        )
        
        assert params.file == "test.mp3"
        assert params.model == "whisper-1"
        assert params.language == "en"
        assert params.prompt == "Test prompt"
        assert params.response_format == "json"
        assert params.temperature == 0.5

    def test_default_values(self):
        """Test default parameter values"""
        params = TranscriptionCreateParams(
            file="test.mp3",
            model="whisper-1"
        )
        
        assert params.language is None
        assert params.prompt is None
        assert params.response_format == "json"
        assert params.temperature == 0

    def test_temperature_validation(self):
        """Test temperature validation bounds"""
        # Valid temperature
        params = TranscriptionCreateParams(
            file="test.mp3",
            model="whisper-1",
            temperature=0.8
        )
        assert params.temperature == 0.8
        
        # Test that pydantic validation would catch invalid values
        with pytest.raises(ValueError):
            TranscriptionCreateParams(
                file="test.mp3",
                model="whisper-1",
                temperature=1.5  # Too high
            )


class TestTranscriptionResponses:
    """Test cases for transcription response models"""

    def test_transcription_response(self):
        """Test basic transcription response"""
        response = TranscriptionResponse(text="Hello world")
        assert response.text == "Hello world"
        assert response.model_dump() == {"text": "Hello world"}

    def test_verbose_transcription_response(self):
        """Test verbose transcription response"""
        segments = [
            {
                "id": 0,
                "start": 0.0,
                "end": 1.0,
                "text": "Hello",
                "tokens": ["Hello"],
                "temperature": 0.0,
                "avg_logprob": 0.9,
                "compression_ratio": 1.0,
                "no_speech_prob": 0.0
            }
        ]
        
        response = VerboseTranscriptionResponse(
            text="Hello world",
            task="transcribe",
            language="en",
            duration=1.0,
            segments=segments
        )
        
        assert response.text == "Hello world"
        assert response.task == "transcribe"
        assert response.language == "en"
        assert response.duration == 1.0
        assert len(response.segments) == 1


class TestTranscriptionService:
    """Test cases for TranscriptionService"""

    @pytest.fixture
    def service(self):
        """Create a transcription service for testing"""
        return TranscriptionService()

    def test_service_initialization(self, service):
        """Test service initialization"""
        assert service.stt_service is not None
        assert hasattr(service.stt_service, 'create_transcription')

    @pytest.mark.asyncio
    async def test_create_transcription(self, service):
        """Test transcription creation"""
        params = TranscriptionCreateParams(
            file="test.wav",
            model="whisper-1",
            response_format="json"
        )
        audio_content = b"fake audio data"
        
        with patch.object(service.stt_service, 'create_transcription') as mock_stt:
            mock_stt.return_value = TranscriptionResponse(text="Test transcription")
            
            result = await service.create_transcription(params, audio_content)
            
            assert isinstance(result, TranscriptionResponse)
            assert result.text == "Test transcription"
            mock_stt.assert_called_once_with(params, audio_content)


class TestTranscriptionsAPI:
    """Test cases for the transcriptions API endpoint"""

    @pytest.mark.asyncio
    async def test_transcriptions_endpoint_json(self, client, mock_audio_file):
        """Test transcriptions endpoint with JSON response format"""
        with patch('quipubase.api.audio.transcriptions.router.transcription_service') as mock_service:
            mock_service.create_transcription = AsyncMock(
                return_value=TranscriptionResponse(text="Hello world")
            )
            
            response = client.post(
                "/audio/transcriptions",
                files={"file": ("test.mp3", mock_audio_file, "audio/mp3")},
                data={
                    "model": "whisper-1",
                    "response_format": "json"
                }
            )
            
            assert response.status_code == status.HTTP_200_OK
            assert response.headers["content-type"] == "application/json"
            
            data = response.json()
            assert data["text"] == "Hello world"

    @pytest.mark.asyncio
    async def test_transcriptions_endpoint_text(self, client, mock_audio_file):
        """Test transcriptions endpoint with text response format"""
        with patch('quipubase.api.audio.transcriptions.router.transcription_service') as mock_service:
            mock_service.create_transcription = AsyncMock(
                return_value="Hello world"
            )
            
            response = client.post(
                "/audio/transcriptions",
                files={"file": ("test.mp3", mock_audio_file, "audio/mp3")},
                data={
                    "model": "whisper-1",
                    "response_format": "text"
                }
            )
            
            assert response.status_code == status.HTTP_200_OK
            assert response.headers["content-type"] == "text/plain; charset=utf-8"
            assert response.text == "Hello world"

    @pytest.mark.asyncio
    async def test_transcriptions_endpoint_verbose_json(self, client, mock_audio_file):
        """Test transcriptions endpoint with verbose JSON response format"""
        verbose_response = VerboseTranscriptionResponse(
            text="Hello world",
            task="transcribe",
            language="en",
            duration=2.5,
            segments=[
                {
                    "id": 0,
                    "start": 0.0,
                    "end": 2.5,
                    "text": "Hello world",
                    "tokens": ["Hello", "world"],
                    "temperature": 0.0,
                    "avg_logprob": -0.1,
                    "compression_ratio": 1.0,
                    "no_speech_prob": 0.0
                }
            ]
        )
        
        with patch('quipubase.api.audio.transcriptions.router.transcription_service') as mock_service:
            mock_service.create_transcription = AsyncMock(return_value=verbose_response)
            
            response = client.post(
                "/audio/transcriptions",
                files={"file": ("test.mp3", mock_audio_file, "audio/mp3")},
                data={
                    "model": "whisper-1",
                    "response_format": "verbose_json"
                }
            )
            
            assert response.status_code == status.HTTP_200_OK
            assert response.headers["content-type"] == "application/json"
            
            data = response.json()
            assert data["text"] == "Hello world"
            assert data["task"] == "transcribe"
            assert data["language"] == "en"
            assert data["duration"] == 2.5
            assert len(data["segments"]) == 1

    @pytest.mark.asyncio
    async def test_transcriptions_endpoint_srt(self, client, mock_audio_file):
        """Test transcriptions endpoint with SRT response format"""
        srt_content = "1\n00:00:00,000 --> 00:00:02,500\nHello world\n"
        
        with patch('quipubase.api.audio.transcriptions.router.transcription_service') as mock_service:
            mock_service.create_transcription = AsyncMock(return_value=srt_content)
            
            response = client.post(
                "/audio/transcriptions",
                files={"file": ("test.mp3", mock_audio_file, "audio/mp3")},
                data={
                    "model": "whisper-1",
                    "response_format": "srt"
                }
            )
            
            assert response.status_code == status.HTTP_200_OK
            assert response.headers["content-type"] == "application/x-subrip; charset=utf-8"
            assert response.text == srt_content

    @pytest.mark.asyncio
    async def test_transcriptions_endpoint_vtt(self, client, mock_audio_file):
        """Test transcriptions endpoint with VTT response format"""
        vtt_content = "WEBVTT\n\n00:00:00.000 --> 00:00:02.500\nHello world\n"
        
        with patch('quipubase.api.audio.transcriptions.router.transcription_service') as mock_service:
            mock_service.create_transcription = AsyncMock(return_value=vtt_content)
            
            response = client.post(
                "/audio/transcriptions",
                files={"file": ("test.mp3", mock_audio_file, "audio/mp3")},
                data={
                    "model": "whisper-1",
                    "response_format": "vtt"
                }
            )
            
            assert response.status_code == status.HTTP_200_OK
            assert response.headers["content-type"] == "text/vtt; charset=utf-8"
            assert response.text == vtt_content

    @pytest.mark.asyncio
    async def test_transcriptions_endpoint_with_optional_params(self, client, mock_audio_file):
        """Test transcriptions endpoint with all optional parameters"""
        with patch('quipubase.api.audio.transcriptions.router.transcription_service') as mock_service:
            mock_service.create_transcription = AsyncMock(
                return_value=TranscriptionResponse(text="Hola mundo")
            )
            
            response = client.post(
                "/audio/transcriptions",
                files={"file": ("test.mp3", mock_audio_file, "audio/mp3")},
                data={
                    "model": "whisper-1",
                    "language": "es",
                    "prompt": "This is Spanish audio",
                    "response_format": "json",
                    "temperature": "0.2"
                }
            )
            
            assert response.status_code == status.HTTP_200_OK
            
            # Verify the service was called with correct parameters
            call_args = mock_service.create_transcription.call_args
            params = call_args[0][0]  # First argument is TranscriptionCreateParams
            
            assert params.language == "es"
            assert params.prompt == "This is Spanish audio"
            assert params.response_format == "json"
            assert params.temperature == 0.2

    @pytest.mark.asyncio
    async def test_transcriptions_endpoint_error_handling(self, client, mock_audio_file):
        """Test error handling in transcriptions endpoint"""
        with patch('quipubase.api.audio.transcriptions.router.transcription_service') as mock_service:
            mock_service.create_transcription = AsyncMock(
                side_effect=ValueError("Invalid audio format")
            )
            
            response = client.post(
                "/audio/transcriptions",
                files={"file": ("test.mp3", mock_audio_file, "audio/mp3")},
                data={
                    "model": "whisper-1",
                    "response_format": "json"
                }
            )
            
            assert response.status_code == status.HTTP_400_BAD_REQUEST
            assert "Invalid audio format" in response.json()["detail"]

    def test_transcriptions_endpoint_missing_file(self, client):
        """Test transcriptions endpoint without file upload"""
        response = client.post(
            "/audio/transcriptions",
            data={
                "model": "whisper-1",
                "response_format": "json"
            }
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_transcriptions_endpoint_invalid_model(self, client, mock_audio_file):
        """Test transcriptions endpoint with invalid model"""
        response = client.post(
            "/audio/transcriptions",
            files={"file": ("test.mp3", mock_audio_file, "audio/mp3")},
            data={
                "model": "invalid-model",
                "response_format": "json"
            }
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestOpenAIClientCompatibility:
    """Test cases to ensure compatibility with OpenAI Python client"""

    @pytest.mark.asyncio
    async def test_openai_client_like_usage(self, client, mock_audio_file):
        """Test that the API behaves like OpenAI's transcriptions endpoint"""
        # Simulate how OpenAI client would call the endpoint
        with patch('quipubase.api.audio.transcriptions.router.transcription_service') as mock_service:
            mock_service.create_transcription = AsyncMock(
                return_value=TranscriptionResponse(text="Test transcription")
            )
            
            # This mimics how the OpenAI client sends requests
            response = client.post(
                "/audio/transcriptions",
                files={"file": ("audio.mp3", mock_audio_file, "audio/mpeg")},
                data={
                    "model": "whisper-1"
                    # Note: OpenAI client sends minimal required params by default
                }
            )
            
            assert response.status_code == status.HTTP_200_OK
            
            # Should return JSON by default (OpenAI behavior)
            assert response.headers["content-type"] == "application/json"
            data = response.json()
            assert "text" in data
            assert data["text"] == "Test transcription"

    @pytest.mark.asyncio 
    async def test_response_format_compatibility(self, client, mock_audio_file):
        """Test that all OpenAI response formats are supported"""
        formats_and_expected_content_types = [
            ("json", "application/json"),
            ("text", "text/plain; charset=utf-8"),
            ("srt", "application/x-subrip; charset=utf-8"),
            ("verbose_json", "application/json"),
            ("vtt", "text/vtt; charset=utf-8")
        ]
        
        for response_format, expected_content_type in formats_and_expected_content_types:
            with patch('quipubase.api.audio.transcriptions.router.transcription_service') as mock_service:
                if response_format == "verbose_json":
                    mock_response = VerboseTranscriptionResponse(
                        text="Test", task="transcribe", language="en", 
                        duration=1.0, segments=[]
                    )
                elif response_format in ["srt", "vtt"]:
                    mock_response = f"Sample {response_format.upper()} content"
                else:
                    mock_response = TranscriptionResponse(text="Test") if response_format == "json" else "Test"
                
                mock_service.create_transcription = AsyncMock(return_value=mock_response)
                
                response = client.post(
                    "/audio/transcriptions",
                    files={"file": ("test.mp3", mock_audio_file, "audio/mp3")},
                    data={
                        "model": "whisper-1",
                        "response_format": response_format
                    }
                )
                
                assert response.status_code == status.HTTP_200_OK
                assert response.headers["content-type"] == expected_content_type


# Integration test that would work with actual OpenAI client
@pytest.mark.integration
class TestActualOpenAIClient:
    """Integration tests using the actual OpenAI client library"""
    
    def test_with_openai_client(self):
        """Test the endpoint using the actual OpenAI Python client
        
        This test is marked as integration and should be run with a real server.
        """
        pytest.skip("Integration test - requires running server and OpenAI client setup")
        
        # Example of how this would work:
        # import openai
        # 
        # client = openai.OpenAI(
        #     base_url="http://localhost:8000",  # Your FastAPI server
        #     api_key="dummy-key"  # Not needed for local testing
        # )
        # 
        # with open("test_audio.mp3", "rb") as audio_file:
        #     transcription = client.audio.transcriptions.create(
        #         model="whisper-1",
        #         file=audio_file,
        #         response_format="text"
        #     )
        #     assert isinstance(transcription, str)
        #     assert len(transcription) > 0