# Frontend Setup Guide

## Quick Start

1. **Navigate to frontend directory**
   ```bash
   cd frontend
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Start development server**
   ```bash
   npm run dev
   ```

4. **Open in browser**
   - The app will be available at http://localhost:3000
   - Make sure the backend is running on http://localhost:8000

## Features

### Desktop View (≥768px)
- **Left Panel (40%)**: Chat interface
- **Right Panel (60%)**: Itinerary visualizer + Debug panel

### Mobile View (<768px)
- **Tab Navigation**: Switch between "Chat" and "Plan" tabs
- **Chat Tab**: Full chat interface
- **Plan Tab**: Itinerary view + Debug panel

## Testing Modes

### Mock Data Mode
- Enable "Use Mock Data" checkbox in header
- Tests UI without backend connection
- Uses sample itinerary and sources

### Real Backend Mode
- Disable "Use Mock Data"
- Connects to backend API at `/api/trip/chat`
- Requires backend to be running

## Troubleshooting

### Port Already in Use
If port 3000 is busy, Vite will automatically use the next available port.

### Backend Connection Issues
- Check that backend is running: `cd backend && python -m uvicorn main:app --reload`
- Verify CORS is configured in backend (should be set to allow localhost:3000)
- Check browser console for errors

### TypeScript Errors
- Run `npm install` to ensure all types are installed
- Check that `tsconfig.json` is properly configured

## Build for Production

```bash
npm run build
```

The built files will be in the `dist/` directory.










