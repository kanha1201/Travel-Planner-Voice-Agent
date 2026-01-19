# Voice API Integration

This module provides Speech-to-Text (STT) and Text-to-Speech (TTS) functionality for the Voice Travel Planner.

## Architecture

```
Speech → STT → Text → Backend → Text → TTS → Speech
```

## Components

### 1. STT Client (`stt_client.py`)
- **Provider**: ElevenLabs
- **Purpose**: Converts audio (speech) to text
- **Note**: ElevenLabs is primarily a TTS service. If STT endpoints are not available, consider using AssemblyAI or another STT provider.

### 2. TTS Client (`tts_client.py`)
- **Provider**: AssemblyAI
- **Purpose**: Converts text to audio (speech)
- **Note**: AssemblyAI is primarily an STT service. If TTS endpoints are not available, consider using ElevenLabs or another TTS provider.

## API Endpoints

### `/api/voice/transcribe` (POST)
Transcribes audio file to text.

**Request:**
- `audio`: Audio file (multipart/form-data)
- `language`: Language code (default: "en")
- `model`: Optional model name

**Response:**
```json
{
  "text": "Transcribed text",
  "language": "en",
  "confidence": 0.95
}
```

### `/api/voice/synthesize` (POST)
Converts text to speech audio.

**Request:**
```json
{
  "text": "Text to convert to speech",
  "voice": "default",
  "speed": 1.0,
  "format": "mp3"
}
```

**Response:**
- Audio file (binary, MP3/WAV/PCM)

### `/api/voice/chat` (POST)
Integrated voice chat endpoint that handles the full flow:
1. Receives audio (user's voice)
2. Transcribes to text (STT)
3. Processes with backend (trip planning)
4. Converts response to speech (TTS)
5. Returns audio (AI's voice)

**Request:**
- `audio`: Audio file (multipart/form-data)
- `session_id`: Optional session ID for conversation context
- `language`: Language code (default: "en")
- `voice`: Voice ID for TTS (default: "default")
- `speed`: Speech speed (default: 1.0)

**Response:**
- Audio file (binary, MP3)
- Headers:
  - `X-Session-Id`: Session ID
  - `X-Transcribed-Text`: User's transcribed text
  - `X-AI-Response`: AI's text response

## Environment Variables

Add these to your `.env` file:

```bash
# ElevenLabs STT Configuration
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
ELEVENLABS_BASE_URL=https://api.elevenlabs.io/v1

# AssemblyAI TTS Configuration
ASSEMBLYAI_API_KEY=your_assemblyai_api_key_here
ASSEMBLYAI_BASE_URL=https://api.assemblyai.com/v2
```

## Important Notes

1. **Service Availability**: The current implementation uses ElevenLabs for STT and AssemblyAI for TTS. However, these services are typically used the other way around:
   - ElevenLabs is primarily a TTS service
   - AssemblyAI is primarily an STT service

2. **API Endpoints**: The actual API endpoints may differ from what's implemented. You may need to:
   - Check the official API documentation for the correct endpoints
   - Update `stt_endpoint` in `stt_client.py` if ElevenLabs STT endpoint differs
   - Update `tts_endpoint` in `tts_client.py` if AssemblyAI TTS endpoint differs

3. **Alternative Providers**: If the specified services don't support the required functionality:
   - **For STT**: Consider using AssemblyAI, Deepgram, or OpenAI Whisper
   - **For TTS**: Consider using ElevenLabs, Google Cloud TTS, or Azure Speech

## Testing

You can test the endpoints using curl or any HTTP client:

```bash
# Test transcription
curl -X POST "http://localhost:8000/api/voice/transcribe" \
  -F "audio=@test_audio.wav" \
  -F "language=en"

# Test synthesis
curl -X POST "http://localhost:8000/api/voice/synthesize" \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello, this is a test", "voice": "default", "format": "mp3"}' \
  --output response.mp3

# Test integrated voice chat
curl -X POST "http://localhost:8000/api/voice/chat" \
  -F "audio=@user_voice.wav" \
  -F "language=en" \
  -F "voice=default" \
  --output ai_response.mp3
```

## Error Handling

- If API keys are missing, the endpoints will return 503 (Service Unavailable)
- If audio is empty or invalid, returns 400 (Bad Request)
- If API calls fail, returns 500 (Internal Server Error) with error details








