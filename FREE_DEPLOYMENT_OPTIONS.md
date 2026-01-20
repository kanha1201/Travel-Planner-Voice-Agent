# Free Deployment Platforms Comparison

This guide compares **free** deployment platforms for your Voice Travel Planner (React frontend + FastAPI backend).

## 🆓 Free Tier Comparison

| Platform | Free Tier | Frontend | Backend | Both Together | Best For |
|----------|-----------|----------|---------|---------------|----------|
| **Render** | ✅ Generous | ✅ Static Site | ✅ Web Service | ✅ Yes | Best free option |
| **Railway** | ✅ $5 credit/month | ✅ Yes | ✅ Yes | ✅ Yes | Easiest setup |
| **Fly.io** | ✅ 3 VMs free | ✅ Yes | ✅ Yes | ✅ Yes | Global edge network |
| **Vercel + Render** | ✅ Both free | ✅ Vercel | ✅ Render | ⚠️ Separate | Current setup |
| **Netlify + Render** | ✅ Both free | ✅ Netlify | ✅ Render | ⚠️ Separate | Static + API |
| **PythonAnywhere** | ✅ Free tier | ❌ No | ✅ Yes | ❌ No | Backend only |
| **Heroku** | ❌ No free tier | ✅ Yes | ✅ Yes | ✅ Yes | (Paid only now) |
| **Replit** | ✅ Free tier | ✅ Yes | ✅ Yes | ✅ Yes | Browser-based IDE |

---

## 🏆 Top Recommendations

### 1. Render (⭐ Best Free Option)

**Free Tier:**
- ✅ Static Sites: Unlimited (free forever)
- ✅ Web Services: 750 hours/month (enough for 24/7)
- ✅ 512 MB RAM per service
- ✅ Automatic SSL
- ✅ Custom domains

**Setup:**
- **Frontend**: Deploy as Static Site
- **Backend**: Deploy as Web Service
- Both can be in same account, different services

**Pros:**
- Most generous free tier
- Easy GitHub integration
- Automatic deployments
- Good documentation

**Cons:**
- Services sleep after 15 min inactivity (free tier)
- First request after sleep takes ~30 seconds

**Best For:** Production-ready free deployments

---

### 2. Railway

**Free Tier:**
- ✅ $5 credit/month (usually enough for small apps)
- ✅ 500 hours compute time
- ✅ 5 GB storage
- ✅ Automatic SSL

**Setup:**
- Deploy both frontend and backend in one project
- Two services, shared networking

**Pros:**
- Simplest setup
- Internal networking between services
- No sleep/wake delays
- Great developer experience

**Cons:**
- Credit-based (may need to pay after free tier)
- Less generous than Render for free tier

**Best For:** Quick deployments, development

---

### 3. Fly.io

**Free Tier:**
- ✅ 3 shared-cpu VMs (256 MB each)
- ✅ 3 GB persistent storage
- ✅ 160 GB outbound data transfer
- ✅ Global edge network

**Setup:**
- Deploy frontend and backend as separate apps
- Use Fly CLI or GitHub integration

**Pros:**
- Global edge network (fast worldwide)
- No sleep/wake delays
- Good for production
- Docker-based (flexible)

**Cons:**
- More complex setup (CLI required)
- Learning curve

**Best For:** Production apps needing global performance

---

### 4. Vercel + Render (Current Setup)

**Free Tier:**
- ✅ Vercel: Unlimited for frontend
- ✅ Render: 750 hours/month for backend
- ✅ Both free forever

**Setup:**
- Frontend on Vercel (already configured)
- Backend on Render (separate service)

**Pros:**
- Best-in-class frontend hosting (Vercel)
- Generous backend hosting (Render)
- Already have Vercel set up

**Cons:**
- Two platforms to manage
- Need to configure CORS

**Best For:** Keeping current setup, optimizing each service

---

### 5. Replit

**Free Tier:**
- ✅ Always-on Repls (limited)
- ✅ 500 MB RAM
- ✅ 10 GB storage
- ✅ Browser-based IDE

**Setup:**
- Deploy both in one Repl or separate Repls
- Can use Replit's built-in deployment

**Pros:**
- Code and deploy in browser
- No local setup needed
- Good for learning/experimentation

**Cons:**
- Less suitable for production
- Resource limits
- Can be slow

**Best For:** Learning, quick prototypes

---

## 📋 Detailed Setup Guides

### Option A: Render (Recommended for Free)

#### Backend Setup on Render

1. **Sign up** at [render.com](https://render.com)
2. **New** → **Web Service**
3. **Connect GitHub** → Select your repo
4. **Configure:**
   - **Name**: `travel-planner-backend`
   - **Environment**: `Python 3`
   - **Build Command**: `cd backend && pip install -r requirements.txt`
   - **Start Command**: `cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Root Directory**: `backend` (leave empty, Render uses build/start commands)
5. **Environment Variables:**
   ```
   CEREBRAS_API_KEY=your_key
   ASSEMBLYAI_API_KEY=your_key
   ELEVENLABS_API_KEY=your_key
   CORS_ORIGINS=https://your-frontend.onrender.com
   PORT=10000
   ```
6. **Plan**: Select **Free**
7. **Deploy**

#### Frontend Setup on Render

1. **New** → **Static Site**
2. **Connect GitHub** → Select your repo
3. **Configure:**
   - **Name**: `travel-planner-frontend`
   - **Build Command**: `cd voice-frontend && npm install && npm run build`
   - **Publish Directory**: `voice-frontend/dist`
4. **Environment Variables:**
   ```
   VITE_API_BASE_URL=https://travel-planner-backend.onrender.com
   ```
5. **Deploy**

**Note:** Free tier services sleep after 15 min. First request wakes them up (~30 sec delay).

---

### Option B: Fly.io

#### Prerequisites
```bash
# Install Fly CLI
curl -L https://fly.io/install.sh | sh
```

#### Backend Setup

1. **Login:**
   ```bash
   fly auth login
   ```

2. **Create app:**
   ```bash
   cd backend
   fly launch
   ```
   - Select app name
   - Select region
   - Don't deploy yet

3. **Create `fly.toml`** (auto-generated, edit if needed):
   ```toml
   app = "your-backend-app-name"
   primary_region = "iad"  # Choose closest region
   
   [build]
   
   [http_service]
     internal_port = 8000
     force_https = true
     auto_stop_machines = false
     auto_start_machines = true
     min_machines_running = 0
   
   [[services]]
     protocol = "tcp"
     internal_port = 8000
   ```

4. **Set secrets:**
   ```bash
   fly secrets set CEREBRAS_API_KEY=your_key
   fly secrets set ASSEMBLYAI_API_KEY=your_key
   fly secrets set ELEVENLABS_API_KEY=your_key
   fly secrets set CORS_ORIGINS=https://your-frontend.fly.dev
   ```

5. **Deploy:**
   ```bash
   fly deploy
   ```

#### Frontend Setup

1. **Create app:**
   ```bash
   cd voice-frontend
   fly launch
   ```

2. **Create `Dockerfile`** in `voice-frontend/`:
   ```dockerfile
   FROM node:18-alpine AS builder
   WORKDIR /app
   COPY package*.json ./
   RUN npm install
   COPY . .
   RUN npm run build
   
   FROM nginx:alpine
   COPY --from=builder /app/dist /usr/share/nginx/html
   COPY nginx.conf /etc/nginx/conf.d/default.conf
   EXPOSE 80
   CMD ["nginx", "-g", "daemon off;"]
   ```

3. **Create `nginx.conf`**:
   ```nginx
   server {
       listen 80;
       server_name _;
       root /usr/share/nginx/html;
       index index.html;
       
       location / {
           try_files $uri $uri/ /index.html;
       }
   }
   ```

4. **Deploy:**
   ```bash
   fly deploy
   ```

---

### Option C: Netlify + Render

#### Frontend on Netlify

1. **Sign up** at [netlify.com](https://netlify.com)
2. **Add new site** → **Import from Git**
3. **Configure:**
   - **Base directory**: `voice-frontend`
   - **Build command**: `npm install && npm run build`
   - **Publish directory**: `voice-frontend/dist`
4. **Environment Variables:**
   ```
   VITE_API_BASE_URL=https://your-backend.onrender.com
   ```
5. **Deploy**

#### Backend on Render

Follow "Backend Setup on Render" from Option A above.

---

## 💰 Cost Breakdown (After Free Tier)

| Platform | After Free Tier | Monthly Cost |
|----------|----------------|--------------|
| **Render** | $7/service | ~$14/month (both) |
| **Railway** | $5/month | $5/month |
| **Fly.io** | Pay-as-you-go | ~$2-5/month (small apps) |
| **Vercel** | Free forever | $0 (frontend) |
| **Netlify** | Free forever | $0 (frontend) |

---

## 🎯 My Recommendations

### For Maximum Free Tier:
**Render** (both frontend and backend)
- Most generous free tier
- 750 hours/month (enough for 24/7)
- Easy setup

### For Easiest Setup:
**Railway** (both together)
- Simplest configuration
- One project, two services
- $5 credit/month usually enough

### For Best Performance:
**Vercel (frontend) + Render (backend)**
- Best frontend hosting (Vercel)
- Generous backend (Render)
- Already have Vercel configured

### For Production:
**Fly.io** (both)
- Global edge network
- No sleep delays
- Best performance worldwide

---

## ⚠️ Free Tier Limitations

### Render Free Tier:
- Services sleep after 15 min inactivity
- ~30 second wake-up time
- 512 MB RAM limit

### Railway Free Tier:
- $5 credit/month (may run out)
- Need to monitor usage

### Fly.io Free Tier:
- 3 VMs only
- 256 MB RAM per VM
- May need to upgrade for production

---

## 🚀 Quick Start: Render (Recommended)

**Fastest way to deploy both for free:**

1. **Backend:**
   - Render → New Web Service
   - Connect GitHub repo
   - Build: `cd backend && pip install -r requirements.txt`
   - Start: `cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT`
   - Add environment variables
   - Deploy

2. **Frontend:**
   - Render → New Static Site
   - Connect GitHub repo
   - Build: `cd voice-frontend && npm install && npm run build`
   - Publish: `voice-frontend/dist`
   - Add `VITE_API_BASE_URL` pointing to backend
   - Deploy

**Total time: ~15 minutes**
**Cost: $0/month (free tier)**

---

## 📚 Additional Resources

- **Render Docs**: https://render.com/docs
- **Railway Docs**: https://docs.railway.app
- **Fly.io Docs**: https://fly.io/docs
- **Vercel Docs**: https://vercel.com/docs
- **Netlify Docs**: https://docs.netlify.com

---

## ❓ Which Should You Choose?

**Choose Render if:**
- You want the most generous free tier
- You don't mind 15-min sleep delays
- You want simple setup

**Choose Railway if:**
- You want the easiest setup
- You want both services in one place
- $5/month is acceptable after free tier

**Choose Fly.io if:**
- You need global performance
- You want no sleep delays
- You're comfortable with CLI

**Keep Vercel + Render if:**
- You already have Vercel working
- You want best-in-class frontend hosting
- You're okay managing two platforms

