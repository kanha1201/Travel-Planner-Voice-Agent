"""
Speech-to-Text (STT) Client using AssemblyAI API

AssemblyAI is a primary STT service provider.
This is the recommended STT client.

Uses the official AssemblyAI Python SDK for reliable file handling.
"""

import os
import logging
import subprocess
import tempfile
from typing import Optional, Dict
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Try to import AssemblyAI SDK, fall back to requests if not available
try:
    import assemblyai as aai
    SDK_AVAILABLE = True
except ImportError:
    SDK_AVAILABLE = False
    logger.warning("AssemblyAI SDK not installed. Install with: pip install assemblyai")
    import requests


class AssemblyAISTTClient:
    """
    Speech-to-Text client using AssemblyAI API
    
    Uses the official AssemblyAI SDK for reliable file handling.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize AssemblyAI STT client
        
        Args:
            api_key: AssemblyAI API key. If not provided, reads from ASSEMBLYAI_API_KEY env var
        """
        self.api_key = api_key or os.getenv("ASSEMBLYAI_API_KEY")
        if not self.api_key:
            raise ValueError("ASSEMBLYAI_API_KEY not found in environment variables")
        
        self.use_sdk = False
        if SDK_AVAILABLE:
            # Use official SDK
            try:
                logger.info("🔧 Initializing AssemblyAI SDK...")
                aai.settings.api_key = self.api_key
                self.transcriber = aai.Transcriber()
                self.use_sdk = True
                logger.info("✅ AssemblyAI STT client initialized (using official SDK)")
            except Exception as sdk_init_error:
                logger.error(f"❌ SDK initialization failed: {sdk_init_error}")
                import traceback
                logger.error(traceback.format_exc())
                self.use_sdk = False
        
        if not self.use_sdk:
            # Fallback to manual API calls
            self.base_url = os.getenv("ASSEMBLYAI_BASE_URL", "https://api.assemblyai.com/v2")
            self.upload_endpoint = f"{self.base_url}/upload"
            self.transcript_endpoint = f"{self.base_url}/transcript"
            logger.warning("⚠️ Using manual API calls (SDK not available)")
    
    def _convert_webm_to_wav(self, audio_data: bytes) -> bytes:
        """
        Convert WebM audio to WAV format using ffmpeg
        
        Args:
            audio_data: WebM audio bytes
            
        Returns:
            WAV audio bytes (PCM 16-bit, 16kHz, mono)
        """
        import tempfile
        
        # Create temporary files
        with tempfile.NamedTemporaryFile(delete=False, suffix='.webm') as input_file:
            input_file.write(audio_data)
            input_path = input_file.name
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as output_file:
            output_path = output_file.name
        
        try:
            # Use exact ffmpeg command recommended for AssemblyAI
            ffmpeg_command = [
                "ffmpeg",
                "-y",                    # Overwrite output
                "-i", input_path,        # Input file
                "-ar", "16000",          # Sample rate 16kHz
                "-ac", "1",              # Mono channel
                "-c:a", "pcm_s16le",     # PCM 16-bit signed little-endian
                "-f", "wav",             # WAV format
                "-hide_banner",
                "-loglevel", "error",
                output_path
            ]
            
            logger.info("🔄 Converting WebM to WAV using ffmpeg...")
            process = subprocess.run(
                ffmpeg_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=30
            )
            
            if process.returncode != 0:
                error_msg = process.stderr.decode('utf-8', errors='ignore') if process.stderr else "Unknown error"
                logger.error(f"❌ ffmpeg conversion failed: {error_msg}")
                raise ValueError(f"ffmpeg conversion failed: {error_msg}")
            
            # Log any warnings from ffmpeg
            if process.stderr:
                stderr_output = process.stderr.decode('utf-8', errors='ignore')
                if stderr_output.strip():
                    logger.debug(f"ffmpeg output: {stderr_output}")
            
            # Read the converted file
            with open(output_path, "rb") as f:
                wav_data = f.read()
            
            if len(wav_data) == 0:
                raise ValueError("ffmpeg conversion produced empty WAV file")
            
            # Validate WAV header
            if not (wav_data.startswith(b"RIFF") and b"WAVE" in wav_data[:12]):
                raise ValueError("Converted file does not have valid WAV header")
            
            # Validate using Python's wave module
            try:
                import wave
                with wave.open(output_path, 'rb') as wav_file:
                    channels = wav_file.getnchannels()
                    sample_rate = wav_file.getframerate()
                    sampwidth = wav_file.getsampwidth()
                    frames = wav_file.getnframes()
                    duration = frames / float(sample_rate) if sample_rate > 0 else 0
                    
                    logger.info(f"✅ WAV validation: {channels}ch, {sample_rate}Hz, {sampwidth*8}bit, {duration:.2f}s")
                    
                    if channels != 1:
                        raise ValueError(f"WAV must be mono (got {channels} channels)")
                    if sample_rate != 16000:
                        raise ValueError(f"WAV must be 16kHz (got {sample_rate} Hz)")
                    if sampwidth != 2:
                        raise ValueError(f"WAV must be 16-bit (got {sampwidth*8}-bit)")
                    if duration < 0.16:
                        raise ValueError(f"Audio too short: {duration:.3f}s (minimum 0.16s)")
            except Exception as validation_error:
                raise ValueError(f"WAV validation failed: {validation_error}")
            
            logger.info(f"✅ Conversion successful: {len(audio_data)} bytes → {len(wav_data)} bytes")
            return wav_data
            
        except FileNotFoundError:
            raise ValueError(
                "ffmpeg is not installed. Please install ffmpeg. "
                "Download from: https://ffmpeg.org/download.html"
            )
        except subprocess.TimeoutExpired:
            raise ValueError("Audio conversion timed out")
        except Exception as e:
            raise ValueError(f"Failed to convert audio: {str(e)}")
        finally:
            # Clean up temporary files
            try:
                if os.path.exists(input_path):
                    os.unlink(input_path)
                if os.path.exists(output_path):
                    os.unlink(output_path)
            except Exception as cleanup_error:
                logger.warning(f"Failed to clean up temp files: {cleanup_error}")
    
    def transcribe(
        self,
        audio_data: bytes,
        language: str = "en",
        model: Optional[str] = None
    ) -> Dict:
        """
        Transcribe audio to text using AssemblyAI
        
        Args:
            audio_data: Audio file bytes (any format)
            language: Language code (default: "en")
            model: Optional model name (e.g., "best" for best accuracy)
        
        Returns:
            Dict with transcription result:
            {
                "text": str,  # Transcribed text
                "language": str,  # Detected language
                "confidence": float,  # Confidence score (0-1)
            }
        """
        if not audio_data:
            raise ValueError("audio_data cannot be empty")
        
        logger.info(f"📤 Starting transcription (input size: {len(audio_data)} bytes, language: {language})")
        
        # Convert WebM to WAV if needed
        is_wav = audio_data.startswith(b"RIFF") and b"WAVE" in audio_data[:12]
        is_mp3 = audio_data.startswith(b"\xff\xfb") or audio_data.startswith(b"ID3")
        
        if not (is_wav or is_mp3):
            logger.info("🔄 Converting WebM to WAV for AssemblyAI compatibility...")
            audio_data = self._convert_webm_to_wav(audio_data)
        
        # Check if SDK should be used
        if hasattr(self, 'use_sdk') and self.use_sdk:
            # Use official SDK (most reliable)
            logger.info("🎙️ Using AssemblyAI SDK for transcription")
            return self._transcribe_with_sdk(audio_data, language, model)
        else:
            # Fallback to manual API calls
            logger.info("🎙️ Using manual API calls for transcription")
            return self._transcribe_with_requests(audio_data, language, model)
    
    def _transcribe_with_sdk(self, audio_data: bytes, language: str, model: Optional[str]) -> Dict:
        """Transcribe using official AssemblyAI SDK"""
        import tempfile
        import io
        
        try:
            # Configure transcription settings
            config = aai.TranscriptionConfig()
            
            # Set language code (convert format if needed: "en" -> "en_us")
            if language:
                # AssemblyAI uses format like "en_us", "en_uk", etc.
                # If just "en" provided, use "en_us" as default
                if language == "en":
                    config.language_code = "en_us"
                else:
                    config.language_code = language
            
            if model:
                config.model = model
            
            logger.info(f"🎙️ Starting transcription with AssemblyAI SDK (language: {config.language_code})...")
            
            # Method 1: Try using SDK's upload_file method (handles file format automatically)
            try:
                logger.info("📤 Uploading audio using SDK upload_file method...")
                # Create a file-like object from bytes
                audio_file = io.BytesIO(audio_data)
                audio_file.name = "audio.wav"  # Set filename for SDK
                
                # Upload using SDK (handles format detection automatically)
                upload_url = self.transcriber.upload_file(audio_file)
                logger.info(f"✅ Audio uploaded via SDK, URL: {upload_url[:50]}...")
                
                # Transcribe using the upload URL
                transcript = self.transcriber.transcribe(upload_url, config=config)
                
            except Exception as upload_error:
                logger.warning(f"SDK upload_file failed: {upload_error}, trying file path method...")
                # Method 2: Fallback to file path (SDK handles file upload internally)
                with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
                    temp_file.write(audio_data)
                    temp_path = temp_file.name
                
                try:
                    logger.info(f"📤 Transcribing from file path: {temp_path}")
                    transcript = self.transcriber.transcribe(temp_path, config=config)
                finally:
                    # Clean up temp file
                    try:
                        if os.path.exists(temp_path):
                            os.unlink(temp_path)
                    except Exception:
                        pass
            
            # Wait for completion (SDK handles polling automatically)
            # Check status
            if hasattr(transcript, 'status'):
                if transcript.status == aai.TranscriptStatus.error:
                    error_msg = getattr(transcript, 'error', 'Unknown error') or "Unknown error"
                    logger.error(f"❌ Transcription failed: {error_msg}")
                    raise ValueError(f"Transcription failed: {error_msg}")
            
            # Get results
            text = transcript.text or ""
            language_detected = getattr(transcript, 'language_code', None) or language
            confidence = getattr(transcript, 'confidence', None) or 1.0
            
            if not text:
                logger.warning("⚠️ Transcription returned empty text")
                text = ""  # Return empty string instead of failing
            
            logger.info(f"✅ Transcription successful: '{text[:100]}{'...' if len(text) > 100 else ''}'")
            
            return {
                "text": text,
                "language": language_detected,
                "confidence": confidence,
            }
            
        except Exception as e:
            logger.error(f"❌ Transcription error: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise
    
    def _transcribe_with_requests(self, audio_data: bytes, language: str, model: Optional[str]) -> Dict:
        """Fallback: Transcribe using manual API calls"""
        import requests
        import time
        import tempfile
        
        headers = {
            "authorization": self.api_key,
        }
        
        # Save to temporary file for upload
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
            temp_file.write(audio_data)
            temp_path = temp_file.name
        
        try:
            # Upload file using AssemblyAI's recommended method
            # According to AssemblyAI docs, upload should use Content-Type: application/octet-stream
            logger.info("📤 Uploading audio file to AssemblyAI...")
            
            # Read the file data
            with open(temp_path, 'rb') as audio_file:
                audio_bytes = audio_file.read()
            
            # Verify file is valid WAV before upload
            if not (audio_bytes.startswith(b"RIFF") and b"WAVE" in audio_bytes[:12]):
                raise ValueError("File is not a valid WAV file before upload")
            
            logger.info(f"📤 Uploading {len(audio_bytes)} bytes of WAV data...")
            
            # Upload with correct Content-Type header (AssemblyAI expects application/octet-stream)
            upload_headers = {
                "authorization": self.api_key,
                "Content-Type": "application/octet-stream"
            }
            
            upload_response = requests.post(
                self.upload_endpoint,
                headers=upload_headers,
                data=audio_bytes,  # Send raw bytes, not multipart form
                timeout=60
            )
            
            upload_response.raise_for_status()
            upload_result = upload_response.json()
            upload_url = upload_result.get("upload_url")
            
            if not upload_url:
                error_detail = upload_result.get("error", "No error message")
                raise ValueError(f"AssemblyAI did not return upload_url: {error_detail}")
            
            logger.info(f"✅ Audio uploaded successfully, URL: {upload_url[:50]}...")
            
            logger.info("✅ Audio uploaded, starting transcription...")
            
            # Start transcription
            # Convert language code format: "en" -> "en_us" for AssemblyAI
            language_code = language
            if language == "en":
                language_code = "en_us"
            
            transcript_data = {
                "audio_url": upload_url,
                "language_code": language_code,
            }
            if model:
                transcript_data["model"] = model
            
            logger.info(f"📝 Creating transcription job (language: {language_code})...")
            transcript_response = requests.post(
                self.transcript_endpoint,
                headers=headers,
                json=transcript_data,
                timeout=30
            )
            
            # Check for errors in response
            if transcript_response.status_code != 200:
                error_detail = transcript_response.text
                logger.error(f"❌ Transcription request failed: {transcript_response.status_code} - {error_detail}")
                raise ValueError(f"Transcription request failed: {transcript_response.status_code} - {error_detail}")
            
            transcript_response.raise_for_status()
            transcript_result = transcript_response.json()
            transcript_id = transcript_result.get("id")
            
            if not transcript_id:
                raise ValueError("AssemblyAI did not return transcript ID")
            
            logger.info(f"📝 Transcription job created (ID: {transcript_id}), polling for results...")
            
            # Poll for completion
            max_attempts = 60
            for attempt in range(max_attempts):
                status_response = requests.get(
                    f"{self.transcript_endpoint}/{transcript_id}",
                    headers=headers,
                    timeout=30
                )
                status_response.raise_for_status()
                status_data = status_response.json()
                
                status = status_data.get("status")
                
                if status == "completed":
                    text = status_data.get("text", "")
                    language_detected = status_data.get("language_code", language)
                    confidence = status_data.get("confidence", 1.0)
                    
                    logger.info(f"✅ Transcription completed: '{text[:100]}{'...' if len(text) > 100 else ''}'")
                    return {
                        "text": text,
                        "language": language_detected,
                        "confidence": confidence,
                    }
                elif status == "error":
                    error_msg = status_data.get("error", "Unknown error")
                    logger.error(f"❌ Transcription error: {error_msg}")
                    raise ValueError(f"Transcription failed: {error_msg}")
                
                # Log progress every 5 seconds
                if attempt % 5 == 0 and attempt > 0:
                    logger.info(f"⏳ Transcription in progress... (attempt {attempt + 1}/{max_attempts})")
                
                time.sleep(1)
            
            raise ValueError("Transcription timeout: took too long to complete")
            
        except requests.exceptions.HTTPError as e:
            error_detail = e.response.text if e.response else "No response body"
            logger.error(f"❌ HTTP error: {e.response.status_code} - {error_detail}")
            raise ValueError(f"HTTP error: {e.response.status_code} - {error_detail}")
        except Exception as e:
            logger.error(f"❌ Transcription error: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise
        finally:
            try:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
            except Exception:
                pass
    
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
