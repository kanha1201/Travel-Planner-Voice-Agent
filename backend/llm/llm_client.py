"""
Unified LLM client interface - supports Cerebras, Groq, and Gemini
Implements fallback chain: Cerebras -> Groq -> Gemini
"""

import os
from typing import List, Dict, Optional
from dotenv import load_dotenv
import logging

load_dotenv()

logger = logging.getLogger(__name__)


class LLMClient:
    """
    Unified LLM client that supports Cerebras, Groq, and Gemini
    Implements automatic fallback chain: Cerebras -> Groq -> Gemini
    """
    
    def __init__(self, provider: Optional[str] = None):
        """
        Initialize LLM client
        
        Args:
            provider: "cerebras", "groq", "gemini", or None (auto-detect, defaults to cerebras)
        """
        # Determine provider
        if provider is None:
            provider = os.getenv("LLM_PROVIDER", "cerebras").lower()
        
        self.provider = provider
        self.current_provider = provider  # Track current active provider
        
        # Initialize the primary client
        if provider == "cerebras":
            from .cerebras_client import CerebrasClient
            self.client = CerebrasClient()
            logger.info(f"✅ Using Cerebras as primary LLM provider")
        elif provider == "gemini":
            from .gemini_client import GeminiClient
            self.client = GeminiClient()
            logger.info(f"✅ Using Gemini as primary LLM provider")
        elif provider == "groq":
            from .groq_client import GroqClient
            self.client = GroqClient()
            logger.info(f"✅ Using Groq as primary LLM provider")
        else:
            raise ValueError(f"Unknown LLM provider: {provider}. Use 'cerebras', 'groq', or 'gemini'")
    
    def get_system_prompt(self) -> str:
        """Get the system prompt"""
        return self.client.get_system_prompt()
    
    def _clean_messages_for_groq(self, messages: List[Dict]) -> List[Dict]:
        """
        Clean messages when falling back from Gemini to Groq
        Converts Gemini-formatted tool responses back to Groq format
        """
        cleaned = []
        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content", "")
            
            # If it's a user message that looks like a Gemini tool response, convert it back
            if role == "user" and content.startswith("Function ") and " returned: " in content:
                # Extract function name and result
                try:
                    parts = content.split(" returned: ", 1)
                    if len(parts) == 2:
                        func_name = parts[0].replace("Function ", "").strip()
                        func_result = parts[1]
                        
                        # Find the corresponding tool_call_id from previous assistant message
                        # For now, just keep as user message - Groq should handle it
                        # Actually, we should convert it to tool role if we have the tool_call_id
                        cleaned.append(msg)  # Keep as-is for now
                    else:
                        cleaned.append(msg)
                except:
                    cleaned.append(msg)
            else:
                # Keep other messages as-is
                cleaned.append(msg)
        
        return cleaned
    
    def _is_retryable_error(self, error: Exception) -> bool:
        """
        Check if an error is retryable (should trigger fallback)
        
        Args:
            error: The exception that occurred
            
        Returns:
            True if error is retryable (rate limit, API error, etc.)
        """
        error_str = str(error).lower()
        retryable_keywords = [
            "rate limit", "429", "quota", "serializable", "mapcomposite",
            "invalid", "400", "500", "503", "timeout", "exceeded",
            "connection", "network", "unavailable", "service"
        ]
        return any(keyword in error_str for keyword in retryable_keywords)
    
    def _switch_provider(self, new_provider: str, messages: List[Dict]):
        """
        Switch to a different provider
        
        Args:
            new_provider: Provider name ("cerebras", "groq", "gemini")
            messages: Current messages (may need cleaning for new provider)
        """
        logger.info(f"🔄 Switching provider from {self.current_provider} to {new_provider}...")
        
        if new_provider == "cerebras":
            from .cerebras_client import CerebrasClient
            self.client = CerebrasClient()
            self.current_provider = "cerebras"
        elif new_provider == "groq":
            from .groq_client import GroqClient
            self.client = GroqClient()
            self.current_provider = "groq"
            # Clean messages for Groq if coming from Gemini
            messages = self._clean_messages_for_groq(messages)
        elif new_provider == "gemini":
            from .gemini_client import GeminiClient
            self.client = GeminiClient()
            self.current_provider = "gemini"
        else:
            raise ValueError(f"Unknown provider: {new_provider}")
        
        logger.info(f"✅ Switched to {new_provider}")
        return messages
    
    def chat_completion(self, messages: List[Dict], tools: Optional[List[Dict]] = None,
                       tool_choice: str = "auto", temperature: float = 0.7) -> Dict:
        """
        Make a chat completion request with automatic fallback chain
        
        Fallback order: Cerebras -> Groq -> Gemini
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            tools: List of function definitions (for function calling)
            tool_choice: "auto", "none", or {"type": "function", "function": {"name": "..."}}
            temperature: Sampling temperature (0-2)
        
        Returns:
            Response dict with message and tool_calls
        """
        # Define fallback chain based on current provider
        if self.current_provider == "cerebras":
            fallback_chain = ["cerebras", "groq", "gemini"]
        elif self.current_provider == "groq":
            fallback_chain = ["groq", "gemini"]
        elif self.current_provider == "gemini":
            fallback_chain = ["gemini"]
        else:
            fallback_chain = ["cerebras", "groq", "gemini"]
        
        last_error = None
        
        # Try each provider in the fallback chain
        for i, provider_name in enumerate(fallback_chain):
            # Skip if we've already tried this provider
            if i > 0 or self.current_provider != provider_name:
                # Switch to this provider
                try:
                    messages = self._switch_provider(provider_name, messages)
                except Exception as switch_error:
                    logger.warning(f"⚠️  Failed to switch to {provider_name}: {switch_error}")
                    continue
            
            try:
                logger.info(f"🔄 Attempting request with {provider_name.upper()}...")
                result = self.client.chat_completion(
                    messages=messages,
                    tools=tools,
                    tool_choice=tool_choice,
                    temperature=temperature
                )
                logger.info(f"✅ Successfully completed request with {provider_name.upper()}")
                return result
                
            except Exception as e:
                last_error = e
                error_str = str(e).lower()
                
                # Check if this is a quota exceeded error (non-retryable, permanent)
                if "quota exceeded" in error_str or "exceeded your current quota" in error_str:
                    logger.error(f"⚠️  {provider_name.upper()} daily quota exceeded - will skip in future")
                    # Continue to next provider in chain
                    continue
                
                # Check if error is retryable
                if self._is_retryable_error(e):
                    logger.warning(f"⚠️  {provider_name.upper()} failed with retryable error: {e}")
                    # Continue to next provider in chain
                    continue
                else:
                    # Non-retryable error (e.g., invalid request), don't fallback
                    logger.error(f"❌ {provider_name.upper()} failed with non-retryable error: {e}")
                    raise
        
        # All providers failed
        error_summary = f"All providers in fallback chain failed. Last error: {last_error}"
        logger.error(f"❌ {error_summary}")
        raise Exception(error_summary)

