"""
Trip Planning API Routes
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
import logging
from llm.orchestrator import LLMOrchestrator
from core.session_manager import SessionManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/trip", tags=["trip"])

# Initialize orchestrator (singleton)
_orchestrator = None

def get_orchestrator() -> LLMOrchestrator:
    """Get or create orchestrator instance"""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = LLMOrchestrator()
    return _orchestrator

def get_session_manager() -> SessionManager:
    """Get session manager from orchestrator"""
    orchestrator = get_orchestrator()
    return orchestrator.session_manager


# Request/Response Models
class TripRequest(BaseModel):
    """Request model for trip planning"""
    message: str = Field(..., description="User message/request")
    session_id: Optional[str] = Field(None, description="Session ID (optional, will create new if not provided)")

class TripResponse(BaseModel):
    """Response model for trip planning"""
    status: str = Field(..., description="Response status")
    response: str = Field(..., description="LLM response text")
    session_id: str = Field(..., description="Session ID")
    tool_calls: List[Dict] = Field(default_factory=list, description="Tool calls made")
    usage: Optional[Dict] = Field(None, description="Token usage information")
    itinerary: Optional[Dict] = Field(None, description="Structured itinerary (if generated)")
    sources: Optional[List[Dict]] = Field(None, description="Citations/sources (if available)")

class ErrorResponse(BaseModel):
    """Error response model"""
    status: str = "error"
    error_type: str = Field(..., description="Type of error")
    message: str = Field(..., description="Error message")
    session_id: Optional[str] = None
    details: Optional[str] = Field(None, description="Additional error details")


@router.post("/chat", response_model=TripResponse, responses={500: {"model": ErrorResponse}})
async def chat(request: TripRequest, orchestrator: LLMOrchestrator = Depends(get_orchestrator)):
    """
    Main chat endpoint for trip planning
    
    Handles:
    - Creating new itineraries
    - Editing existing itineraries
    - Answering questions
    - All user interactions
    """
    try:
        logger.info(f"Received request: {request.message[:100]}...")
        
        # Get or create session
        session_id = request.session_id
        if not session_id:
            session_id = orchestrator.session_manager.create_session()
            logger.info(f"Created new session: {session_id}")
        else:
            session = orchestrator.session_manager.get_session(session_id)
            if not session:
                session_id = orchestrator.session_manager.create_session()
                logger.info(f"Session expired, created new: {session_id}")
        
        # Process request
        result = orchestrator.process_user_request(
            user_message=request.message,
            session_id=session_id
        )
        
        # Get current itinerary and sources from session
        session = orchestrator.session_manager.get_session(session_id)
        itinerary = session.get("current_itinerary") if session else None
        
        # Ensure itinerary structure is complete (all days have all time slots, even if empty)
        if itinerary:
            for day_key in ["day_1", "day_2", "day_3"]:
                if day_key in itinerary and itinerary[day_key]:
                    day = itinerary[day_key]
                    # Ensure all time slots exist as arrays
                    if "morning" not in day:
                        day["morning"] = []
                    if "afternoon" not in day:
                        day["afternoon"] = []
                    if "evening" not in day:
                        day["evening"] = []
                    # Ensure arrays are lists (not None)
                    day["morning"] = day["morning"] if isinstance(day["morning"], list) else []
                    day["afternoon"] = day["afternoon"] if isinstance(day["afternoon"], list) else []
                    day["evening"] = day["evening"] if isinstance(day["evening"], list) else []
        
        sources = session.get("sources", []) if session else []
        
        # Deduplicate sources
        if sources:
            seen_urls = set()
            unique_sources = []
            for source in sources:
                url = source.get("url", "")
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    unique_sources.append(source)
            sources = unique_sources[:10]  # Limit to 10 sources
        
        return TripResponse(
            status="success",
            response=result["response"],
            session_id=result["session_id"],
            tool_calls=result.get("tool_calls", []),
            usage=result.get("usage"),
            itinerary=itinerary,
            sources=sources
        )
        
    except ValueError as e:
        # Validation errors
        logger.error(f"Validation error: {e}")
        raise HTTPException(
            status_code=400,
            detail={
                "status": "error",
                "error_type": "validation_error",
                "message": str(e),
                "session_id": request.session_id
            }
        )
    except Exception as e:
        # Generic errors
        logger.error(f"Error processing request: {e}", exc_info=True)
        import traceback
        error_traceback = traceback.format_exc()
        logger.error(f"Full traceback:\n{error_traceback}")
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "error_type": "server_error",
                "message": f"I'm having trouble processing your request right now. Error: {str(e)}",
                "session_id": request.session_id,
                "details": error_traceback[-500:] if logger.level <= logging.INFO else None  # Last 500 chars of traceback
            }
        )


@router.get("/session/{session_id}")
async def get_session(session_id: str, 
                     session_manager: SessionManager = Depends(get_session_manager)):
    """Get session data"""
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {
        "session_id": session_id,
        "conversation_history": session["conversation_history"][-10:],  # Last 10 messages
        "user_preferences": session["user_preferences"],
        "current_itinerary": session["current_itinerary"],
        "questions_asked": session["questions_asked"]
    }


@router.delete("/session/{session_id}")
async def delete_session(session_id: str,
                        session_manager: SessionManager = Depends(get_session_manager)):
    """Delete session"""
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Remove session
    if session_id in session_manager.sessions:
        del session_manager.sessions[session_id]
        logger.info(f"Deleted session: {session_id}")
    
    return {"message": "Session deleted", "session_id": session_id}


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "components": {
            "orchestrator": "ready",
            "session_manager": "ready"
        }
    }

