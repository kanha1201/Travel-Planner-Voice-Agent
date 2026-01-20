# Render Deployment Troubleshooting Guide

## Common Issues and Solutions

### 500 Internal Server Error

If you're seeing a 500 error when using the voice chat, follow these steps:

#### 1. Check Backend Logs in Render Dashboard

1. Go to your Render dashboard
2. Click on your backend service
3. Go to the "Logs" tab
4. Look for error messages, especially:
   - API key errors
   - Import errors
   - Initialization failures

#### 2. Verify Environment Variables

Make sure all required environment variables are set in Render:

**Required for Backend:**
- `CEREBRAS_API_KEY` or `GROQ_API_KEY` or `GEMINI_API_KEY` (at least one LLM provider)
- `ASSEMBLYAI_API_KEY` (if using AssemblyAI for STT)
- `ELEVENLABS_API_KEY` (if using ElevenLabs for STT or TTS)
- `CORS_ORIGINS` (should include your frontend URL)

**Required for Frontend:**
- `VITE_API_BASE_URL` (should be your backend URL without `/api`)

#### 3. Use the Health Check Endpoint

Test the health check endpoint to see which services are failing:

```bash
curl https://your-backend-url.onrender.com/api/voice/health
```

This will show you:
- STT service status
- TTS service status
- Orchestrator/LLM service status

#### 4. Common Error Causes

**Missing API Keys:**
- Error: `CEREBRAS_API_KEY not found` or similar
- Solution: Add the API key in Render's environment variables

**ChromaDB Initialization:**
- Error: `Failed to initialize ChromaDB` or `chromadb` import errors
- Solution: ChromaDB should auto-initialize. If issues persist, check that all Python dependencies are installed

**CORS Errors:**
- Error: `CORS policy` errors in browser console
- Solution: Ensure `CORS_ORIGINS` includes your frontend URL (e.g., `https://your-frontend.onrender.com`)

**Module Import Errors:**
- Error: `ModuleNotFoundError: No module named 'X'`
- Solution: Check that `requirements.txt` includes all dependencies and Render successfully installed them

#### 5. Check Render Build Logs

1. Go to your backend service in Render
2. Check the "Events" tab for build errors
3. Look for:
   - Failed pip installs
   - Missing dependencies
   - Python version issues

#### 6. Test Individual Services

You can test each service individually:

**Test STT:**
```bash
curl -X POST https://your-backend-url.onrender.com/api/voice/transcribe \
  -F "audio=@test_audio.webm" \
  -F "language=en"
```

**Test TTS:**
```bash
curl -X POST https://your-backend-url.onrender.com/api/voice/synthesize \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello, this is a test", "voice": "default", "speed": 1.0}'
```

**Test LLM/Orchestrator:**
```bash
curl -X POST https://your-backend-url.onrender.com/api/trip/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Plan a trip to Jaipur", "session_id": null}'
```

### Frontend Can't Connect to Backend

**Symptoms:**
- "Failed to fetch" errors
- Network errors in browser console
- 404 or CORS errors

**Solutions:**

1. **Verify API URL:**
   - Check that `VITE_API_BASE_URL` is set correctly
   - Should be: `https://your-backend-url.onrender.com` (without `/api`)
   - Frontend will automatically append `/api` to the base URL

2. **Check CORS:**
   - Backend `CORS_ORIGINS` must include frontend URL
   - Format: `https://your-frontend.onrender.com` (no trailing slash)

3. **Verify Backend is Running:**
   - Check Render dashboard - backend should show "Live"
   - If "Sleeping", wake it up by making a request

### Service Goes to Sleep (Free Tier)

Render's free tier services sleep after 15 minutes of inactivity.

**Symptoms:**
- First request after sleep takes ~30 seconds
- Timeout errors

**Solutions:**
- Wait for the service to wake up (first request will be slow)
- Consider upgrading to paid tier for always-on service
- Use a service like UptimeRobot to ping your service periodically

### Debugging Tips

1. **Enable Debug Logging:**
   - Set `LOG_LEVEL=DEBUG` in backend environment variables
   - Check logs for detailed error messages

2. **Test Locally First:**
   - If possible, test the same configuration locally
   - This helps isolate Render-specific issues

3. **Check Browser Console:**
   - Open browser DevTools (F12)
   - Check Console and Network tabs
   - Look for specific error messages

4. **Verify File Paths:**
   - Ensure all file paths in code are relative
   - Render uses different directory structure than local

### Getting Help

If you're still experiencing issues:

1. Check Render's status page: https://status.render.com
2. Review Render's documentation: https://render.com/docs
3. Check backend logs for specific error messages
4. Use the health check endpoint to identify which service is failing

