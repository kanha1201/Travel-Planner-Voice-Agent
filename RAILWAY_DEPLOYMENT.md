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

**CRITICAL: Configure Root Directory FIRST before Railway tries to build!**

1. After creating the project, Railway will start building automatically
2. **STOP the deployment** if it's running (click the service → Settings → Delete/Stop)
3. Click on the service (or create new service if needed)
4. Go to **Settings** tab
5. **IMPORTANT**: Set **Root Directory** to: `backend`
   - This tells Railway to look in the `backend/` folder for Python files
   - Without this, Railway looks at repo root and can't detect Python
6. Go to **Settings** → **Deploy** section
7. Set **Start Command** to:
   ```
   uvicorn main:app --host 0.0.0.0 --port $PORT
   ```
   - Railway should auto-detect build from `requirements.txt` and `nixpacks.toml`
8. Go to **Variables** tab and add:

```
CEREBRAS_API_KEY=your_cerebras_key_here
ASSEMBLYAI_API_KEY=your_assemblyai_key_here
ELEVENLABS_API_KEY=your_elevenlabs_key_here
CORS_ORIGINS=https://your-frontend-url.railway.app
LOG_LEVEL=INFO
```

9. Click **"Redeploy"** or wait for automatic redeploy
10. Wait for deployment to complete
11. Copy the generated URL (e.g., `https://your-backend.railway.app`)

**If you see "Railpack could not determine how to build the app":**
- Make sure **Root Directory** is set to `backend` (not empty!)
- The `backend/` folder contains `requirements.txt` and `main.py`
- Check that `nixpacks.toml` and `Procfile` exist in `backend/` folder

### Step 3: Deploy Frontend Service

1. In the same Railway project, click **"+ New"** → **"GitHub Repo"**
2. Select the same repository: `kanha1201/Travel-Planner-Voice-Agent`
3. Click **"Deploy Now"**
4. **IMPORTANT**: Go to **Settings** tab immediately
5. Set **Root Directory** to: `voice-frontend`
   - This tells Railway to look in `voice-frontend/` for Node.js files
   - Without this, Railway can't find `package.json`
6. Go to **Settings** → **Deploy** section
7. Set **Build Command** to:
   ```
   npm install && npm run build
   ```
8. Set **Start Command** to:
   ```
   npm run serve
   ```
   (The `serve` script is already added to `package.json`)
9. Go to **Variables** tab and add:
   ```
   VITE_API_BASE_URL=https://your-backend.railway.app
   ```
   (Replace with your actual backend URL from Step 2)
10. Railway will automatically redeploy with new settings
11. Wait for deployment to complete
12. Copy the frontend URL

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

**"Railpack could not determine how to build the app" Error:**
- ✅ **Solution**: Set **Root Directory** to `backend` in service settings
- ✅ Make sure `backend/requirements.txt` exists
- ✅ Make sure `backend/main.py` exists
- ✅ The `nixpacks.toml` and `Procfile` files help Railway detect Python
- ❌ Don't leave Root Directory empty - Railway will look at repo root

**Port Error:**
- Make sure start command uses `$PORT` environment variable
- Railway provides this automatically

**Module Not Found:**
- Check `requirements.txt` includes all dependencies
- Check Railway build logs
- Verify Python version (should be 3.12 based on `runtime.txt`)

**ChromaDB Issues:**
- ChromaDB data is stored locally. For production, consider:
  - Using Railway's persistent volumes
  - Or migrating to cloud vector DB

**Build Fails:**
- Check that Root Directory is set correctly
- Verify all files exist in the backend directory
- Check build logs for specific error messages

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

