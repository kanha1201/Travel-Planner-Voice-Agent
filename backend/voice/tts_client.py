"""
Text-to-Speech (TTS) Client using AssemblyAI API

Note: AssemblyAI is primarily an STT service. If TTS is not available,
consider using ElevenLabs or another TTS service instead.
"""

import os
import requests
from typing import Optional, Dict
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class AssemblyAITTSClient:
    """
    Text-to-Speech client using AssemblyAI API
    
    Note: As of 2024, AssemblyAI primarily offers STT services.
    If TTS is not available, this client may need to be replaced
    with ElevenLabs or another TTS provider.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize AssemblyAI TTS client
        
        Args:
            api_key: AssemblyAI API key. If not provided, reads from ASSEMBLYAI_API_KEY env var
        """
        self.api_key = api_key or os.getenv("ASSEMBLYAI_API_KEY")
        if not self.api_key:
            raise ValueError("ASSEMBLYAI_API_KEY not found in environment variables")
        
        # AssemblyAI API base URL
        # Note: This may need to be updated based on actual AssemblyAI TTS endpoint
        self.base_url = os.getenv("ASSEMBLYAI_BASE_URL", "https://api.assemblyai.com/v2")
        self.tts_endpoint = f"{self.base_url}/text-to-speech"
        
        logger.info("AssemblyAI TTS client initialized")
    
    def synthesize(
        self,
        text: str,
        voice: str = "default",
        speed: float = 1.0,
        format: str = "mp3",
        sample_rate: int = 24000
    ) -> bytes:
        """
        Convert text to speech audio
        
        Args:
            text: Text to convert to speech
            voice: Voice ID or name (default: "default")
            speed: Speech speed multiplier (0.5 to 2.0, default: 1.0)
            format: Audio format ("mp3", "wav", "pcm", default: "mp3")
            sample_rate: Audio sample rate in Hz (default: 24000)
        
        Returns:
            bytes: Audio file data
        
        Raises:
            ValueError: If text is empty
            requests.RequestException: If API request fails
        """
        if not text or not text.strip():
            raise ValueError("text cannot be empty")
        
        headers = {
            "authorization": self.api_key,
            "content-type": "application/json"
        }
        
        payload = {
            "text": text,
            "voice": voice,
            "speed": speed,
            "format": format,
            "sample_rate": sample_rate
        }
        
        try:
            logger.info(f"Synthesizing speech for text: {text[:100]}... (voice: {voice}, speed: {speed})")
            
            response = requests.post(
                self.tts_endpoint,
                headers=headers,
                json=payload,
                timeout=30
            )
            
            response.raise_for_status()
            
            # AssemblyAI TTS may return JSON with audio URL or direct audio bytes
            # Adjust based on actual API response format
            if response.headers.get("content-type", "").startswith("application/json"):
                result = response.json()
                # If API returns URL, fetch the audio
                if "audio_url" in result:
                    audio_response = requests.get(result["audio_url"], timeout=30)
                    audio_response.raise_for_status()
                    audio_data = audio_response.content
                elif "audio" in result:
                    # If base64 encoded audio in JSON
                    import base64
                    audio_data = base64.b64decode(result["audio"])
                else:
                    raise ValueError("Unexpected API response format")
            else:
                # Direct audio bytes
                audio_data = response.content
            
            logger.info(f"Speech synthesis successful (audio size: {len(audio_data)} bytes)")
            
            return audio_data
        
        except requests.exceptions.HTTPError as e:
            logger.error(f"AssemblyAI TTS API error: {e.response.status_code} - {e.response.text}")
            raise requests.RequestException(f"TTS API error: {e.response.status_code} - {e.response.text}")
        
        except requests.exceptions.RequestException as e:
            logger.error(f"AssemblyAI TTS request failed: {e}")
            raise
    
    def synthesize_to_file(
        self,
        text: str,
        output_path: str,
        voice: str = "default",
        speed: float = 1.0,
        format: str = "mp3"
    ) -> str:
        """
        Convert text to speech and save to file
        
        Args:
            text: Text to convert to speech
            output_path: Path to save audio file
            voice: Voice ID or name (default: "default")
            speed: Speech speed multiplier (default: 1.0)
            format: Audio format (default: "mp3")
        
        Returns:
            str: Path to saved audio file
        """
        audio_data = self.synthesize(text, voice=voice, speed=speed, format=format)
        
        with open(output_path, "wb") as f:
            f.write(audio_data)
        
        logger.info(f"Audio saved to {output_path}")
        return output_path








