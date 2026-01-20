# Vercel Deployment Guide

This guide explains how to deploy the Voice Travel Planner frontend to Vercel.

## Prerequisites

1. A GitHub account with the repository pushed
2. A Vercel account (sign up at https://vercel.com)
3. A deployed backend API (see Backend Deployment section)

## Frontend Deployment Steps

### 1. Connect Repository to Vercel

1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Click "Add New Project"
3. Import your GitHub repository: `kanha1201/Travel-Planner-Voice-Agent`
4. Vercel will automatically detect the `vercel.json` configuration

### 2. Configure Build Settings

The `vercel.json` file is already configured with:
- **Build Command**: `cd voice-frontend && npm install && npm run build`
- **Output Directory**: `voice-frontend/dist`
- **Framework**: Vite

Vercel should automatically detect these settings. Verify in the project settings.

### 3. Set Environment Variables

In your Vercel project settings, add the following environment variable:

**Variable Name**: `VITE_API_BASE_URL`  
**Value**: Your backend API URL (e.g., `https://your-backend.railway.app`)

**Important**: 
- Do NOT include `/api` in the URL - the frontend code appends `/api` automatically
- If you leave this empty, the frontend will use `/api` (which will only work if you set up API rewrites)

### 4. Deploy

1. Click "Deploy" in Vercel
2. Wait for the build to complete
3. Your frontend will be available at `https://your-project.vercel.app`

## Backend Deployment

The FastAPI backend needs to be deployed separately. Recommended platforms:

### Option 1: Railway (Recommended)

1. Sign up at [Railway](https://railway.app)
2. Create a new project from GitHub
3. Select your repository
4. Railway will auto-detect Python
5. Set environment variables in Railway dashboard:
   - `CEREBRAS_API_KEY`
   - `ASSEMBLAS_API_KEY`
   - `ELEVENLABS_API_KEY`
   - `CORS_ORIGINS` (set to your Vercel frontend URL)
6. Deploy

### Option 2: Render

1. Sign up at [Render](https://render.com)
2. Create a new Web Service
3. Connect your GitHub repository
4. Set build command: `cd backend && pip install -r requirements.txt`
5. Set start command: `cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT`
6. Add environment variables
7. Deploy

### Option 3: Vercel Serverless Functions

For advanced users, you can convert the FastAPI backend to Vercel serverless functions. This requires significant refactoring.

## API Rewrites (Optional)

If you want to proxy API calls through Vercel instead of using CORS, you can update `vercel.json`:

```json
{
  "rewrites": [
    {
      "source": "/api/(.*)",
      "destination": "https://your-backend-url.railway.app/api/$1"
    },
    {
      "source": "/(.*)",
      "destination": "/index.html"
    }
  ]
}
```

Then set `VITE_API_BASE_URL` to empty string (or remove it) so the frontend uses `/api`.

## Troubleshooting

### 404 Error After Deployment

1. **Check Build Logs**: Ensure the build completed successfully
2. **Verify Output Directory**: Should be `voice-frontend/dist`
3. **Check Routing**: The `vercel.json` should have a rewrite rule for `/(.*)` → `/index.html`

### API Calls Failing

1. **Check CORS**: Ensure your backend has `CORS_ORIGINS` set to include your Vercel URL
2. **Verify API URL**: Check that `VITE_API_BASE_URL` is set correctly in Vercel
3. **Check Network Tab**: Look for CORS errors or 404s in browser console

### Build Fails

1. **Check Node Version**: Vercel should auto-detect, but ensure Node.js 18+ is used
2. **Check Dependencies**: Ensure `package.json` in `voice-frontend` is correct
3. **Check Build Command**: Verify the build command works locally

## Environment Variables Reference

### Frontend (Vercel)
- `VITE_API_BASE_URL`: Backend API base URL (without `/api` suffix)

### Backend (Railway/Render)
- `CEREBRAS_API_KEY`: Cerebras API key
- `ASSEMBLYAI_API_KEY`: AssemblyAI API key for STT
- `ELEVENLABS_API_KEY`: ElevenLabs API key for TTS
- `CORS_ORIGINS`: Comma-separated list of allowed origins (include your Vercel URL)
- `LOG_LEVEL`: Logging level (default: `INFO`)

## Next Steps

After deployment:
1. Test the voice chat functionality
2. Verify API connectivity
3. Check browser console for any errors
4. Monitor Vercel and backend logs for issues

