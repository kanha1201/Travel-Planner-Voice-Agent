# Voice Travel Planner - Trip Planning Assistant

An AI-powered voice assistant for planning personalized trips to Jaipur, India. The system uses natural language processing, RAG (Retrieval Augmented Generation), and real-time POI search to create customized itineraries based on user preferences.

## 🏗️ Architecture

### System Overview

```
┌─────────────────┐
│  Voice Frontend │  (React + TypeScript)
│  (Browser)      │
└────────┬────────┘
         │ HTTP/WebSocket
         ▼
┌─────────────────┐
│  FastAPI Server │  (Python Backend)
│  (Port 8000)    │
└────────┬────────┘
         │
    ┌────┴────┬──────────────┬─────────────┐
    ▼         ▼              ▼             ▼
┌────────┐ ┌────────┐  ┌─────────┐  ┌──────────┐
│  LLM   │ │  RAG    │  │  POI     │  │  Voice   │
│Orchestr│ │ System  │  │  Search  │  │ Services │
│        │ │         │  │          │  │          │
└────────┘ └────────┘  └─────────┘  └──────────┘
    │         │              │             │
    ▼         ▼              ▼             ▼
┌─────────────────────────────────────────────────┐
│  External Services                               │
│  - Cerebras/Groq/Gemini (LLM)                    │
│  - AssemblyAI (Speech-to-Text)                   │
│  - ElevenLabs (Text-to-Speech)                   │
│  - OpenStreetMap (POI Data)                      │
│  - ChromaDB (Vector Database)                    │
└─────────────────────────────────────────────────┘
```

### Core Components

#### 1. **Frontend** (`voice-frontend/`)
- **Technology**: React 18, TypeScript, Vite, Tailwind CSS
- **Components**:
  - `VoiceChatPage`: Main voice interface with transcript display
  - `ItineraryFeed`: Day-wise itinerary visualization
  - `SourcesModal`: Data sources display
  - `Header`: Navigation and info button
- **Features**:
  - Real-time voice recording and playback
  - Scrollable chat interface
  - Formatted message display (days, time periods, bullet points)
  - Source citations in modal

#### 2. **Backend** (`backend/`)
- **Technology**: FastAPI, Python 3.12+
- **Key Modules**:
  - `api/routes/voice.py`: Voice chat API endpoint
  - `api/routes/trip.py`: Itinerary retrieval endpoint
  - `llm/orchestrator.py`: LLM orchestration with tool calling
  - `llm/cerebras_client.py`: Cerebras LLM integration
  - `llm/groq_client.py`: Groq LLM integration
  - `llm/gemini_client.py`: Gemini LLM integration
  - `tools/poi_search.py`: OpenStreetMap POI search
  - `tools/itinerary_builder.py`: Day-wise itinerary construction
  - `tools/rag_retrieval.py`: RAG-based city guidance retrieval
  - `rag/`: RAG system (data ingestion, chunking, vector store)
  - `voice/`: STT/TTS clients (AssemblyAI, ElevenLabs)
  - `core/session_manager.py`: Session management
  - `core/response_cache.py`: Response caching
  - `core/tool_cache.py`: Tool result caching

#### 3. **LLM Orchestrator**
- **Function Calling**: Supports tool execution with automatic fallback
- **Providers**: Cerebras (primary) → Groq (fallback) → Gemini (last resort)
- **Tools**:
  - `search_pois`: Find points of interest
  - `build_itinerary`: Create structured day-wise plans
  - `retrieve_city_guidance`: Get factual information with citations
  - `ask_clarifying_question`: Generate clarifying questions

#### 4. **RAG System**
- **Vector Database**: ChromaDB with sentence-transformers embeddings
- **Embedding Model**: `all-MiniLM-L6-v2` (384 dimensions)
- **Data Sources**: Wikivoyage, Wikipedia
- **Chunking**: ~500 tokens per chunk with overlap
- **Retrieval**: Semantic search with top-k results

#### 5. **Voice Services**
- **STT (Speech-to-Text)**: AssemblyAI (primary), ElevenLabs (alternative)
- **TTS (Text-to-Speech)**: ElevenLabs
- **Audio Format**: WebM (browser) → WAV (converted) → MP3 (response)

## 🚀 Setup

### Prerequisites

- **Python**: 3.12 or higher
- **Node.js**: 18+ and npm
- **ffmpeg**: Required for audio conversion (download from https://ffmpeg.org/download.html)
- **API Keys**:
  - Cerebras API key (or Groq/Gemini as fallback)
  - AssemblyAI API key (for STT)
  - ElevenLabs API key (for TTS)

### Backend Setup

1. **Navigate to backend directory**:
   ```bash
   cd backend
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   ```

3. **Activate virtual environment**:
   - **Windows**:
     ```bash
     .\venv\Scripts\activate
     ```
   - **Linux/Mac**:
     ```bash
     source venv/bin/activate
     ```

4. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

5. **Set up environment variables**:
   ```bash
   cp env.example .env
   ```
   Edit `.env` and add your API keys:
   ```env
   CEREBRAS_API_KEY=your_key_here
   ASSEMBLYAI_API_KEY=your_key_here
   ELEVENLABS_API_KEY=your_key_here
   ```

6. **Ingest RAG data** (first time only):
   ```bash
   python -m rag.ingest_pipeline
   ```
   This downloads and processes travel guide data from Wikivoyage and Wikipedia.

7. **Start the server**:
   ```bash
   uvicorn main:app --reload
   ```
   Server runs on `http://localhost:8000`

### Frontend Setup

1. **Navigate to frontend directory**:
   ```bash
   cd voice-frontend
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Start development server**:
   ```bash
   npm run dev
   ```
   Frontend runs on `http://localhost:5173`

### Verify Installation

1. Backend health check: `http://localhost:8000/docs` (FastAPI Swagger UI)
2. Frontend: Open `http://localhost:5173` in browser
3. Test voice chat: Click microphone button and speak

## 📁 Project Structure

```
.
├── backend/
│   ├── api/
│   │   └── routes/
│   │       ├── voice.py          # Voice chat endpoint
│   │       └── trip.py           # Itinerary endpoint
│   ├── core/
│   │   ├── session_manager.py   # Session management
│   │   ├── response_cache.py    # Response caching
│   │   └── tool_cache.py        # Tool result caching
│   ├── llm/
│   │   ├── orchestrator.py      # LLM orchestration
│   │   ├── cerebras_client.py   # Cerebras LLM client
│   │   ├── groq_client.py       # Groq LLM client
│   │   ├── gemini_client.py     # Gemini LLM client
│   │   └── functions.py         # Function definitions
│   ├── tools/
│   │   ├── poi_search.py         # POI search tool
│   │   ├── itinerary_builder.py  # Itinerary builder tool
│   │   ├── rag_retrieval.py     # RAG retrieval tool
│   │   └── register_handlers.py # Tool registration
│   ├── rag/
│   │   ├── data_ingestion.py    # Data fetching
│   │   ├── chunking.py          # Text chunking
│   │   ├── vector_store.py      # ChromaDB management
│   │   ├── retrieval.py        # RAG retrieval
│   │   └── ingest_pipeline.py   # Ingestion pipeline
│   ├── voice/
│   │   ├── stt_client.py        # STT client interface
│   │   ├── assemblyai_stt_client.py  # AssemblyAI STT
│   │   ├── tts_client.py        # TTS client interface
│   │   └── elevenlabs_tts_client.py  # ElevenLabs TTS
│   ├── data/
│   │   ├── raw/                 # Raw data files
│   │   └── chroma_db/           # Vector database
│   ├── main.py                  # FastAPI app
│   ├── requirements.txt         # Python dependencies
│   ├── env.example              # Environment template
│   └── test_sources.py          # Source testing script
│
├── voice-frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── VoiceChatPage.tsx    # Main voice interface
│   │   │   ├── ItineraryFeed.tsx    # Itinerary display
│   │   │   ├── SourcesModal.tsx     # Sources modal
│   │   │   └── Header.tsx          # App header
│   │   ├── utils/
│   │   │   ├── api.ts               # API client
│   │   │   ├── voiceRecorder.ts     # Voice recording
│   │   │   └── formatMessage.ts    # Message formatting
│   │   ├── App.tsx                  # Main app component
│   │   └── types.ts                 # TypeScript types
│   ├── package.json
│   └── vite.config.ts
│
└── README.md                      # This file
```

## 🔧 Configuration

### Environment Variables

See `backend/env.example` for all available configuration options.

**Key Variables**:
- `LLM_PROVIDER`: `cerebras`, `groq`, or `gemini` (default: `cerebras`)
- `STT_PROVIDER`: `assemblyai` or `elevenlabs` (default: `assemblyai`)
- `TTS_PROVIDER`: `elevenlabs` (only option currently)
- `LOG_LEVEL`: `DEBUG`, `INFO`, `WARNING`, `ERROR` (default: `INFO`)

### LLM Provider Selection

The system automatically falls back through providers:
1. **Cerebras** (primary) - Fast, reliable
2. **Groq** (fallback) - Fast inference
3. **Gemini** (last resort) - Google's model

Set `LLM_PROVIDER` in `.env` to force a specific provider.

## 🧪 Testing

### Test Sources Generation

Test if sources are being generated correctly:

```bash
cd backend
.\venv\Scripts\activate  # Windows
# or: source venv/bin/activate  # Linux/Mac
python test_sources.py
```

### Manual Testing

1. **Voice Chat**: Use the microphone button to test voice interactions
2. **Itinerary Generation**: Ask "Plan a 2-day trip to Jaipur"
3. **Source Citations**: Click the "i" button to view sources
4. **Itinerary Modifications**: Try "Remove Day 1 morning activity"

## 📚 Documentation

- **Tools**: See [TOOLS.md](TOOLS.md) for detailed tool documentation
- **Datasets**: See [DATASETS.md](DATASETS.md) for data sources
- **Evaluations**: See [EVALS.md](EVALS.md) for evaluation instructions
- **Sample Transcripts**: See [SAMPLE_TRANSCRIPTS.md](SAMPLE_TRANSCRIPTS.md) for test cases

## 🐛 Troubleshooting

### Common Issues

1. **"ModuleNotFoundError: No module named 'dotenv'"**
   - Solution: Activate virtual environment before running scripts

2. **"ElevenLabs API key error"**
   - Solution: Verify API key in `.env` file, check account credits

3. **"AssemblyAI STT error: File does not appear to contain audio"**
   - Solution: Ensure ffmpeg is installed and in PATH

4. **"Sources not appearing in UI"**
   - Solution: Check browser console for errors, verify backend logs

5. **"LLM provider errors"**
   - Solution: System will auto-fallback to next provider, check API keys

### Debug Mode

Enable debug logging:
```env
LOG_LEVEL=DEBUG
```

## 📝 License

This project is for educational/demonstration purposes.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📧 Support

For issues or questions, please open an issue on the repository.


