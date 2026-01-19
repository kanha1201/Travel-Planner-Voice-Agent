# Voice Travel Planner - Voice Agent Frontend

Voice-based UI for the Jaipur Travel Planner, running on port 3001.

## Features

- 🎤 Voice input using browser microphone
- 🔊 Audio output for AI responses
- 📱 Mobile-responsive design
- 📅 Itinerary visualization
- 🔄 Real-time conversation with backend

## Setup

1. Install dependencies:
```bash
npm install
```

2. Start the development server:
```bash
npm run dev
```

The app will run on `http://localhost:3001`

## Architecture

- **Port**: 3001 (chat-based agent runs on 3000)
- **Backend**: Connects to `http://localhost:8000`
- **Voice Flow**: Speech → STT → Backend → TTS → Speech

## Components

- `VoiceChatPage`: Main voice conversation interface
- `ItineraryFeed`: Displays day-wise itinerary
- `DaySelector`: Day navigation tabs
- `ActivityCard`: Individual activity display
- `SourcesModal`: RAG sources display

## API Integration

The app connects to the backend `/api/voice/chat` endpoint which handles:
1. Speech-to-Text (ElevenLabs)
2. Trip planning backend processing
3. Text-to-Speech (AssemblyAI)

## Requirements

- Modern browser with microphone access
- Backend server running on port 8000
- API keys configured in backend `.env` file







