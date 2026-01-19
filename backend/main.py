"""
FastAPI main application
Voice Travel Planner Backend
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Voice Travel Planner API",
    description="AI-powered voice-first travel planning assistant for Jaipur",
    version="1.0.0"
)

# CORS middleware
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    """Root endpoint"""
    return {
        "message": "Voice Travel Planner API",
        "status": "running",
        "version": "1.0.0"
    }

@app.get("/health")
def health():
    """Health check endpoint"""
    return {"status": "healthy"}

# Import and register routers
try:
    from api.routes import trip, voice
    
    # Register routers
    app.include_router(trip.router)
    app.include_router(voice.router)
    logger.info("✅ API routes registered")
except ImportError as e:
    logger.warning(f"Could not import routes: {e}")

# @app.on_event("startup")
# async def startup_event():
#     """Initialize services on startup"""
#     logger.info("Starting Voice Travel Planner API...")

if __name__ == "__main__":
    import uvicorn
    host = os.getenv("BACKEND_HOST", "0.0.0.0")
    port = int(os.getenv("BACKEND_PORT", 8000))
    uvicorn.run(app, host=host, port=port, reload=True)

