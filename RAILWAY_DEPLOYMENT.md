# Railway Deployment Guide - Deploy Both Frontend & Backend

This guide shows you how to deploy both your React frontend and FastAPI backend on Railway in one project.

## Prerequisites

1. GitHub account with your repository
2. Railway account (sign up at https://railway.app - free tier available)
3. API keys ready (Cerebras, AssemblyAI, ElevenLabs)

## Step-by-Step Deployment

### Step 1: Create Railway Project

1. Go to [Railway Dashboard](https://railway.app/dashboard)
2. Click **"New Project"**
3. Select **"Deploy from GitHub repo"**
4. Authorize Railway to access your GitHub
5. Select repository: `kanha1201/Travel-Planner-Voice-Agent`
6. Click **"Deploy Now"**

### Step 2: Deploy Backend Service

Railway will auto-detect Python and create a service. Configure it:

1. Click on the service (or create new service if needed)
2. Go to **Settings** tab
3. Set **Root Directory** to: `backend`
4. Go to **Variables** tab and add:

```
CEREBRAS_API_KEY=your_cerebras_key_here
ASSEMBLYAI_API_KEY=your_assemblyai_key_here
ELEVENLABS_API_KEY=your_elevenlabs_key_here
CORS_ORIGINS=https://your-frontend-url.railway.app
LOG_LEVEL=INFO
```

5. Go to **Settings** → **Deploy** section
6. Set **Start Command** to:
   ```
   uvicorn main:app --host 0.0.0.0 --port $PORT
   ```
7. Railway will auto-detect the build command (installs from `requirements.txt`)
8. Wait for deployment to complete
9. Copy the generated URL (e.g., `https://your-backend.railway.app`)

### Step 3: Deploy Frontend Service

1. In the same Railway project, click **"+ New"** → **"GitHub Repo"**
2. Select the same repository: `kanha1201/Travel-Planner-Voice-Agent`
3. Click **"Deploy Now"**
4. Go to **Settings** tab
5. Set **Root Directory** to: `voice-frontend`
6. Go to **Variables** tab and add:
   ```
   VITE_API_BASE_URL=https://your-backend.railway.app
   ```
   (Replace with your actual backend URL from Step 2)
7. Go to **Settings** → **Deploy** section
8. Set **Build Command** to:
   ```
   npm install && npm run build
   ```
9. Set **Start Command** to:
   ```
   npx serve -s dist -l $PORT
   ```
   Or use a static file server. You may need to add `serve` to `package.json`:
   ```json
   "scripts": {
     "serve": "serve -s dist -l $PORT"
   }
   ```
10. Wait for deployment to complete
11. Copy the frontend URL

### Step 4: Update CORS in Backend

1. Go back to backend service
2. Update `CORS_ORIGINS` variable to include your frontend URL:
   ```
   CORS_ORIGINS=https://your-frontend.railway.app
   ```
3. Redeploy backend (Railway will auto-redeploy)

### Step 5: Test Deployment

1. Visit your frontend URL
2. Test voice chat functionality
3. Check browser console for any errors
4. Check Railway logs if issues occur

## Alternative: Use Railway's Static File Serving

If the `serve` command doesn't work, Railway can serve static files:

1. In frontend service settings
2. Go to **Settings** → **Networking**
3. Enable **"Public Networking"**
4. Railway will serve files from the build output

Or create a simple Python server:

Create `voice-frontend/server.py`:
```python
from http.server import HTTPServer, SimpleHTTPRequestHandler
import os

class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory='dist', **kwargs)

port = int(os.environ.get('PORT', 3000))
server = HTTPServer(('0.0.0.0', port), Handler)
server.serve_forever()
```

Then set start command to: `python server.py`

## Troubleshooting

### Backend Issues

**Port Error:**
- Make sure start command uses `$PORT` environment variable
- Railway provides this automatically

**Module Not Found:**
- Check `requirements.txt` includes all dependencies
- Check Railway build logs

**ChromaDB Issues:**
- ChromaDB data is stored locally. For production, consider:
  - Using Railway's persistent volumes
  - Or migrating to cloud vector DB

### Frontend Issues

**404 on Routes:**
- Ensure static file server is configured correctly
- Check that `dist` folder is being served

**API Connection Failed:**
- Verify `VITE_API_BASE_URL` is set correctly
- Check CORS settings in backend
- Ensure backend URL is accessible

**Build Fails:**
- Check Node.js version (Railway auto-detects)
- Verify `package.json` is correct
- Check build logs for specific errors

## Environment Variables Reference

### Backend Service
```
CEREBRAS_API_KEY=your_key
ASSEMBLYAI_API_KEY=your_key
ELEVENLABS_API_KEY=your_key
CORS_ORIGINS=https://your-frontend.railway.app
LOG_LEVEL=INFO
BACKEND_HOST=0.0.0.0
BACKEND_PORT=$PORT
```

### Frontend Service
```
VITE_API_BASE_URL=https://your-backend.railway.app
```

## Cost

- **Free Tier**: $5 credit/month (usually enough for small projects)
- **Hobby Plan**: $5/month (if you exceed free tier)
- **Pro Plan**: $20/month (for production)

## Next Steps

1. Set up custom domains (optional)
2. Configure monitoring and alerts
3. Set up CI/CD for automatic deployments
4. Consider migrating ChromaDB to cloud solution for production

## Support

- Railway Docs: https://docs.railway.app
- Railway Discord: https://discord.gg/railway

