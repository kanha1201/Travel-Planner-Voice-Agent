# Voice Agent Frontend Setup Guide

## Quick Start

1. **Install Dependencies**
   ```bash
   cd voice-frontend
   npm install
   ```

2. **Start Development Server**
   ```bash
   npm run dev
   ```

3. **Access the App**
   - Open `http://localhost:3001` in your browser
   - Grant microphone permissions when prompted

## Port Configuration

- **Voice Agent**: Port 3001 (this app)
- **Chat Agent**: Port 3000 (existing frontend)
- **Backend**: Port 8000

## Features

### Voice Chat Tab
- Tap the microphone button to start recording
- Speak your travel planning request
- Tap again to stop and send
- AI response will be played as audio
- Transcript is displayed in real-time

### Plan Tab
- View your generated itinerary
- Switch between days using day tabs
- See activities organized by morning/afternoon/evening
- View travel times between activities

## Backend Integration

The app connects to the backend at `http://localhost:8000` via the proxy configured in `vite.config.ts`.

### Required Backend Endpoints
- `POST /api/voice/chat` - Voice chat endpoint
- `GET /api/trip/session/{sessionId}` - Get itinerary data

### Backend Requirements
- Backend must be running on port 8000
- API keys for ElevenLabs (STT) and AssemblyAI (TTS) must be configured
- See `backend/env.example` for required environment variables

## Troubleshooting

### Microphone Not Working
- Check browser permissions for microphone access
- Ensure you're using HTTPS or localhost (required for getUserMedia)
- Try a different browser if issues persist

### Audio Playback Issues
- Check browser audio settings
- Ensure audio isn't muted
- Check browser console for errors

### Backend Connection Issues
- Verify backend is running on port 8000
- Check CORS settings in backend
- Verify API keys are configured correctly

## Development

### Build for Production
```bash
npm run build
```

### Preview Production Build
```bash
npm run preview
```

## Project Structure

```
voice-frontend/
├── src/
│   ├── components/       # React components
│   │   ├── Header.tsx
│   │   ├── VoiceChatPage.tsx
│   │   ├── ItineraryFeed.tsx
│   │   └── ...
│   ├── utils/           # Utility functions
│   │   ├── voiceRecorder.ts
│   │   └── api.ts
│   ├── types.ts         # TypeScript types
│   ├── App.tsx          # Main app component
│   └── main.tsx         # Entry point
├── package.json
├── vite.config.ts       # Vite configuration (port 3001)
└── tailwind.config.js   # Tailwind CSS configuration
```







