"""
Speech-to-Text (STT) Client using ElevenLabs API

Note: ElevenLabs is primarily a TTS service. If STT is not available,
consider using AssemblyAI or another STT service instead.
"""

import os
import requests
from typing import Optional, Dict
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class ElevenLabsSTTClient:
    """
    Speech-to-Text client using ElevenLabs API
    
    Note: As of 2024, ElevenLabs primarily offers TTS services.
    If STT is not available, this client may need to be replaced
    with AssemblyAI or another STT provider.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize ElevenLabs STT client
        
        Args:
            api_key: ElevenLabs API key. If not provided, reads from ELEVENLABS_API_KEY env var
        """
        self.api_key = api_key or os.getenv("ELEVENLABS_API_KEY")
        if not self.api_key:
            raise ValueError("ELEVENLABS_API_KEY not found in environment variables")
        
        # Clean API key (remove whitespace)
        self.api_key = self.api_key.strip()
        
        # Log API key format (first 10 chars only for security)
        logger.info(f"ElevenLabs API key loaded (starts with: {self.api_key[:10]}...)")
        
        # ElevenLabs API base URL
        # Note: This may need to be updated based on actual ElevenLabs STT endpoint
        self.base_url = os.getenv("ELEVENLABS_BASE_URL", "https://api.elevenlabs.io/v1")
        
        # Try different possible STT endpoints (ElevenLabs may use different paths)
        # Common options: /speech-to-text, /transcribe, /stt
        stt_endpoint_path = os.getenv("ELEVENLABS_STT_ENDPOINT", "speech-to-text")
        self.stt_endpoint = f"{self.base_url}/{stt_endpoint_path}"
        
        # Default STT model ID (ElevenLabs STT uses "scribe_v1" or "scribe_v2")
        # Check for STT-specific model ID first, then fall back to generic model ID
        self.default_model_id = (
            os.getenv("ELEVENLABS_STT_MODEL_ID") or 
            os.getenv("ELEVENLABS_MODEL_ID") or 
            "scribe_v1"
        )
        
        logger.info("ElevenLabs STT client initialized")
    
    def transcribe(
        self,
        audio_data: bytes,
        language: str = "en",
        model: Optional[str] = None
    ) -> Dict:
        """
        Transcribe audio to text
        
        Args:
            audio_data: Audio file bytes (WAV, MP3, etc.)
            language: Language code (default: "en")
            model: Optional model name (if ElevenLabs supports multiple STT models)
        
        Returns:
            Dict with transcription result:
            {
                "text": str,  # Transcribed text
                "language": str,  # Detected language
                "confidence": float,  # Confidence score (0-1)
            }
        
        Raises:
            ValueError: If audio_data is empty
            requests.RequestException: If API request fails
        """
        if not audio_data:
            raise ValueError("audio_data cannot be empty")
        
        headers = {
            "xi-api-key": self.api_key,
        }
        
        # ElevenLabs STT API requires model_id in the request body
        model_id = model or self.default_model_id
        
        # Log request details (without sensitive data)
        logger.debug(f"STT Request - Endpoint: {self.stt_endpoint}, Model: {model_id}, Language: {language}")
        
        # Prepare multipart form data
        # ElevenLabs expects the file field to be named "file", not "audio"
        files = {
            "file": ("audio.webm", audio_data, "audio/webm")
        }
        
        data = {
            "language": language,
            "model_id": model_id,  # Required field
        }
        
        try:
            logger.info(f"Transcribing audio (size: {len(audio_data)} bytes, language: {language})")
            
            response = requests.post(
                self.stt_endpoint,
                headers=headers,
                files=files,
                data=data,
                timeout=30
            )
            
            response.raise_for_status()
            result = response.json()
            
            logger.info(f"Transcription successful: {result.get('text', '')[:100]}...")
            
            return {
                "text": result.get("text", ""),
                "language": result.get("language", language),
                "confidence": result.get("confidence", 1.0),
            }
        
        except requests.exceptions.HTTPError as e:
            error_detail = e.response.text if e.response else "No response body"
            logger.error(f"ElevenLabs STT API error: {e.response.status_code} - {error_detail}")
            logger.error(f"Request URL: {self.stt_endpoint}")
            logger.error(f"Request headers: xi-api-key present (length: {len(self.api_key)})")
            logger.error(f"Request data: model_id={model_id}, language={language}")
            logger.error(f"Request files: file present (size: {len(audio_data)} bytes)")
            
            # Provide more helpful error messages
            if e.response.status_code == 401:
                error_msg = (
                    f"Invalid API key (401 Unauthorized). "
                    f"API key starts with: {self.api_key[:10]}...\n"
                    f"Please verify:\n"
                    f"1. Your ELEVENLABS_API_KEY is correct in the .env file\n"
                    f"2. The API key has STT (Speech-to-Text) permissions enabled\n"
                    f"3. The API key is not expired\n"
                    f"4. Your account subscription includes STT access\n"
                    f"Error details: {error_detail}"
                )
            else:
                error_msg = f"STT API error: {e.response.status_code} - {error_detail}"
            
            raise requests.RequestException(error_msg)
        
        except requests.exceptions.RequestException as e:
            logger.error(f"ElevenLabs STT request failed: {e}")
            raise
    
    def transcribe_file(self, file_path: str, language: str = "en") -> Dict:
        """
        Transcribe audio file to text
        
        Args:
            file_path: Path to audio file
            language: Language code (default: "en")
        
        Returns:
            Dict with transcription result
        """
        with open(file_path, "rb") as f:
            audio_data = f.read()
        
        return self.transcribe(audio_data, language=language)


