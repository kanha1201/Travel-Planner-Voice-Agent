# Jaipur Travel Planner - Testing Interface

A React-based chat interface for testing the Jaipur Travel Planner backend.

## Features

- 💬 **Chat Interface**: Send messages and receive AI responses
- 📅 **Itinerary Visualizer**: View day-wise travel plans with timeline
- 🔍 **Debug Panel**: Inspect sources and raw JSON state
- 📱 **Responsive Design**: Desktop split-screen and mobile tabbed views
- 🎨 **Modern UI**: Built with Tailwind CSS and Lucide icons

## Setup

1. **Install Dependencies**
   ```bash
   cd frontend
   npm install
   ```

2. **Start Development Server**
   ```bash
   npm run dev
   ```

3. **Access the App**
   - Open http://localhost:3000 in your browser
   - Make sure the backend is running on http://localhost:8000

## Usage

### Mock Data Mode
- Enable "Use Mock Data" checkbox in the header to test the UI without backend
- This uses sample itinerary and sources data

### Real Backend Mode
- Ensure backend is running: `cd backend && python -m uvicorn main:app --reload`
- Disable "Use Mock Data" to connect to the actual API
- Send messages like: "Plan a 2-day cultural trip to Jaipur with a relaxed pace"

## Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── ChatPanel.tsx      # Chat interface with messages
│   │   ├── ItineraryDisplay.tsx # Day tabs and timeline view
│   │   └── DebugPanel.tsx     # Sources and raw JSON
│   ├── types.ts               # TypeScript interfaces
│   ├── mockData.ts            # Sample data for testing
│   ├── App.tsx                # Main app component
│   └── main.tsx               # Entry point
├── package.json
└── vite.config.ts
```

## API Integration

The app connects to the backend API at `/api/trip/chat`:

```typescript
POST /api/trip/chat
{
  "message": "Plan a 2-day trip",
  "session_id": "optional-session-id"
}
```

Response format matches `ApiResponse` type in `types.ts`.

## Development

- **Build**: `npm run build`
- **Preview**: `npm run preview`
- **Lint**: `npm run lint`










