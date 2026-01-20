# Deployment Options for Voice Travel Planner

This document compares different platforms that can deploy both your React frontend and FastAPI backend together.

## 🎯 Recommended: Platforms That Deploy Both Together

### Option 1: Railway (⭐ Recommended)

**Pros:**
- Deploys both frontend and backend in one project
- Automatic HTTPS
- Simple configuration
- Good free tier
- Supports Python and Node.js

**Setup:**
1. Sign up at [Railway](https://railway.app)
2. Create new project from GitHub
3. Add two services:
   - **Backend Service**: 
     - Root: `backend/`
     - Build: `pip install -r requirements.txt`
     - Start: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Frontend Service**:
     - Root: `voice-frontend/`
     - Build: `npm install && npm run build`
     - Start: `npm run preview` or use static file serving

**Environment Variables:**
- Set in Railway dashboard for backend service
- Frontend can access backend via internal Railway network

**Cost:** Free tier available, then ~$5/month

---

### Option 2: Render

**Pros:**
- Free tier for both web services and static sites
- Easy GitHub integration
- Automatic SSL

**Setup:**
1. Sign up at [Render](https://render.com)
2. Create two services:

   **Backend (Web Service):**
   - Build Command: `cd backend && pip install -r requirements.txt`
   - Start Command: `cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT`
   - Environment: Python 3.12

   **Frontend (Static Site):**
   - Build Command: `cd voice-frontend && npm install && npm run build`
   - Publish Directory: `voice-frontend/dist`

**Environment Variables:**
- Set in Render dashboard
- Frontend uses backend URL from Render

**Cost:** Free tier available (with limitations), then ~$7/month per service

---

### Option 3: Fly.io

**Pros:**
- Deploy both as separate apps
- Global edge network
- Good performance

**Setup:**
1. Install Fly CLI: `curl -L https://fly.io/install.sh | sh`
2. Create two apps:
   - Backend: `fly launch` in `backend/`
   - Frontend: `fly launch` in `voice-frontend/`

**Cost:** Free tier, then pay-as-you-go

---

### Option 4: Docker + Any Platform

**Pros:**
- Most flexible
- Works on any platform (AWS, GCP, Azure, DigitalOcean, etc.)

**Setup:**
Create `Dockerfile` for each service, then deploy containers.

**Cost:** Varies by platform

---

## 🔄 Current Setup: Separate Deployment

### Frontend: Vercel
- ✅ Already configured
- ✅ Great for React apps
- ✅ Free tier
- ❌ Can't deploy backend

### Backend: Needs Separate Platform
- Railway (recommended)
- Render
- Fly.io
- Heroku
- DigitalOcean App Platform

---

## 📋 Quick Comparison

| Platform | Deploy Both? | Free Tier | Ease of Setup | Best For |
|----------|--------------|-----------|---------------|----------|
| **Railway** | ✅ Yes | ✅ Yes | ⭐⭐⭐⭐⭐ | Best overall |
| **Render** | ✅ Yes | ✅ Yes | ⭐⭐⭐⭐ | Good free option |
| **Fly.io** | ✅ Yes | ✅ Yes | ⭐⭐⭐ | Performance-focused |
| **Vercel + Railway** | ⚠️ Separate | ✅ Yes | ⭐⭐⭐⭐ | Current setup |
| **Streamlit** | ❌ No | N/A | N/A | Not applicable |

---

## 🚀 Recommended Approach

**For simplicity:** Use **Railway** to deploy both together
- One project, two services
- Shared environment variables
- Internal networking between services

**For current setup:** Keep **Vercel for frontend** + **Railway for backend**
- Already have Vercel configured
- Just need to deploy backend separately
- Set `VITE_API_BASE_URL` in Vercel to point to Railway backend

---

## 📝 Railway Setup Guide

### Step 1: Deploy Backend

1. Go to [Railway Dashboard](https://railway.app/dashboard)
2. Click "New Project" → "Deploy from GitHub repo"
3. Select your repository
4. Railway will detect Python
5. Set **Root Directory** to: `backend`
6. Add environment variables:
   ```
   CEREBRAS_API_KEY=your_key
   ASSEMBLYAI_API_KEY=your_key
   ELEVENLABS_API_KEY=your_key
   CORS_ORIGINS=https://your-vercel-app.vercel.app
   ```
7. Railway will auto-generate a URL like: `https://your-backend.railway.app`

### Step 2: Deploy Frontend (Option A: Railway)

1. In same Railway project, click "New Service"
2. Select "GitHub Repo" (same repo)
3. Set **Root Directory** to: `voice-frontend`
4. Add environment variable:
   ```
   VITE_API_BASE_URL=https://your-backend.railway.app
   ```
5. Railway will serve the built frontend

### Step 2: Deploy Frontend (Option B: Keep Vercel)

1. In Vercel project settings, add environment variable:
   ```
   VITE_API_BASE_URL=https://your-backend.railway.app
   ```
2. Redeploy on Vercel
3. Frontend will now connect to Railway backend

---

## ⚠️ Important Notes

1. **ChromaDB**: Your vector database is stored locally. For production, consider:
   - Using Railway's persistent volumes
   - Or migrating to a cloud vector DB (Pinecone, Weaviate, etc.)

2. **CORS**: Make sure backend `CORS_ORIGINS` includes your frontend URL

3. **Environment Variables**: Never commit `.env` files. Use platform's env var settings.

4. **ffmpeg**: If your backend needs ffmpeg for audio conversion, ensure it's available in the deployment environment (Railway includes it by default).

---

## 🎯 My Recommendation

**Start with Railway for both services:**
- Simplest setup
- One platform to manage
- Internal networking
- Good documentation

**Or keep current setup:**
- Vercel for frontend (already working)
- Railway for backend (easy to set up)
- Just configure the API URL

Both approaches work well. Choose based on your preference for managing one vs. two platforms.

