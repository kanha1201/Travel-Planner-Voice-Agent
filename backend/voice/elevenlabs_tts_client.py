"""
Text-to-Speech (TTS) Client using ElevenLabs API

ElevenLabs is a primary TTS service provider.
"""

import os
import requests
from typing import Optional, Dict
import logging
from dotenv import load_dotenv
from pathlib import Path

# Load .env file from backend directory
backend_dir = Path(__file__).parent.parent
env_path = backend_dir / ".env"
load_dotenv(dotenv_path=env_path, override=True)

logger = logging.getLogger(__name__)


class ElevenLabsTTSClient:
    """
    Text-to-Speech client using ElevenLabs API
    
    ElevenLabs is a leading TTS service provider.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize ElevenLabs TTS client
        
        Args:
            api_key: ElevenLabs API key. If not provided, reads from ELEVENLABS_API_KEY env var
        """
        # Debug: Check what's in the environment
        raw_key = api_key or os.getenv("ELEVENLABS_API_KEY")
        
        # Log the key being used (first 10 and last 4 chars for security)
        if raw_key:
            key_preview = f"{raw_key[:10]}...{raw_key[-4:]}" if len(raw_key) > 14 else raw_key[:10] + "..."
            logger.info(f"🔑 Using ElevenLabs API key: {key_preview} (length: {len(raw_key)})")
        else:
            logger.error("❌ ELEVENLABS_API_KEY is None or empty!")
        
        self.api_key = raw_key
        if not self.api_key:
            # Check if .env file exists
            env_file = backend_dir / ".env"
            logger.error(f"ELEVENLABS_API_KEY not found. Checked .env file at: {env_file}")
            logger.error(f".env file exists: {env_file.exists()}")
            if env_file.exists():
                # Read and check .env file for duplicate keys
                with open(env_file, 'r') as f:
                    lines = f.readlines()
                    elevenlabs_lines = [line.strip() for line in lines if 'ELEVENLABS_API_KEY' in line.upper()]
                    if elevenlabs_lines:
                        logger.warning(f"⚠️  Found {len(elevenlabs_lines)} line(s) with ELEVENLABS_API_KEY in .env:")
                        for i, line in enumerate(elevenlabs_lines, 1):
                            # Mask the key value
                            if '=' in line:
                                key_part, value_part = line.split('=', 1)
                                masked_value = f"{value_part[:10]}...{value_part[-4:]}" if len(value_part) > 14 else value_part[:10] + "..."
                                logger.warning(f"   Line {i}: {key_part}={masked_value}")
            raise ValueError(
                f"ELEVENLABS_API_KEY not found in environment variables. "
                f"Make sure your .env file is in: {backend_dir} and contains ELEVENLABS_API_KEY=your_key"
            )
        
        # Clean and validate API key
        self.api_key = self.api_key.strip()
        
        # Check for placeholder values
        if self.api_key.startswith("your_") or "placeholder" in self.api_key.lower() or len(self.api_key) < 20:
            logger.error(f"Invalid API key detected. Key starts with: {self.api_key[:20]}...")
            logger.error(f"Key length: {len(self.api_key)}")
            raise ValueError(
                f"ELEVENLABS_API_KEY appears to be invalid or a placeholder. "
                f"API key starts with: {self.api_key[:20]}... "
                f"Please set a valid ElevenLabs API key in your .env file at: {backend_dir / '.env'}. "
                f"Get your API key from: https://elevenlabs.io/app/settings/api-keys"
            )
        
        # Log API key format (first 10 chars only for security)
        logger.info(f"ElevenLabs TTS API key loaded (starts with: {self.api_key[:10]}...)")
        
        # ElevenLabs API base URL
        self.base_url = os.getenv("ELEVENLABS_BASE_URL", "https://api.elevenlabs.io/v1")
        self.tts_endpoint = f"{self.base_url}/text-to-speech"
        
        # Default voice ID (can be configured)
        # Using a voice that's available to all accounts (Rachel - free tier compatible)
        # If you get 403 errors, try: pNInz6obpgDQGcFmaJgB (Adam) or EXAVITQu4vr4xnSDxMaL (Bella)
        self.default_voice_id = os.getenv("ELEVENLABS_VOICE_ID", "pNInz6obpgDQGcFmaJgB")  # Adam voice (free tier)
        
        # Default model ID (can be configured)
        self.default_model_id = os.getenv("ELEVENLABS_MODEL_ID", "eleven_multilingual_v2")
        
        logger.info("ElevenLabs TTS client initialized")
    
    def synthesize(
        self,
        text: str,
        voice: str = "default",
        speed: float = 1.0,
        format: str = "mp3_44100_128",  # ElevenLabs requires specific format, not just "mp3"
        sample_rate: int = 24000
    ) -> bytes:
        """
        Convert text to speech audio
        
        Args:
            text: Text to convert to speech
            voice: Voice ID or name (default: "default" uses default_voice_id)
            speed: Speech speed multiplier (0.25 to 4.0, default: 1.0)
            format: Audio format ("mp3", "pcm", default: "mp3")
            sample_rate: Audio sample rate in Hz (24000, 22050, 16000, 8000, default: 24000)
        
        Returns:
            bytes: Audio file data
        
        Raises:
            ValueError: If text is empty
            requests.RequestException: If API request fails
        """
        if not text or not text.strip():
            raise ValueError("text cannot be empty")
        
        # Use default voice ID if "default" is specified
        voice_id = self.default_voice_id if voice == "default" else voice
        
        headers = {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json"
        }
        
        # Clamp speed to valid range
        speed = max(0.25, min(4.0, speed))
        
        payload = {
            "text": text,
            "model_id": self.default_model_id,  # ElevenLabs TTS model
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75,
                "style": 0.0,
                "use_speaker_boost": True
            }
        }
        
        # Add speed if not default
        if speed != 1.0:
            payload["voice_settings"]["speed"] = speed
        
        try:
            # Log which API key is being used (for debugging)
            key_preview = f"{self.api_key[:10]}...{self.api_key[-4:]}" if len(self.api_key) > 14 else self.api_key[:10] + "..."
            logger.info(f"🔑 Using API key: {key_preview} (length: {len(self.api_key)})")
            logger.info(f"Synthesizing speech for text: {text[:100]}... (voice: {voice_id}, speed: {speed})")
            
            # ElevenLabs TTS endpoint format: /v1/text-to-speech/{voice_id}
            # ElevenLabs requires specific output formats, not just "mp3"
            # Valid formats: mp3_44100_128, mp3_24000_48, wav_44100, opus_48000_128, etc.
            # If format is just "mp3", convert to a valid format
            output_format = format
            if format == "mp3":
                output_format = "mp3_44100_128"  # High quality MP3
            elif format not in ["mp3_22050_32", "mp3_24000_48", "mp3_44100_128", "mp3_44100_192", 
                               "mp3_44100_32", "mp3_44100_64", "mp3_44100_96", "wav_44100", 
                               "opus_48000_128"]:
                # Default to high quality MP3 if format is not recognized
                logger.warning(f"Unrecognized format '{format}', using 'mp3_44100_128'")
                output_format = "mp3_44100_128"
            
            response = requests.post(
                f"{self.tts_endpoint}/{voice_id}",
                headers=headers,
                json=payload,
                params={
                    "output_format": output_format,
                    "optimize_streaming_latency": "0"
                },
                timeout=30
            )
            
            response.raise_for_status()
            
            # ElevenLabs returns audio directly as bytes
            audio_data = response.content
            
            logger.info(f"Speech synthesis successful (audio size: {len(audio_data)} bytes)")
            
            return audio_data
        
        except requests.exceptions.HTTPError as e:
            # Extract error details from the response
            status_code = None
            error_detail = "No response body"
            response_headers = {}
            
            # Properly extract status code and error details
            if hasattr(e, 'response') and e.response is not None:
                status_code = e.response.status_code
                try:
                    # Try to get error message from response
                    if e.response.text:
                        error_detail = e.response.text
                        # Try to parse JSON error if available
                        content_type = e.response.headers.get('content-type', '')
                        if 'application/json' in content_type:
                            try:
                                error_json = e.response.json()
                                if isinstance(error_json, dict):
                                    error_detail = error_json.get('detail', {}).get('message', str(error_json))
                                else:
                                    error_detail = str(error_json)
                            except Exception:
                                pass
                    else:
                        error_detail = "Empty response body"
                except Exception as parse_error:
                    error_detail = f"Could not parse response: {parse_error}"
                
                response_headers = dict(e.response.headers)
            else:
                # If no response object, try to get status from exception message
                error_msg = str(e)
                if "403" in error_msg:
                    status_code = 403
                elif "401" in error_msg:
                    status_code = 401
            
            logger.error(f"❌ ElevenLabs TTS API error: {status_code}")
            logger.error(f"   API key starts with: {self.api_key[:10]}...")
            logger.error(f"   Voice ID: {voice_id}")
            logger.error(f"   Model ID: {self.default_model_id}")
            logger.error(f"   Error details: {error_detail}")
            logger.error(f"   Response headers: {response_headers}")
            
            # Check if it's actually a quota error (sometimes returned as 401)
            is_quota_error = "quota" in error_detail.lower() or "credits" in error_detail.lower() or "exceeds" in error_detail.lower()
            
            if status_code == 401 and is_quota_error:
                # This is actually a quota error, not an auth error
                # Extract credit information from error message if available
                import re
                credit_info = ""
                quota_match = re.search(r'quota of (\d+)', error_detail, re.IGNORECASE)
                remaining_match = re.search(r'(\d+) credits? remaining', error_detail, re.IGNORECASE)
                required_match = re.search(r'(\d+) credits? are required', error_detail, re.IGNORECASE)
                
                if quota_match and remaining_match:
                    quota_total = quota_match.group(1)
                    remaining = remaining_match.group(1)
                    used = int(quota_total) - int(remaining)
                    credit_info = f"\nYour monthly quota: {quota_total} credits\n"
                    credit_info += f"Credits used this month: {used} credits\n"
                    credit_info += f"Credits remaining: {remaining} credits\n"
                    if required_match:
                        required = required_match.group(1)
                        credit_info += f"Credits needed for this request: {required} credits\n"
                
                raise requests.RequestException(
                    f"ElevenLabs monthly quota exceeded (401/Quota Error).\n\n"
                    f"{credit_info}\n"
                    f"Note: The quota is monthly, not daily. You may have used most of your monthly credits.\n"
                    f"Error details: {error_detail}\n\n"
                    f"This means your response text is too long and requires more credits than you have available.\n"
                    f"Solutions:\n"
                    f"1. Wait for your monthly quota to reset\n"
                    f"2. Upgrade your ElevenLabs subscription for more credits\n"
                    f"3. The response will be truncated to fit within your remaining credit limit\n"
                    f"4. Check your monthly usage at: https://elevenlabs.io/app/settings/usage\n\n"
                    f"Original error: {error_detail}"
                )
            elif status_code == 401:
                raise requests.RequestException(
                    f"Invalid ElevenLabs API key (401 Unauthorized). "
                    f"API key starts with: {self.api_key[:10]}...\n"
                    f"Please verify:\n"
                    f"1. Your ELEVENLABS_API_KEY is correct in the .env file\n"
                    f"2. The API key has TTS (Text-to-Speech) permissions enabled\n"
                    f"3. The API key is not expired\n"
                    f"4. Your account subscription includes TTS access\n"
                    f"Get your API key from: https://elevenlabs.io/app/settings/api-keys\n"
                    f"Error details: {error_detail}"
                )
            elif status_code == 403:
                raise requests.RequestException(
                    f"ElevenLabs API access forbidden (403 Forbidden).\n\n"
                    f"This usually means:\n"
                    f"1. The API key doesn't have 'Text to Speech' permission enabled\n"
                    f"2. Your account subscription doesn't include TTS access\n"
                    f"3. The voice ID '{voice_id}' is not available to your account\n"
                    f"4. Rate limit or quota exceeded\n"
                    f"5. The voice ID requires a paid subscription\n\n"
                    f"Please check:\n"
                    f"- Go to https://elevenlabs.io/app/settings/api-keys\n"
                    f"- Edit your API key and ensure 'Text to Speech' has 'Access' enabled (not 'No Access')\n"
                    f"- Click 'Save Changes' after enabling the permission\n"
                    f"- Verify your account has an active subscription with TTS access\n"
                    f"- Try using a different voice ID if this one is restricted\n"
                    f"- Check if you've exceeded your monthly character limit\n\n"
                    f"Error details: {error_detail}"
                )
            else:
                raise requests.RequestException(
                    f"TTS API error: {status_code} - {error_detail}\n"
                    f"Voice ID: {voice_id}, Model: {self.default_model_id}"
                )
        
        except requests.exceptions.RequestException as e:
            logger.error(f"ElevenLabs TTS request failed: {e}")
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


