# Evaluation Guide

This document explains how to run evaluations and test the Voice Travel Planner system.

## Overview

Evaluations help ensure:
- **Functionality**: Tools work correctly
- **Quality**: Responses are accurate and helpful
- **Sources**: Citations are generated properly
- **Performance**: System responds in reasonable time

## Evaluation Types

### 1. Source Generation Testing

**Purpose**: Verify that sources are generated and stored correctly.

**Script**: `backend/test_sources.py`

**Run**:
```bash
cd backend
.\venv\Scripts\activate  # Windows
# or: source venv/bin/activate  # Linux/Mac
python test_sources.py
```

**What It Tests**:
1. Sources with `retrieve_city_guidance` tool
2. Sources during trip planning (from `search_pois`)
3. Source format transformation (backend → frontend)

**Expected Output**:
```
✅ Test 1 (retrieve_city_guidance): X sources
✅ Test 2 (trip planning): X sources
✅ Test 3 (format transformation): X sources
```

**Success Criteria**:
- Test 1: At least 1 source from RAG retrieval
- Test 2: At least 1 source from POI search (OpenStreetMap)
- Test 3: Sources correctly transformed to frontend format

---

### 2. Manual Voice Chat Testing

**Purpose**: Test end-to-end voice interaction flow.

**Steps**:

1. **Start Backend**:
   ```bash
   cd backend
   .\venv\Scripts\activate
   uvicorn main:app --reload
   ```

2. **Start Frontend**:
   ```bash
   cd voice-frontend
   npm run dev
   ```

3. **Open Browser**: Navigate to `http://localhost:5173`

4. **Test Scenarios** (see [SAMPLE_TRANSCRIPTS.md](SAMPLE_TRANSCRIPTS.md)):
   - Basic trip planning
   - Itinerary modifications
   - Question answering
   - Source citations

**Checklist**:
- [ ] Voice recording works
- [ ] Transcription is accurate
- [ ] LLM response is generated
- [ ] Audio playback works
- [ ] Itinerary is displayed correctly
- [ ] Sources appear in modal (click "i" button)
- [ ] Message formatting is correct (days, time periods, bullets)

---

### 3. API Endpoint Testing

**Purpose**: Test backend API endpoints directly.

**Tool**: FastAPI Swagger UI (`http://localhost:8000/docs`)

**Endpoints to Test**:

#### POST `/api/voice/chat`

**Request**:
- `audio`: Audio file (WebM format)
- `session_id`: Optional session ID

**Response**:
- `audio`: MP3 audio response
- Headers:
  - `X-Transcribed-Text`: User's transcribed text
  - `X-AI-Response`: AI's response text
  - `X-Sources`: Base64-encoded JSON sources
  - `X-Session-Id`: Session ID

**Test**:
1. Record audio using browser or upload file
2. Send POST request
3. Verify response headers contain sources
4. Check audio playback

#### GET `/api/trip/session/{session_id}`

**Request**:
- `session_id`: Session ID from voice chat

**Response**:
- `itinerary`: Structured itinerary object
- `sources`: List of sources

**Test**:
1. Get session ID from voice chat
2. Call GET endpoint
3. Verify itinerary structure
4. Verify sources are present

---

### 4. Tool Functionality Testing

**Purpose**: Test individual tools in isolation.

#### Test POI Search

```python
from tools.poi_search import search_pois_handler

result = search_pois_handler(
    interests=["history", "architecture"],
    constraints={"budget": "mid-range", "pace": "moderate"},
    max_results=10
)

print(f"Found {len(result)} POIs")
for poi in result[:3]:
    print(f"- {poi['name']}: {poi['category']}")
```

#### Test Itinerary Builder

```python
from tools.itinerary_builder import build_itinerary_handler

# First get POIs
pois = search_pois_handler(interests=["culture"], max_results=10)

# Build itinerary
itinerary = build_itinerary_handler(
    candidate_pois=pois,
    duration_days=2,
    pace="moderate"
)

print(f"Days: {len(itinerary['days'])}")
for day in itinerary['days']:
    print(f"Day {day['day']}: {len(day['activities'])} activities")
```

#### Test RAG Retrieval

```python
from tools.rag_retrieval import retrieve_city_guidance_handler

result = retrieve_city_guidance_handler(
    query="Why is Hawa Mahal a recommended tourist destination?",
    top_k=3
)

print(f"Retrieved {len(result)} chunks")
for chunk in result:
    print(f"- Source: {chunk['source']}, URL: {chunk['url']}")
```

---

### 5. Performance Testing

**Purpose**: Measure response times and system performance.

**Metrics to Track**:
- **STT Time**: Time to transcribe audio
- **LLM Time**: Time for LLM to generate response
- **Tool Execution Time**: Time for tools to execute
- **TTS Time**: Time to generate audio
- **Total Response Time**: End-to-end latency

**Test Script** (create `backend/test_performance.py`):

```python
import time
from api.routes.voice import voice_chat

start = time.time()

# Test voice chat
response = voice_chat(audio_file, session_id)

end = time.time()
print(f"Total time: {end - start:.2f}s")
```

**Target Performance**:
- STT: < 3 seconds
- LLM + Tools: < 10 seconds
- TTS: < 5 seconds
- **Total**: < 20 seconds

---

### 6. Quality Evaluation

**Purpose**: Assess response quality and accuracy.

**Evaluation Criteria**:

1. **Accuracy**: Information is factually correct
2. **Relevance**: Responses match user intent
3. **Completeness**: All requested information is provided
4. **Source Attribution**: Sources are cited correctly
5. **Formatting**: Responses are well-formatted

**Manual Evaluation**:

Use sample transcripts (see [SAMPLE_TRANSCRIPTS.md](SAMPLE_TRANSCRIPTS.md)) and rate:
- ✅ Excellent
- ✓ Good
- ⚠️ Needs improvement
- ❌ Poor

**Automated Checks**:
- Sources are present for factual questions
- Itinerary structure is correct (days, time periods)
- POI data includes required fields
- No placeholder text in responses

---

### 7. Error Handling Testing

**Purpose**: Verify system handles errors gracefully.

**Test Cases**:

1. **Invalid API Keys**:
   - Remove API keys from `.env`
   - Verify error messages are clear
   - Check fallback to next provider works

2. **Network Errors**:
   - Disconnect internet
   - Verify graceful error handling
   - Check user-friendly error messages

3. **Invalid Input**:
   - Send malformed audio
   - Send empty requests
   - Verify validation errors

4. **Rate Limiting**:
   - Exceed API rate limits
   - Verify retry logic works
   - Check error messages

---

### 8. Integration Testing

**Purpose**: Test full system integration.

**Test Flow**:

1. **Start Services**:
   - Backend server
   - Frontend dev server
   - Verify both are running

2. **Complete User Journey**:
   - Open frontend
   - Record voice message
   - Receive response
   - View itinerary
   - Check sources
   - Modify itinerary
   - Verify changes appear

3. **Session Persistence**:
   - Make multiple requests
   - Verify session maintains context
   - Check itinerary updates correctly

---

## Running All Evaluations

**Quick Test Suite**:

```bash
# 1. Source generation
cd backend
python test_sources.py

# 2. Manual testing (in browser)
# Open http://localhost:5173 and test voice chat

# 3. API testing
# Open http://localhost:8000/docs and test endpoints
```

**Full Evaluation Checklist**:

- [ ] Source generation test passes
- [ ] Voice chat works end-to-end
- [ ] API endpoints respond correctly
- [ ] Tools execute successfully
- [ ] Performance is acceptable (< 20s total)
- [ ] Quality is good (accurate, relevant)
- [ ] Error handling works
- [ ] Integration is smooth

---

## Debugging Failed Tests

### Sources Not Generated

**Check**:
1. RAG data is ingested: `python -m rag.ingest_pipeline`
2. ChromaDB exists: `backend/data/chroma_db/`
3. Session manager stores sources correctly
4. Backend logs show source generation

**Fix**:
- Re-run RAG ingestion
- Check API keys are valid
- Verify tool handlers are registered

### LLM Errors

**Check**:
1. API keys are correct in `.env`
2. Provider is available (Cerebras/Groq/Gemini)
3. Rate limits not exceeded
4. Network connectivity

**Fix**:
- Verify API keys
- Check provider status
- Wait for rate limit reset
- Try fallback provider

### Audio Issues

**Check**:
1. ffmpeg is installed and in PATH
2. Audio format is supported (WebM)
3. STT/TTS API keys are valid
4. Audio files are not corrupted

**Fix**:
- Install ffmpeg: https://ffmpeg.org/download.html
- Check audio format
- Verify API keys
- Test with sample audio file

---

## Continuous Evaluation

**Recommended**:
- Run source tests before each deployment
- Manual testing for major features
- Performance monitoring in production
- User feedback collection

**Automation**:
- Add tests to CI/CD pipeline
- Automated quality checks
- Performance regression tests

---

## See Also

- [SAMPLE_TRANSCRIPTS.md](SAMPLE_TRANSCRIPTS.md) - Test cases
- [TOOLS.md](TOOLS.md) - Tool documentation
- [README.md](README.md) - System setup


