"""
Tool result caching to avoid redundant API calls
"""

from typing import Dict, Optional, Any
from datetime import datetime, timedelta
import hashlib
import json
import logging

logger = logging.getLogger(__name__)


class ToolCache:
    """
    Cache tool execution results to reduce redundant calls
    """
    
    def __init__(self, ttl_hours: int = 24, max_size: int = 500):
        """
        Initialize tool cache
        
        Args:
            ttl_hours: Time-to-live for cache entries in hours
            max_size: Maximum number of cache entries
        """
        self.cache: Dict[str, Dict] = {}
        self.ttl = timedelta(hours=ttl_hours)
        self.max_size = max_size
        logger.info(f"Tool cache initialized (TTL: {ttl_hours} hours, Max size: {max_size})")
    
    def _generate_key(self, function_name: str, args: Dict[str, Any]) -> str:
        """
        Generate cache key from function name and arguments
        
        Args:
            function_name: Name of the function
            args: Function arguments
        
        Returns:
            Cache key string
        """
        # Normalize args (sort keys, remove None values)
        normalized_args = {
            k: v for k, v in sorted(args.items()) 
            if v is not None
        }
        
        key_string = f"{function_name}:{json.dumps(normalized_args, sort_keys=True)}"
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def get(self, function_name: str, args: Dict[str, Any]) -> Optional[Dict]:
        """
        Get cached tool result if available
        
        Args:
            function_name: Name of the function
            args: Function arguments
        
        Returns:
            Cached result dict or None
        """
        key = self._generate_key(function_name, args)
        
        if key not in self.cache:
            return None
        
        entry = self.cache[key]
        
        # Check if expired
        if datetime.now() - entry["timestamp"] > self.ttl:
            del self.cache[key]
            logger.debug(f"Tool cache entry expired: {function_name}:{key[:8]}")
            return None
        
        logger.info(f"✅ Tool cache hit: {function_name}:{key[:8]}")
        return entry["result"]
    
    def set(self, function_name: str, args: Dict[str, Any], result: Dict):
        """
        Cache a tool result
        
        Args:
            function_name: Name of the function
            args: Function arguments
            result: Tool result to cache
        """
        # Don't cache if cache is full
        if len(self.cache) >= self.max_size:
            # Remove oldest entries
            oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k]["timestamp"])
            del self.cache[oldest_key]
            logger.debug(f"Tool cache full, removed oldest entry: {oldest_key[:8]}")
        
        key = self._generate_key(function_name, args)
        self.cache[key] = {
            "result": result,
            "timestamp": datetime.now()
        }
        logger.debug(f"Cached tool result: {function_name}:{key[:8]}")
    
    def clear(self):
        """Clear all cache entries"""
        count = len(self.cache)
        self.cache.clear()
        logger.info(f"Cleared {count} tool cache entries")


# Global tool cache instance
_tool_cache: Optional[ToolCache] = None


def get_tool_cache() -> ToolCache:
    """Get global tool cache instance"""
    global _tool_cache
    if _tool_cache is None:
        import os
        from dotenv import load_dotenv
        load_dotenv()
        ttl = int(os.getenv("TOOL_CACHE_TTL_HOURS", "24"))
        max_size = int(os.getenv("TOOL_CACHE_MAX_SIZE", "500"))
        _tool_cache = ToolCache(ttl_hours=ttl, max_size=max_size)
    return _tool_cache










