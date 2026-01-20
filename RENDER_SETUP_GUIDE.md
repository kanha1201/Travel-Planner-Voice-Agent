# Render Deployment Setup Guide

Step-by-step configuration for deploying your Voice Travel Planner on Render.

## 🎯 Backend Service Configuration

### Step 1: Basic Configuration

**Source Code:**
- ✅ Already set: `kanha1201 / Travel-Planner-Voice-Agent`
- No changes needed

**Name:**
- ✅ Already set: `Travel-Planner-Voice-Agent`
- Or change to: `travel-planner-backend` (more descriptive)

**Language:**
- ✅ Already set: `Python 3`
- No changes needed

**Branch:**
- ✅ Already set: `main`
- No changes needed

**Region:**
- ✅ Already set: `Oregon (US West)`
- You can change to a region closer to you, but this is fine

---

### Step 2: Build & Start Commands

**Root Directory:**
```
backend
```
⚠️ **IMPORTANT**: Set this to `backend` (without quotes, without slash). This tells Render to look in the `backend/` folder for your Python files.

**Build Command:**
```
cd backend && pip install -r requirements.txt
```
Or simply:
```
pip install -r requirements.txt
```
(Render will run this from the root directory, so you need `cd backend &&` or set Root Directory)

**Start Command:**
```
cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT
```
Or if Root Directory is set to `backend`:
```
uvicorn main:app --host 0.0.0.0 --port $PORT
```

**Instance Type:**
- ✅ Select **Free** (for now)
- You can upgrade later if needed

---

### Step 3: Environment Variables

Click **"Add Environment Variable"** and add each of these:

#### Required API Keys:

1. **CEREBRAS_API_KEY**
   - Value: `your_cerebras_api_key_here`
   - Replace with your actual Cerebras API key

2. **ASSEMBLYAI_API_KEY**
   - Value: `your_assemblyai_api_key_here`
   - Replace with your actual AssemblyAI API key

3. **ELEVENLABS_API_KEY**
   - Value: `your_elevenlabs_api_key_here`
   - Replace with your actual ElevenLabs API key

#### Application Configuration:

4. **CORS_ORIGINS**
   - Value: `https://your-frontend-url.onrender.com`
   - Replace with your frontend URL (you'll get this after deploying frontend)
   - For now, you can use: `https://travel-planner-frontend.onrender.com`
   - Or add multiple: `https://travel-planner-frontend.onrender.com,http://localhost:5173`

5. **LOG_LEVEL**
   - Value: `INFO`
   - Options: `DEBUG`, `INFO`, `WARNING`, `ERROR`

6. **ENVIRONMENT**
   - Value: `production`

#### Optional (with defaults):

7. **LLM_PROVIDER** (optional)
   - Value: `cerebras`
   - Options: `cerebras`, `groq`, `gemini`

8. **STT_PROVIDER** (optional)
   - Value: `assemblyai`
   - Options: `assemblyai`, `elevenlabs`

9. **TTS_PROVIDER** (optional)
   - Value: `elevenlabs`
   - Options: `elevenlabs`

10. **PORT** (optional - Render sets this automatically)
    - Value: `10000`
    - Or leave empty (Render provides `$PORT`)

---

### Step 4: Deploy

1. Click **"Deploy Web Service"** button at the bottom
2. Wait for build to complete (5-10 minutes first time)
3. Copy the generated URL (e.g., `https://travel-planner-backend.onrender.com`)

---

## 🎨 Frontend Service Configuration

After backend is deployed, create a new Static Site:

### Step 1: Create Static Site

1. In Render dashboard, click **"New +"** → **"Static Site"**
2. Connect your GitHub repository: `kanha1201/Travel-Planner-Voice-Agent`

### Step 2: Basic Configuration

**Name:**
```
travel-planner-frontend
```

**Branch:**
```
main
```

**Root Directory:**
```
voice-frontend
```
⚠️ **IMPORTANT**: Set this to `voice-frontend`

**Build Command:**
```
npm install && npm run build
```

**Publish Directory:**
```
dist
```

### Step 3: Environment Variables

Add one environment variable:

**VITE_API_BASE_URL**
- Value: `https://travel-planner-backend.onrender.com`
- Replace with your actual backend URL from Step 4 above
- ⚠️ **Important**: Do NOT include `/api` at the end - the frontend code adds it automatically

### Step 4: Deploy

1. Click **"Create Static Site"**
2. Wait for build to complete
3. Copy the frontend URL (e.g., `https://travel-planner-frontend.onrender.com`)

### Step 5: Update Backend CORS

1. Go back to your backend service
2. Update the `CORS_ORIGINS` environment variable:
   - Add your frontend URL: `https://travel-planner-frontend.onrender.com`
   - Or replace with: `https://travel-planner-frontend.onrender.com,http://localhost:5173`
3. Render will auto-redeploy

---

## 📋 Quick Reference: Exact Values to Copy

### Backend Service:

```
Root Directory: backend
Build Command: cd backend && pip install -r requirements.txt
Start Command: cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT
Instance Type: Free
```

**Environment Variables:**
```
CEREBRAS_API_KEY = your_actual_key
ASSEMBLYAI_API_KEY = your_actual_key
ELEVENLABS_API_KEY = your_actual_key
CORS_ORIGINS = https://travel-planner-frontend.onrender.com
LOG_LEVEL = INFO
ENVIRONMENT = production
```

### Frontend Service:

```
Root Directory: voice-frontend
Build Command: npm install && npm run build
Publish Directory: dist
```

**Environment Variables:**
```
VITE_API_BASE_URL = https://travel-planner-backend.onrender.com
```

---

## ⚠️ Common Mistakes to Avoid

1. **Root Directory**: 
   - ✅ Correct: `backend` or `voice-frontend`
   - ❌ Wrong: `/backend`, `./backend`, `backend/`

2. **Build Command**:
   - ✅ If Root Directory is set: `pip install -r requirements.txt`
   - ✅ If Root Directory is empty: `cd backend && pip install -r requirements.txt`

3. **Start Command**:
   - ✅ Must use `$PORT` (Render provides this)
   - ✅ Must use `0.0.0.0` as host (not `localhost`)

4. **CORS_ORIGINS**:
   - ✅ Include your frontend URL
   - ✅ No trailing slashes
   - ✅ Use `https://` (not `http://`)

5. **VITE_API_BASE_URL**:
   - ✅ Just the base URL: `https://travel-planner-backend.onrender.com`
   - ❌ Don't include `/api`: `https://travel-planner-backend.onrender.com/api`

---

## 🔍 Troubleshooting

### Backend won't start:
- Check Root Directory is set to `backend`
- Verify Start Command uses `$PORT` and `0.0.0.0`
- Check build logs for errors

### Frontend can't connect to backend:
- Verify `VITE_API_BASE_URL` is set correctly
- Check `CORS_ORIGINS` includes frontend URL
- Ensure backend is deployed and running

### Build fails:
- Check Root Directory is correct
- Verify Build Command paths are correct
- Check that `requirements.txt` exists in `backend/`

---

## 📝 Notes

- **Free tier limitation**: Services sleep after 15 minutes of inactivity
- **Wake time**: First request after sleep takes ~30 seconds
- **Auto-deploy**: Render auto-deploys on git push to main branch
- **Logs**: Check logs in Render dashboard if issues occur

