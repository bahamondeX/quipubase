from typing import Union
from .typedefs import GoogleSTTService, TranscriptionCreateParams, TranscriptionResponse, VerboseTranscriptionResponse

class TranscriptionService:
    """Service class for handling audio transcription"""
    
    def __init__(self):
        self.stt_service = GoogleSTTService()
    
    async def create_transcription(
        self, 
        params: TranscriptionCreateParams, 
        audio_content: bytes
    ) -> Union[TranscriptionResponse, VerboseTranscriptionResponse, str]:
        """
        Creates a transcription of the provided audio content.
        
        Args:
            params: Transcription parameters
            audio_content: Audio file content as bytes
            
        Returns:
            Transcription result in the requested format
        """
        return self.stt_service.create_transcription(params, audio_content)