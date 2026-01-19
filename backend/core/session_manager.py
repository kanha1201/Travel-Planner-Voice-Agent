"""
Session management for user conversations
"""

from typing import Dict, Optional, List
import uuid
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class SessionManager:
    """
    Manages user sessions and conversation context
    """
    
    def __init__(self, session_timeout_minutes: int = 30):
        self.sessions: Dict[str, Dict] = {}
        self.session_timeout = timedelta(minutes=session_timeout_minutes)
        logger.info(f"Session manager initialized (timeout: {session_timeout_minutes} minutes)")
    
    def create_session(self) -> str:
        """Create a new session"""
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = {
            "created_at": datetime.now(),
            "last_accessed": datetime.now(),
            "conversation_history": [],
            "user_preferences": {},
            "current_itinerary": None,
            "sources": [],  # Citations/sources from RAG
            "questions_asked": 0
        }
        logger.info(f"Created new session: {session_id}")
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """Get session data"""
        if session_id not in self.sessions:
            return None
        
        session = self.sessions[session_id]
        
        # Check if session expired
        if datetime.now() - session["last_accessed"] > self.session_timeout:
            logger.info(f"Session {session_id} expired")
            del self.sessions[session_id]
            return None
        
        # Update last accessed
        session["last_accessed"] = datetime.now()
        return session
    
    def update_session(self, session_id: str, updates: Dict):
        """Update session data"""
        if session_id not in self.sessions:
            return
        
        self.sessions[session_id].update(updates)
        self.sessions[session_id]["last_accessed"] = datetime.now()
    
    def add_message(self, session_id: str, role: str, content: str):
        """Add message to conversation history"""
        if session_id not in self.sessions:
            return
        
        self.sessions[session_id]["conversation_history"].append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        self.sessions[session_id]["last_accessed"] = datetime.now()
    
    def get_conversation_history(self, session_id: str, 
                                 max_messages: int = 30) -> List[Dict]:
        """Get recent conversation history"""
        session = self.get_session(session_id)
        if not session:
            return []
        
        history = session["conversation_history"]
        # Return last N messages
        return history[-max_messages:] if len(history) > max_messages else history
    
    def increment_questions(self, session_id: str):
        """Increment question count"""
        if session_id in self.sessions:
            self.sessions[session_id]["questions_asked"] += 1
    
    def get_questions_asked(self, session_id: str) -> int:
        """Get number of questions asked"""
        session = self.get_session(session_id)
        return session["questions_asked"] if session else 0
    
    def cleanup_expired_sessions(self):
        """Remove expired sessions"""
        now = datetime.now()
        expired = [
            sid for sid, session in self.sessions.items()
            if now - session["last_accessed"] > self.session_timeout
        ]
        for sid in expired:
            del self.sessions[sid]
        if expired:
            logger.info(f"Cleaned up {len(expired)} expired sessions")
        return len(expired)


if __name__ == "__main__":
    # Test session manager
    logging.basicConfig(level=logging.INFO)
    manager = SessionManager()
    
    session_id = manager.create_session()
    logger.info(f"Created session: {session_id}")
    
    manager.add_message(session_id, "user", "Plan a 2-day trip")
    manager.add_message(session_id, "assistant", "I'll help you plan...")
    
    history = manager.get_conversation_history(session_id)
    logger.info(f"History: {len(history)} messages")

