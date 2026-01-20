"""
Voice API Routes
Handles Speech-to-Text and Text-to-Speech endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from fastapi.responses import Response
from pydantic import BaseModel, Field
from typing import Optional
import logging
import io
import os
import requests
from dotenv import load_dotenv
from pathlib import Path

from voice.stt_client import ElevenLabsSTTClient
from voice.assemblyai_stt_client import AssemblyAISTTClient
from voice.tts_client import AssemblyAITTSClient
from voice.elevenlabs_tts_client import ElevenLabsTTSClient
from typing import Union
from llm.orchestrator import LLMOrchestrator
from api.routes.trip import get_orchestrator

# Get backend directory for .env file
backend_dir = Path(__file__).parent.parent
env_path = backend_dir / ".env"

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/voice", tags=["voice"])

# Initialize clients (singleton pattern)
_stt_client = None
_tts_client = None

# STT Provider selection: "elevenlabs" or "assemblyai" (default: assemblyai)
STT_PROVIDER = os.getenv("STT_PROVIDER", "assemblyai").lower()
logger.info(f"📢 STT Provider configured: {STT_PROVIDER}")

# TTS Provider selection: "elevenlabs" or "assemblyai" (default: elevenlabs)
# Note: AssemblyAI doesn't actually offer TTS, so elevenlabs is recommended
TTS_PROVIDER = os.getenv("TTS_PROVIDER", "elevenlabs").lower()
logger.info(f"🔊 TTS Provider configured: {TTS_PROVIDER}")


def get_stt_client() -> Optional[Union[ElevenLabsSTTClient, AssemblyAISTTClient]]:
    """Get or create STT client instance"""
    global _stt_client
    
    if _stt_client is None:
        try:
            if STT_PROVIDER == "assemblyai":
                _stt_client = AssemblyAISTTClient()
                logger.info("✅ STT Client initialized: AssemblyAI")
            else:
                _stt_client = ElevenLabsSTTClient()
                logger.info("✅ STT Client initialized: ElevenLabs")
        except ValueError as e:
            logger.error(f"❌ STT client initialization failed: {e}")
            _stt_client = None
    
    return _stt_client


def get_tts_client():
    """Get or create TTS client instance"""
    global _tts_client
    
    # Reload .env file to pick up any changes (e.g., new API keys)
    # This allows picking up new API keys without full server restart
    load_dotenv(dotenv_path=env_path, override=True)
    current_api_key = os.getenv("ELEVENLABS_API_KEY")
    
    if _tts_client is None:
        try:
            if TTS_PROVIDER == "elevenlabs":
                _tts_client = ElevenLabsTTSClient()
                logger.info(f"✅ ElevenLabs TTS client initialized (API key starts with: {current_api_key[:15] if current_api_key else 'None'}...)")
            else:
                _tts_client = AssemblyAITTSClient()
                logger.warning("Using AssemblyAI for TTS (Note: AssemblyAI may not support TTS)")
        except ValueError as e:
            logger.warning(f"TTS client not available: {e}")
            _tts_client = None
    elif TTS_PROVIDER == "elevenlabs" and hasattr(_tts_client, 'api_key'):
        # Check if API key has changed and re-initialize if needed
        if current_api_key and _tts_client.api_key != current_api_key:
            logger.info(f"🔄 ELEVENLABS_API_KEY changed detected!")
            logger.info(f"   Old key starts with: {_tts_client.api_key[:15]}...")
            logger.info(f"   New key starts with: {current_api_key[:15]}...")
            logger.info("   Re-initializing TTS client...")
            try:
                _tts_client = ElevenLabsTTSClient()
                logger.info("✅ TTS client re-initialized with new API key")
            except ValueError as e:
                logger.warning(f"Failed to re-initialize TTS client: {e}")
    
    return _tts_client


class TranscribeRequest(BaseModel):
    """Request model for transcription"""
    language: Optional[str] = Field(default="en", description="Language code")
    model: Optional[str] = Field(default=None, description="Optional model name")


class TranscribeResponse(BaseModel):
    """Response model for transcription"""
    text: str = Field(description="Transcribed text")
    language: str = Field(description="Detected language")
    confidence: float = Field(description="Confidence score (0-1)")


class SynthesizeRequest(BaseModel):
    """Request model for speech synthesis"""
    text: str = Field(description="Text to convert to speech")
    voice: Optional[str] = Field(default="default", description="Voice ID or name")
    speed: Optional[float] = Field(default=1.0, description="Speech speed (0.5-2.0)")
    format: Optional[str] = Field(default="mp3", description="Audio format (mp3, wav, pcm)")


class VoiceChatRequest(BaseModel):
    """Request model for integrated voice chat"""
    session_id: Optional[str] = Field(default=None, description="Session ID for conversation context")
    language: Optional[str] = Field(default="en", description="Language code for STT")
    voice: Optional[str] = Field(default="default", description="Voice ID for TTS")
    speed: Optional[float] = Field(default=1.0, description="Speech speed for TTS")


@router.post("/transcribe", response_model=TranscribeResponse)
async def transcribe_audio(
    audio: UploadFile = File(..., description="Audio file to transcribe"),
    language: str = Form(default="en", description="Language code"),
    model: Optional[str] = Form(default=None, description="Optional model name"),
    stt_client: Optional[Union[ElevenLabsSTTClient, AssemblyAISTTClient]] = Depends(get_stt_client)
):
    """
    Transcribe audio to text using STT provider (AssemblyAI or ElevenLabs)
    
    Accepts audio file upload and returns transcribed text.
    """
    if not stt_client:
        provider_name = "ElevenLabs" if STT_PROVIDER == "elevenlabs" else "AssemblyAI"
        api_key_name = "ELEVENLABS_API_KEY" if STT_PROVIDER == "elevenlabs" else "ASSEMBLYAI_API_KEY"
        raise HTTPException(
            status_code=503,
            detail=f"Speech-to-Text service is not available. Please check {api_key_name} configuration."
        )
    
    try:
        # Read audio file
        audio_data = await audio.read()
        
        if not audio_data:
            raise HTTPException(status_code=400, detail="Audio file is empty")
        
        logger.info(f"Transcribing audio file: {audio.filename} (size: {len(audio_data)} bytes)")
        
        # Transcribe
        result = stt_client.transcribe(audio_data, language=language, model=model)
        
        return TranscribeResponse(
            text=result["text"],
            language=result["language"],
            confidence=result["confidence"]
        )
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Transcription error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")


@router.post("/synthesize")
async def synthesize_speech(
    request: SynthesizeRequest,
    tts_client = Depends(get_tts_client)
):
    """
    Convert text to speech using TTS provider (ElevenLabs or AssemblyAI)
    
    Returns audio file as binary response.
    """
    if not tts_client:
        provider_name = "ElevenLabs" if TTS_PROVIDER == "elevenlabs" else "AssemblyAI"
        api_key_name = "ELEVENLABS_API_KEY" if TTS_PROVIDER == "elevenlabs" else "ASSEMBLYAI_API_KEY"
        raise HTTPException(
            status_code=503,
            detail=f"Text-to-Speech service is not available. Please check {api_key_name} configuration."
        )
    
    try:
        logger.info(f"Synthesizing speech for text: {request.text[:100]}...")
        
        # Synthesize speech
        audio_data = tts_client.synthesize(
            text=request.text,
            voice=request.voice,
            speed=request.speed,
            format=request.format
        )
        
        # Determine content type based on format
        content_type_map = {
            "mp3": "audio/mpeg",
            "wav": "audio/wav",
            "pcm": "audio/pcm"
        }
        content_type = content_type_map.get(request.format, "audio/mpeg")
        
        return Response(
            content=audio_data,
            media_type=content_type,
            headers={
                "Content-Disposition": f'attachment; filename="speech.{request.format}"'
            }
        )
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Speech synthesis error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Speech synthesis failed: {str(e)}")


@router.get("/health")
async def voice_health_check():
    """Health check endpoint to verify all services are configured"""
    health_status = {
        "status": "healthy",
        "services": {}
    }
    
    # Check STT
    try:
        stt = get_stt_client()
        health_status["services"]["stt"] = {
            "available": stt is not None,
            "provider": STT_PROVIDER
        }
    except Exception as e:
        health_status["services"]["stt"] = {
            "available": False,
            "error": str(e)
        }
    
    # Check TTS
    try:
        tts = get_tts_client()
        health_status["services"]["tts"] = {
            "available": tts is not None,
            "provider": TTS_PROVIDER
        }
    except Exception as e:
        health_status["services"]["tts"] = {
            "available": False,
            "error": str(e)
        }
    
    # Check Orchestrator
    try:
        from api.routes.trip import get_orchestrator
        orchestrator = get_orchestrator()
        health_status["services"]["orchestrator"] = {
            "available": orchestrator is not None,
            "provider": orchestrator.llm_client.provider if orchestrator else None
        }
    except Exception as e:
        health_status["services"]["orchestrator"] = {
            "available": False,
            "error": str(e)
        }
        health_status["status"] = "degraded"
    
    return health_status


@router.post("/chat")
async def voice_chat(
    audio: UploadFile = File(..., description="Audio file with user's voice input"),
    session_id: Optional[str] = Form(default=None, description="Session ID for conversation context"),
    language: str = Form(default="en", description="Language code for STT"),
    voice: str = Form(default="default", description="Voice ID for TTS"),
    speed: float = Form(default=1.0, description="Speech speed for TTS"),
    stt_client = Depends(get_stt_client),
    tts_client = Depends(get_tts_client),
    orchestrator: LLMOrchestrator = Depends(get_orchestrator)
):
    """
    Integrated voice chat endpoint
    
    Full flow: Speech → STT → Text → Backend → Text → TTS → Speech
    
    This endpoint:
    1. Receives audio file (user's voice)
    2. Transcribes it to text using STT
    3. Sends text to the trip planning backend
    4. Gets text response from backend
    5. Converts response to speech using TTS
    6. Returns audio file with AI's voice response
    """
    if not stt_client:
        provider_name = "ElevenLabs" if STT_PROVIDER == "elevenlabs" else "AssemblyAI"
        api_key_name = "ELEVENLABS_API_KEY" if STT_PROVIDER == "elevenlabs" else "ASSEMBLYAI_API_KEY"
        raise HTTPException(
            status_code=503,
            detail=f"Speech-to-Text service is not available. Please check {api_key_name} configuration."
        )
    
    if not tts_client:
        provider_name = "ElevenLabs" if TTS_PROVIDER == "elevenlabs" else "AssemblyAI"
        api_key_name = "ELEVENLABS_API_KEY" if TTS_PROVIDER == "elevenlabs" else "ASSEMBLYAI_API_KEY"
        raise HTTPException(
            status_code=503,
            detail=f"Text-to-Speech service is not available. Please check {api_key_name} configuration."
        )
    
    try:
        # Step 1: Transcribe audio to text
        logger.info(f"Step 1: Transcribing audio (session: {session_id})")
        audio_data = await audio.read()
        
        if not audio_data:
            raise HTTPException(status_code=400, detail="Audio file is empty")
        
        transcription_result = stt_client.transcribe(audio_data, language=language)
        user_text = transcription_result["text"]
        
        logger.info(f"Transcribed text: {user_text}")
        
        if not user_text or not user_text.strip():
            raise HTTPException(
                status_code=400,
                detail="Could not transcribe audio. Please ensure the audio is clear and contains speech."
            )
        
        # Step 2: Process with backend (trip planning orchestrator)
        logger.info(f"Step 2: Processing with backend (session: {session_id})")
        
        # Get or create session
        if not session_id:
            session_id = orchestrator.session_manager.create_session()
            logger.info(f"Created new session: {session_id}")
        else:
            session = orchestrator.session_manager.get_session(session_id)
            if not session:
                session_id = orchestrator.session_manager.create_session()
                logger.info(f"Session expired, created new: {session_id}")
        
        # Process user request
        backend_result = orchestrator.process_user_request(
            user_message=user_text,
            session_id=session_id
        )
        
        ai_text = backend_result.get("response", "")
        
        if not ai_text:
            ai_text = "I'm sorry, I couldn't generate a response. Please try again."
        
        logger.info(f"Backend response: {ai_text[:100]}...")
        
        # Step 3: Convert response to speech
        logger.info(f"Step 3: Synthesizing speech response")
        
        # Estimate character count and truncate if needed to avoid quota issues
        # ElevenLabs charges ~1 credit per character, so we need to be mindful of length
        # Start with a conservative limit, but be ready to reduce further if quota is low
        MAX_CHARACTERS = 8000  # Initial limit
        
        if len(ai_text) > MAX_CHARACTERS:
            logger.warning(f"Response text is {len(ai_text)} characters, truncating to {MAX_CHARACTERS} to avoid quota issues")
            # Truncate at a sentence boundary if possible
            truncated = ai_text[:MAX_CHARACTERS]
            last_period = truncated.rfind('.')
            last_newline = truncated.rfind('\n')
            cutoff = max(last_period, last_newline)
            if cutoff > MAX_CHARACTERS * 0.8:  # Only use cutoff if it's not too short
                ai_text = truncated[:cutoff + 1] + "\n\n[Response truncated due to length]"
            else:
                ai_text = truncated + "... [Response truncated]"
            logger.info(f"Truncated response to {len(ai_text)} characters")
        
        try:
            audio_response = tts_client.synthesize(
                text=ai_text,
                voice=voice,
                speed=speed,
                format="mp3"
            )
        except requests.exceptions.RequestException as tts_error:
            error_msg = str(tts_error)
            # If quota error, try with progressively shorter text
            if "quota" in error_msg.lower() or "credits" in error_msg.lower():
                logger.warning("Quota error detected, trying with progressively shorter responses...")
                
                # Extract remaining credits from error if possible
                import re
                remaining_credits = None
                credit_match = re.search(r'(\d+) credits? remaining', error_msg, re.IGNORECASE)
                if credit_match:
                    remaining_credits = int(credit_match.group(1))
                    # Use 80% of remaining credits to be safe
                    max_chars = int(remaining_credits * 0.8) if remaining_credits else 200
                else:
                    max_chars = 200  # Very conservative fallback
                
                # Try progressively shorter texts
                retry_lengths = [max_chars, 150, 100, 50]
                
                for retry_len in retry_lengths:
                    if retry_len >= len(ai_text):
                        continue  # Skip if already shorter
                    
                    short_text = ai_text[:retry_len]
                    # Try to end at a sentence
                    last_period = short_text.rfind('.')
                    if last_period > retry_len * 0.7:
                        short_text = short_text[:last_period + 1]
                    
                    short_text += "\n\n[Response shortened due to credit limit]"
                    logger.info(f"Retrying with {len(short_text)} characters (target: {retry_len})")
                    
                    try:
                        audio_response = tts_client.synthesize(
                            text=short_text,
                            voice=voice,
                            speed=speed,
                            format="mp3"
                        )
                        logger.info(f"Successfully generated audio with {len(short_text)} characters")
                        ai_text = short_text  # Update ai_text for response
                        break
                    except requests.exceptions.RequestException as retry_error:
                        retry_error_msg = str(retry_error)
                        if "quota" not in retry_error_msg.lower() and "credits" not in retry_error_msg.lower():
                            # Different error, re-raise
                            raise
                        # Still quota error, try next shorter length
                        logger.warning(f"Still quota error with {len(short_text)} chars, trying shorter...")
                        continue
                else:
                    # All retries failed
                    logger.error(f"Failed even with shortest text. Remaining credits: {remaining_credits}")
                    raise HTTPException(
                        status_code=402,
                        detail=f"Quota exceeded. Your account has insufficient credits remaining. "
                               f"Remaining: {remaining_credits or 'unknown'} credits. "
                               f"Please upgrade your ElevenLabs subscription or wait for quota reset. "
                               f"Error: {error_msg}"
                    )
            else:
                raise
        
        logger.info(f"Voice chat complete (session: {session_id})")
        
        # Get sources from session
        session = orchestrator.session_manager.get_session(session_id)
        raw_sources = session.get("sources", []) if session else []
        
        logger.info(f"🔍 Checking sources in session {session_id}: {len(raw_sources)} raw sources found")
        if raw_sources:
            logger.info(f"   First source structure: {raw_sources[0] if raw_sources else 'None'}")
        
        # Transform citations to frontend format: {id, name, type, url}
        # Backend format: {source, url, section, section_anchor}
        sources = []
        seen_urls = set()
        
        for idx, citation in enumerate(raw_sources):
            url = citation.get("url", "")
            source_name = citation.get("source", "Unknown Source")
            
            # Skip duplicates by URL
            if url and url in seen_urls:
                continue
            if url:
                seen_urls.add(url)
            
            # Transform to frontend format
            transformed_source = {
                "id": f"source_{idx}_{hash(url) if url else hash(source_name)}",
                "name": source_name,
                "type": citation.get("section", "General"),
                "url": url
            }
            sources.append(transformed_source)
        
        sources = sources[:10]  # Limit to 10 sources
        logger.info(f"✅ Transformed {len(sources)} sources for frontend (from {len(raw_sources)} raw citations)")
        
        # Return audio response
        # Note: Custom headers with text content must be encoded to avoid invalid characters
        # HTTP headers can only contain ASCII characters, so we encode text values
        import base64
        import json
        
        # Encode text headers to base64 to avoid invalid characters (newlines, unicode, etc.)
        encoded_user_text = base64.b64encode(user_text.encode('utf-8')).decode('ascii')
        encoded_ai_text = base64.b64encode(ai_text.encode('utf-8')).decode('ascii')
        
        # Encode sources as JSON and then base64
        encoded_sources = ""
        if sources:
            sources_json = json.dumps(sources)
            encoded_sources = base64.b64encode(sources_json.encode('utf-8')).decode('ascii')
            logger.info(f"📤 Sending {len(sources)} sources in X-Sources header (encoded length: {len(encoded_sources)})")
            logger.debug(f"   First source: {sources[0] if sources else 'None'}")
        else:
            logger.warning("⚠️  No sources to send in response")
        
        headers = {
            "Content-Disposition": 'attachment; filename="response.mp3"',
            "X-Session-Id": session_id or "",
            "X-Transcribed-Text": encoded_user_text,
            "X-AI-Response": encoded_ai_text,
            "X-Encoding": "base64"  # Indicate that custom headers are base64 encoded
        }
        
        # Add sources header if available
        if encoded_sources:
            headers["X-Sources"] = encoded_sources
            logger.info(f"✅ Added X-Sources header to response")
        else:
            logger.warning("⚠️  X-Sources header NOT added (no sources or encoding failed)")
        
        return Response(
            content=audio_response,
            media_type="audio/mpeg",
            headers=headers
        )
    
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"ValueError in voice chat: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        logger.error(f"Voice chat error: {e}", exc_info=True)
        logger.error(f"Full traceback:\n{error_traceback}")
        # Provide more detailed error message for debugging
        error_detail = str(e)
        if "api" in error_detail.lower() or "key" in error_detail.lower():
            error_detail = f"API configuration error: {error_detail}. Please check your API keys in Render environment variables."
        elif "import" in error_detail.lower() or "module" in error_detail.lower():
            error_detail = f"Module import error: {error_detail}. Please check that all dependencies are installed."
        raise HTTPException(
            status_code=500, 
            detail=f"Voice chat failed: {error_detail}. Check backend logs for full traceback."
        )


@router.get("/debug/api-key")
async def debug_api_key():
    """
    Debug endpoint to check which API key is currently being used.
    This helps verify if the new API key from .env is being loaded.
    """
    # Reload .env to get latest values
    load_dotenv(dotenv_path=env_path, override=True)
    
    current_key = os.getenv("ELEVENLABS_API_KEY")
    tts_client = get_tts_client()
    
    result = {
        "env_file_path": str(env_path),
        "env_file_exists": env_path.exists(),
        "current_api_key_from_env": current_key[:20] + "..." if current_key else None,
        "tts_provider": TTS_PROVIDER,
        "tts_client_initialized": tts_client is not None,
    }
    
    if tts_client and hasattr(tts_client, 'api_key'):
        result["tts_client_api_key"] = tts_client.api_key[:20] + "..." if tts_client.api_key else None
        result["keys_match"] = current_key == tts_client.api_key if current_key else False
    
    return result




