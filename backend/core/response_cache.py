"""
Response caching to reduce LLM API calls
"""

from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
import hashlib
import json
import logging

logger = logging.getLogger(__name__)


class ResponseCache:
    """
    Cache LLM responses to reduce API calls
    Uses content-based hashing for cache keys
    """
    
    def __init__(self, ttl_minutes: int = 60, max_size: int = 1000):
        """
        Initialize response cache
        
        Args:
            ttl_minutes: Time-to-live for cache entries in minutes
            max_size: Maximum number of cache entries
        """
        self.cache: Dict[str, Dict] = {}
        self.ttl = timedelta(minutes=ttl_minutes)
        self.max_size = max_size
        logger.info(f"Response cache initialized (TTL: {ttl_minutes} min, Max size: {max_size})")
    
    def _generate_key(self, messages: list, tools_hash: Optional[str] = None) -> str:
        """
        Generate cache key from messages and tools
        
        Args:
            messages: List of message dicts
            tools_hash: Optional hash of tools configuration
        
        Returns:
            Cache key string
        """
        # Extract relevant parts for hashing
        # Only use last few messages and system prompt for key generation
        key_parts = []
        
        # System prompt
        for msg in messages:
            if msg.get("role") == "system":
                key_parts.append(f"system:{msg.get('content', '')[:100]}")
                break
        
        # Last user message (most important for cache hit)
        for msg in reversed(messages):
            if msg.get("role") == "user":
                key_parts.append(f"user:{msg.get('content', '')}")
                break
        
        # Tools hash if provided
        if tools_hash:
            key_parts.append(f"tools:{tools_hash}")
        
        # Create hash
        key_string = "|".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def get(self, messages: list, tools_hash: Optional[str] = None) -> Optional[Dict]:
        """
        Get cached response if available
        
        Args:
            messages: List of message dicts
            tools_hash: Optional hash of tools configuration
        
        Returns:
            Cached response dict or None
        """
        key = self._generate_key(messages, tools_hash)
        
        if key not in self.cache:
            return None
        
        entry = self.cache[key]
        
        # Check if expired
        if datetime.now() - entry["timestamp"] > self.ttl:
            del self.cache[key]
            logger.debug(f"Cache entry expired: {key[:8]}")
            return None
        
        # Check if it's a tool-call response (don't cache those)
        if entry.get("has_tool_calls", False):
            logger.debug(f"Cache entry has tool calls, skipping: {key[:8]}")
            return None
        
        logger.info(f"✅ Cache hit: {key[:8]}")
        return entry["response"]
    
    def set(self, messages: list, response: Dict, tools_hash: Optional[str] = None, 
            has_tool_calls: bool = False):
        """
        Cache a response
        
        Args:
            messages: List of message dicts
            response: Response dict to cache
            tools_hash: Optional hash of tools configuration
            has_tool_calls: Whether response contains tool calls (don't cache these)
        """
        # Don't cache responses with tool calls
        if has_tool_calls:
            return
        
        # Don't cache if cache is full
        if len(self.cache) >= self.max_size:
            # Remove oldest entries (simple FIFO)
            oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k]["timestamp"])
            del self.cache[oldest_key]
            logger.debug(f"Cache full, removed oldest entry: {oldest_key[:8]}")
        
        key = self._generate_key(messages, tools_hash)
        self.cache[key] = {
            "response": response,
            "timestamp": datetime.now(),
            "has_tool_calls": has_tool_calls
        }
        logger.debug(f"Cached response: {key[:8]}")
    
    def clear(self):
        """Clear all cache entries"""
        count = len(self.cache)
        self.cache.clear()
        logger.info(f"Cleared {count} cache entries")
    
    def cleanup_expired(self) -> int:
        """Remove expired entries"""
        now = datetime.now()
        expired = [
            key for key, entry in self.cache.items()
            if now - entry["timestamp"] > self.ttl
        ]
        for key in expired:
            del self.cache[key]
        if expired:
            logger.info(f"Cleaned up {len(expired)} expired cache entries")
        return len(expired)


# Global cache instance
_response_cache: Optional[ResponseCache] = None


def get_cache() -> ResponseCache:
    """Get global cache instance"""
    global _response_cache
    if _response_cache is None:
        import os
        from dotenv import load_dotenv
        load_dotenv()
        ttl = int(os.getenv("RESPONSE_CACHE_TTL_MINUTES", "60"))
        max_size = int(os.getenv("RESPONSE_CACHE_MAX_SIZE", "1000"))
        _response_cache = ResponseCache(ttl_minutes=ttl, max_size=max_size)
    return _response_cache










