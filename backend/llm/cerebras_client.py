"""
Cerebras LLM client configuration
"""

import requests
from typing import List, Dict, Optional
import os
from dotenv import load_dotenv
import logging
import json
import re

load_dotenv()

logger = logging.getLogger(__name__)


class CerebrasClient:
    """Cerebras LLM client wrapper"""
    
    def __init__(self, model: str = "llama-3.3-70b"):
        """
        Initialize Cerebras client
        
        Args:
            model: Model name (default: llama-3.3-70b)
        """
        api_key = os.getenv("CEREBRAS_API_KEY")
        if not api_key:
            raise ValueError("CEREBRAS_API_KEY not found in environment variables. Please set it in .env file.")
        
        base_url = os.getenv("CEREBRAS_BASE_URL", "https://api.cerebras.ai/v1")
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        logger.info(f"✅ Cerebras client initialized with model: {model}")
    
    def get_system_prompt(self) -> str:
        """Get the system prompt for the travel assistant"""
        return """You are a helpful travel planning assistant specializing in Jaipur, India.

**CRITICAL FUNCTION CALLING INSTRUCTIONS:**
You MUST use the function calling tools provided. DO NOT respond with text-only answers when tools are available.

**WHEN TO USE TOOLS:**
- When user asks about planning a trip → ALWAYS use search_pois and build_itinerary
- When user asks questions about Jaipur → ALWAYS use retrieve_city_guidance first
- When you need more information → Use ask_clarifying_question

**HOW TO USE TOOLS:**
- Use the standard function calling API provided by the system
- The system will automatically execute the functions for you
- DO NOT write function calls as text (e.g., retrieve_city_guidance(query="..."))
- DO NOT write function calls in XML format (e.g., <function=name>...</function>)
- DO NOT write function calls in any text format
- You MUST use the tool calling API - the system will handle execution automatically
- If you write function calls as text, they will NOT be executed

**Available tools:**
1. search_pois - Search for points of interest in Jaipur (USE THIS for finding attractions)
2. build_itinerary - Build a structured day-wise itinerary (USE THIS after getting POIs)
3. retrieve_city_guidance - Get factual information about Jaipur (USE THIS for questions)
4. ask_clarifying_question - Ask the user for missing information (USE THIS when needed)

**WORKFLOW FOR ITINERARY CREATION:**
When user asks to plan a trip:
1. IMMEDIATELY call search_pois with their interests
   - Use max_results=20 or more to get enough POIs for a multi-day trip
   - Include a variety of POIs: morning attractions, afternoon sites, and evening activities (restaurants, markets, cultural shows, etc.)
2. Then call build_itinerary with ALL or MOST POI objects from search_pois results
   - CRITICAL: Pass MANY POI objects (at least 8-10 for 2-day trip, 12-15 for 3-day trip)
   - IMPORTANT: Include evening activities! Pass POIs suitable for evening (restaurants, markets, cultural venues, night views)
   - DO NOT pass just 2-3 POIs - pass as many as possible from search_pois results
   - Pass the COMPLETE POI objects (with id, name, location, visit_duration_minutes, distance_km, category)
   - DO NOT pass just {"id": 1} or incomplete data
   - The build_itinerary function will intelligently select and schedule the best POIs across morning, afternoon, AND evening
   - For relaxed pace: pass at least 8-10 POIs for 2 days (to ensure morning, afternoon, and evening activities)
   - For moderate pace: pass at least 10-12 POIs for 2 days
   - For packed pace: pass at least 15-18 POIs for 2 days
3. Present the itinerary to the user
   - The itinerary should include activities for morning, afternoon, AND evening for each day

**WORKFLOW FOR ITINERARY EDITS (CRITICAL):**
When user asks to edit/modify/remove/change activities (e.g., "remove Day 1 morning plan", "change Day 2 activity"):
1. CRITICAL: You MUST call build_itinerary again with the edited POI list
2. DO NOT just respond with text - you MUST call build_itinerary to update the structured itinerary
3. Steps for edits:
   a. Get the current itinerary from conversation context (it was previously built)
   b. For removals: Remove the specified activities from candidate_pois, then call build_itinerary
   c. For additions: Search for new POIs if needed, combine with existing, then call build_itinerary
   d. For changes: Modify the POI list accordingly, then call build_itinerary
4. ALWAYS call build_itinerary after ANY edit request - this is REQUIRED for the UI to update
5. If you only respond with text without calling build_itinerary, the UI will NOT show the changes

**For questions about Jaipur:**
- ALWAYS call retrieve_city_guidance first - never make up information
- Use the retrieved information to answer

**IMPORTANT:** If tools are available, you MUST use them. Do not provide text-only responses when you should be calling functions."""
    
    def _clean_messages(self, messages: List[Dict]) -> List[Dict]:
        """
        Clean messages to ensure they're in the correct format for Cerebras
        
        Cerebras API expects tool messages in a nested format:
        {
            "role": "tool",
            "tool": {
                "tool_call_id": "...",
                "name": "...",
                "content": "..."
            }
        }
        """
        cleaned = []
        for i, msg in enumerate(messages):
            role = msg.get("role", "")
            content = msg.get("content")
            tool_calls = msg.get("tool_calls")
            
            # Handle tool role messages - Cerebras expects FLAT format (not nested!)
            # Format: {"role": "tool", "tool_call_id": "...", "content": "..."}
            if role == "tool":
                # Extract values - check both nested (if coming from our code) and top-level (standard format)
                tool_obj = msg.get("tool", {})
                tool_call_id = msg.get("tool_call_id") or tool_obj.get("tool_call_id")
                name = msg.get("name") or tool_obj.get("name", "")
                content = msg.get("content") or tool_obj.get("content")
                
                # Log the raw message for debugging
                logger.info(f"Cerebras: Processing tool message {i}: tool_call_id={tool_call_id}, name={name}, content_type={type(content)}")
                
                # Validate required fields
                if not tool_call_id:
                    logger.error(f"❌ Tool message {i} missing tool_call_id, skipping. Message keys: {list(msg.keys())}")
                    continue
                
                # Ensure content is a non-empty string (Cerebras requires it)
                if content is None:
                    logger.warning(f"⚠️  Tool message {i} has None content, using empty JSON object")
                    content = "{}"
                elif content == "":
                    logger.warning(f"⚠️  Tool message {i} has empty string content, using empty JSON object")
                    content = "{}"
                elif not isinstance(content, str):
                    # Convert to JSON string if it's not already a string
                    try:
                        content = json.dumps(content) if content else "{}"
                    except (TypeError, ValueError):
                        content = str(content) if content else "{}"
                
                # Ensure tool_call_id is a string
                tool_call_id_str = str(tool_call_id).strip() if tool_call_id else ""
                if not tool_call_id_str:
                    logger.error(f"❌ Tool message {i} has empty tool_call_id after conversion, skipping")
                    continue
                
                # Cerebras expects FLAT structure: role, tool_call_id, and content at top level
                cleaned_msg = {
                    "role": "tool",
                    "tool_call_id": tool_call_id_str,
                    "content": str(content)
                }
                
                # Add name if provided (optional field)
                if name:
                    cleaned_msg["name"] = str(name)
                
                logger.info(f"✅ Cerebras: Converted tool message {i} - tool_call_id: {tool_call_id_str[:20]}..., content_length: {len(str(content))}")
                cleaned.append(cleaned_msg)
                continue
            
            # Skip empty messages (except system messages)
            if not content and not tool_calls and role != "system":
                continue
            
            cleaned_msg = {
                "role": role,
                "content": content if content else None
            }
            
            # Add tool_calls if present (for assistant messages)
            if tool_calls:
                cleaned_msg["tool_calls"] = tool_calls
            
            # Note: We intentionally don't copy 'timestamp' or other unsupported fields
            # Cerebras API doesn't support timestamp in messages
            
            cleaned.append(cleaned_msg)
        
        return cleaned
    
    def _extract_tool_calls_from_text(self, content: str, tools: Optional[List[Dict]] = None) -> List[Dict]:
        """
        Extract function calls from text content when Cerebras returns them as text instead of tool_calls.
        Similar to Groq's post-processing logic.
        
        Returns list of tool call dicts in format: [{"id": "...", "type": "function", "function": {"name": "...", "arguments": "..."}}]
        """
        if not content or not tools:
            return []
        
        tool_calls = []
        tool_names = [t.get('function', {}).get('name', '') for t in tools]
        
        # Pattern 1: function_name({json}) format
        # Example: retrieve_city_guidance(query="Jaipur cultural trip", top_k=5)
        pattern1 = rf'\b({"|".join(re.escape(name) for name in tool_names)})\s*\(\s*{{'
        for match in re.finditer(pattern1, content):
            func_name = match.group(1)
            start_pos = match.end() - 1  # Position of opening brace
            
            # Extract JSON by finding balanced braces
            brace_count = 0
            json_str = ""
            for i in range(start_pos, len(content)):
                char = content[i]
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                
                json_str += char
                
                if brace_count == 0:
                    # Check if next is closing paren
                    remaining = content[i+1:].strip()
                    if remaining.startswith(')'):
                        try:
                            func_args = json.loads(json_str)
                            tool_calls.append({
                                "id": f"call_extracted_{len(tool_calls)}",
                                "type": "function",
                                "function": {
                                    "name": func_name,
                                    "arguments": json_str
                                }
                            })
                            logger.info(f"   ✅ Extracted {func_name} from text (parentheses format)")
                        except json.JSONDecodeError:
                            logger.warning(f"   Failed to parse JSON for {func_name}")
                    break
        
        # Pattern 2: function_name{json} format (no parentheses)
        # Example: search_pois{"interests": ["culture"]}
        pattern2 = rf'\b({"|".join(re.escape(name) for name in tool_names)})\s*{{'
        for match in re.finditer(pattern2, content):
            func_name = match.group(1)
            start_pos = match.end() - 1
            
            # Extract JSON by finding balanced braces
            brace_count = 0
            json_str = ""
            for i in range(start_pos, len(content)):
                char = content[i]
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                
                json_str += char
                
                if brace_count == 0:
                    try:
                        func_args = json.loads(json_str)
                        # Check if this tool call was already added (avoid duplicates)
                        already_added = False
                        for tc in tool_calls:
                            if (tc.get("function", {}).get("name") == func_name and 
                                tc.get("function", {}).get("arguments", "") == json_str):
                                already_added = True
                                break
                        
                        if not already_added:
                            tool_calls.append({
                                "id": f"call_extracted_{len(tool_calls)}",
                                "type": "function",
                                "function": {
                                    "name": func_name,
                                    "arguments": json_str
                                }
                            })
                            logger.info(f"   ✅ Extracted {func_name} from text (no parentheses format)")
                    except json.JSONDecodeError:
                        logger.warning(f"   Failed to parse JSON for {func_name}")
                    break
        
        # Pattern 3: Python-style function calls with keyword arguments
        # Example: retrieve_city_guidance(query="Jaipur cultural trip", top_k=5)
        pattern3 = rf'\b({"|".join(re.escape(name) for name in tool_names)})\s*\('
        for match in re.finditer(pattern3, content):
            func_name = match.group(1)
            start_pos = match.end()  # Position after opening paren
            
            # Extract arguments by finding balanced parentheses
            paren_count = 1
            args_str = ""
            for i in range(start_pos, len(content)):
                char = content[i]
                if char == '(':
                    paren_count += 1
                elif char == ')':
                    paren_count -= 1
                
                if paren_count == 0:
                    # Found closing paren
                    args_str = content[start_pos:i].strip()
                    break
                elif paren_count > 0:
                    args_str += char
            
            if args_str:
                try:
                    # Convert Python kwargs to JSON
                    # Handle: query="value", top_k=5 -> {"query": "value", "top_k": 5}
                    import ast
                    # Try to parse as Python literal (handles strings, numbers, etc.)
                    # For kwargs, we need to construct a dict
                    kwargs_dict = {}
                    # Split by comma, but respect quoted strings
                    parts = []
                    current = ""
                    in_quotes = False
                    quote_char = None
                    for char in args_str:
                        if char in ['"', "'"] and (not current or current[-1] != '\\'):
                            if not in_quotes:
                                in_quotes = True
                                quote_char = char
                            elif char == quote_char:
                                in_quotes = False
                                quote_char = None
                        elif char == ',' and not in_quotes:
                            if current.strip():
                                parts.append(current.strip())
                            current = ""
                            continue
                        current += char
                    if current.strip():
                        parts.append(current.strip())
                    
                    # Parse each part as key=value
                    for part in parts:
                        if '=' in part:
                            key, value = part.split('=', 1)
                            key = key.strip()
                            value = value.strip()
                            # Remove quotes from value
                            if value.startswith('"') and value.endswith('"'):
                                value = value[1:-1]
                            elif value.startswith("'") and value.endswith("'"):
                                value = value[1:-1]
                            # Try to convert to number if possible
                            try:
                                if '.' in value:
                                    value = float(value)
                                else:
                                    value = int(value)
                            except ValueError:
                                pass
                            kwargs_dict[key] = value
                    
                    if kwargs_dict:
                        json_str = json.dumps(kwargs_dict)
                        # Check for duplicates
                        already_added = False
                        for tc in tool_calls:
                            if (tc.get("function", {}).get("name") == func_name and 
                                tc.get("function", {}).get("arguments", "") == json_str):
                                already_added = True
                                break
                        
                        if not already_added:
                            tool_calls.append({
                                "id": f"call_extracted_{len(tool_calls)}",
                                "type": "function",
                                "function": {
                                    "name": func_name,
                                    "arguments": json_str
                                }
                            })
                            logger.info(f"   ✅ Extracted {func_name} from text (Python kwargs format)")
                except Exception as e:
                    logger.debug(f"   Failed to parse Python kwargs for {func_name}: {e}")
        
        return tool_calls
    
    def chat_completion(self, messages: List[Dict], tools: Optional[List[Dict]] = None,
                       tool_choice: str = "auto", temperature: float = 0.7) -> Dict:
        """
        Make a chat completion request to Cerebras
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            tools: List of function definitions (for function calling)
            tool_choice: "auto", "none", or {"type": "function", "function": {"name": "..."}}
            temperature: Sampling temperature (0-2)
        
        Returns:
            Response dict with message and tool_calls
        """
        try:
            # Clean messages
            cleaned_messages = self._clean_messages(messages)
            
            # Log request
            logger.info(f"Cerebras request: {len(cleaned_messages)} messages, {len(tools) if tools else 0} tools")
            if tools:
                tool_names = [t.get('function', {}).get('name', 'unknown') for t in tools]
                logger.info(f"   Tool names: {tool_names}")
            
            # Final validation and fixing: Ensure all tool messages have required fields BEFORE creating payload
            tool_message_indices = []
            for i, msg in enumerate(cleaned_messages):
                if msg.get("role") == "tool":
                    tool_message_indices.append(i)
                    tool_obj = msg.get("tool")
                    
                    # Check if tool object exists and has required fields
                    needs_fix = False
                    if not tool_obj:
                        logger.error(f"❌ Tool message {i} missing 'tool' object entirely! Message keys: {list(msg.keys())}")
                        needs_fix = True
                        tool_obj = {}
                    else:
                        # Check required fields
                        if not tool_obj.get("tool_call_id"):
                            logger.error(f"❌ Tool message {i} missing tool_call_id in tool object")
                            needs_fix = True
                        if not tool_obj.get("content"):
                            logger.error(f"❌ Tool message {i} missing content in tool object")
                            needs_fix = True
                    
                    # Fix the message if needed
                    if needs_fix or not tool_obj:
                        # Get values from top-level or nested object
                        tool_call_id = tool_obj.get("tool_call_id") or msg.get("tool_call_id")
                        name = tool_obj.get("name") or msg.get("name", "")
                        content = tool_obj.get("content") or msg.get("content", "{}")
                        
                        if not tool_call_id:
                            logger.error(f"❌ Cannot fix tool message {i} - no tool_call_id found anywhere. Removing message.")
                            # Mark for removal
                            cleaned_messages[i] = None
                            continue
                        
                        # Ensure content is a string
                        if not content or content == "":
                            content = "{}"
                        elif not isinstance(content, str):
                            try:
                                content = json.dumps(content) if content else "{}"
                            except:
                                content = str(content) if content else "{}"
                        
                        # Recreate the message with proper structure
                        cleaned_messages[i] = {
                            "role": "tool",
                            "tool": {
                                "tool_call_id": str(tool_call_id),
                                "name": str(name) if name else "",
                                "content": str(content)
                            }
                        }
                        logger.warning(f"⚠️  Fixed tool message {i} - tool_call_id: {str(tool_call_id)[:20]}..., content_length: {len(str(content))}")
            
            # Remove any None messages (invalid ones we couldn't fix)
            cleaned_messages = [msg for msg in cleaned_messages if msg is not None]
            
            # CRITICAL: Completely rebuild ALL tool messages from cleaned_messages BEFORE creating payload
            # Cerebras expects FLAT structure: {"role": "tool", "tool_call_id": "...", "content": "..."}
            final_messages = []
            for i, msg in enumerate(cleaned_messages):
                if msg.get("role") == "tool":
                    # Extract values - handle both nested (from our code) and flat (standard) formats
                    tool_obj = msg.get("tool", {})
                    tool_call_id = msg.get("tool_call_id") or tool_obj.get("tool_call_id")
                    name = msg.get("name") or tool_obj.get("name", "")
                    content = msg.get("content") or tool_obj.get("content", "{}")
                    
                    # Ensure all are strings and non-empty
                    tool_call_id = str(tool_call_id).strip() if tool_call_id else ""
                    name = str(name).strip() if name else ""
                    content = str(content).strip() if content else "{}"
                    
                    if not tool_call_id:
                        logger.error(f"❌ CRITICAL: Message {i} has empty tool_call_id after all processing! Skipping.")
                        continue
                    
                    # Recreate with FLAT structure (Cerebras format)
                    final_msg = {
                        "role": "tool",
                        "tool_call_id": tool_call_id,
                        "content": content
                    }
                    
                    # Add name if provided (optional)
                    if name:
                        final_msg["name"] = name
                    
                    # Verify the structure
                    if "tool_call_id" not in final_msg:
                        logger.error(f"❌ CRITICAL: Recreated message {i} missing 'tool_call_id' key!")
                    elif not final_msg.get("tool_call_id"):
                        logger.error(f"❌ CRITICAL: Recreated message {i} has empty tool_call_id!")
                    elif "content" not in final_msg:
                        logger.error(f"❌ CRITICAL: Recreated message {i} missing 'content' key!")
                    elif not final_msg.get("content"):
                        logger.error(f"❌ CRITICAL: Recreated message {i} has empty content!")
                    else:
                        logger.info(f"✅ Recreated tool message {i}: tool_call_id={tool_call_id[:20]}..., content_len={len(content)}")
                    
                    final_messages.append(final_msg)
                else:
                    # Non-tool messages - keep as-is
                    final_messages.append(msg)
            
            # NOW build request payload with rebuilt messages
            payload = {
                "model": self.model,
                "messages": final_messages,
                "temperature": temperature
            }
            
            # Add tools if provided
            if tools:
                # Verify tools format is correct (OpenAI-compatible)
                # Format should be: [{"type": "function", "function": {"name": "...", "description": "...", "parameters": {...}}}]
                validated_tools = []
                for tool in tools:
                    if isinstance(tool, dict):
                        # Ensure it has the correct structure
                        if tool.get("type") == "function" and tool.get("function"):
                            validated_tools.append(tool)
                        else:
                            logger.warning(f"⚠️  Invalid tool format: {list(tool.keys())}, skipping")
                    else:
                        logger.warning(f"⚠️  Tool is not a dict: {type(tool)}, skipping")
                
                if validated_tools:
                    payload["tools"] = validated_tools
                    # Log tools structure for debugging
                    logger.info(f"Cerebras: Tools structure - {len(validated_tools)} validated tools")
                    if validated_tools:
                        first_tool = validated_tools[0]
                        func_info = first_tool.get('function', {})
                        logger.debug(f"   First tool: type={first_tool.get('type')}, name={func_info.get('name', 'N/A')}, has_params={bool(func_info.get('parameters'))}")
                    
                    # Handle tool_choice
                    if tool_choice == "none":
                        payload["tool_choice"] = "none"
                        logger.debug(f"   tool_choice: none (tools disabled)")
                    elif isinstance(tool_choice, dict) and tool_choice.get("type") == "function":
                        payload["tool_choice"] = tool_choice
                        logger.debug(f"   tool_choice: specific function {tool_choice.get('function', {}).get('name', 'unknown')}")
                    else:
                        # For "auto", explicitly set it to encourage tool usage
                        # Some Cerebras models may need explicit "auto" to trigger tool calls
                        payload["tool_choice"] = "auto"
                        logger.debug(f"   tool_choice: auto (model should use tools when appropriate)")
                else:
                    logger.error(f"❌ No valid tools after validation! Original tools: {len(tools)}")
            else:
                logger.debug(f"   No tools provided")
            
            # Final verification: Check what we're actually sending
            tool_count = 0
            for i, msg in enumerate(payload["messages"]):
                if msg.get("role") == "tool":
                    tool_count += 1
                    # Cerebras uses FLAT structure, not nested
                    tool_call_id = msg.get("tool_call_id")
                    content = msg.get("content")
                    if not tool_call_id:
                        logger.error(f"❌ CRITICAL FINAL: Message {i} missing 'tool_call_id'! Full msg: {json.dumps(msg)}")
                    elif not content:
                        logger.error(f"❌ CRITICAL FINAL: Message {i} missing 'content'! Full msg: {json.dumps(msg)}")
                    else:
                        logger.info(f"✅ FINAL VERIFIED message {i}: tool_call_id={str(tool_call_id)[:20]}..., content_len={len(str(content))}")
            
            logger.info(f"Cerebras: Final payload has {tool_count} tool messages, {len(payload['messages'])} total messages")
            
            # CRITICAL: Serialize to JSON and verify structure one more time
            try:
                payload_json_str = json.dumps(payload)
                payload_verified = json.loads(payload_json_str)
                
                # Check tool messages in serialized form (Cerebras uses FLAT format)
                for i, msg in enumerate(payload_verified.get("messages", [])):
                    if msg.get("role") == "tool":
                        tool_call_id = msg.get("tool_call_id")
                        content = msg.get("content")
                        if not tool_call_id:
                            logger.error(f"❌ SERIALIZATION CHECK: Message {i} lost 'tool_call_id' after JSON serialization!")
                            logger.error(f"   Message after serialization: {json.dumps(msg, indent=2)}")
                        elif not content:
                            logger.error(f"❌ SERIALIZATION CHECK: Message {i} lost 'content' after JSON serialization!")
                        else:
                            logger.info(f"✅ SERIALIZATION CHECK: Message {i} structure intact after JSON serialization")
                
                # Use verified payload
                payload = payload_verified
            except Exception as e:
                logger.error(f"❌ Error in serialization check: {e}")
                # Continue with original payload
            
            # Make API request
            url = f"{self.base_url}/chat/completions"
            logger.debug(f"Cerebras: Sending request with {len(payload['messages'])} messages")
            
            # Log actual JSON being sent (for debugging)
            try:
                json_to_send = json.dumps(payload)
                # Extract just tool messages for logging (Cerebras uses FLAT format)
                tool_msgs_json = []
                for msg in payload.get("messages", []):
                    if msg.get("role") == "tool":
                        tool_msgs_json.append({
                            "role": msg.get("role"),
                            "has_tool_call_id": "tool_call_id" in msg,
                            "tool_call_id": str(msg.get("tool_call_id", "MISSING"))[:30],
                            "has_content": "content" in msg,
                            "content_len": len(str(msg.get("content", "")))
                        })
                logger.info(f"Cerebras: Tool messages in JSON payload: {json.dumps(tool_msgs_json, indent=2)}")
                
                # Log tools being sent
                if payload.get("tools"):
                    tools_summary = []
                    for tool in payload.get("tools", []):
                        func_info = tool.get("function", {})
                        tools_summary.append({
                            "type": tool.get("type"),
                            "name": func_info.get("name", "N/A"),
                            "has_params": bool(func_info.get("parameters"))
                        })
                    logger.info(f"Cerebras: Tools in payload: {json.dumps(tools_summary, indent=2)}")
                    logger.debug(f"Cerebras: tool_choice={payload.get('tool_choice', 'not set')}")
            except Exception as e:
                logger.warning(f"Could not log payload structure: {e}")
            
            try:
                response = requests.post(
                    url,
                    headers=self.headers,
                    json=payload,
                    timeout=60
                )
            except requests.exceptions.ConnectionError as e:
                # Handle DNS resolution failures and connection errors
                error_str = str(e)
                if "getaddrinfo failed" in error_str or "NameResolutionError" in error_str:
                    logger.error(f"❌ DNS Resolution Error: Cannot resolve '{self.base_url}'. Please check:")
                    logger.error(f"   1. Your internet connection")
                    logger.error(f"   2. The CEREBRAS_BASE_URL in your .env file (currently: {self.base_url})")
                    logger.error(f"   3. If the Cerebras API endpoint has changed")
                    raise Exception(f"Cerebras API DNS resolution failed: Cannot resolve '{self.base_url}'. Check your network connection and API endpoint URL.")
                else:
                    raise Exception(f"Cerebras API connection error: {e}")
            except requests.exceptions.Timeout as e:
                logger.error(f"❌ Cerebras API request timeout after 60 seconds")
                raise Exception(f"Cerebras API request timeout: {e}")
            except requests.exceptions.RequestException as e:
                logger.error(f"❌ Cerebras API request error: {e}")
                raise Exception(f"Cerebras API request error: {e}")
            
            # Check for errors
            if response.status_code != 200:
                error_data = response.json() if response.content else {}
                error_msg = error_data.get("error", {}).get("message", response.text) or error_data.get("message", response.text)
                error_code = error_data.get("error", {}).get("code", str(response.status_code))
                error_type = error_data.get("error", {}).get("type") or error_data.get("type", "unknown")
                
                # Check for server errors (503, 502, 504) - these are temporary and should be retried
                if response.status_code in [502, 503, 504]:
                    error_detail = f"Server error ({response.status_code}): {error_msg}"
                    if error_type:
                        error_detail += f" (type: {error_type})"
                    logger.warning(f"⚠️  Cerebras API server error ({response.status_code}): {error_msg}")
                    logger.info(f"   This is a temporary server issue. The request will be retried or fallback will be used.")
                    raise Exception(f"Cerebras API error ({response.status_code}): {error_detail}")
                
                # Check for rate limit
                if response.status_code == 429:
                    retry_after = response.headers.get("Retry-After", "unknown")
                    raise Exception(f"Cerebras API rate limit reached (429). Retry after: {retry_after}")
                
                # Check for tool_use_failed errors - extract function calls from Python code format
                if "tool_use_failed" in error_msg.lower() or error_code == "tool_use_failed":
                    logger.warning("⚠️  Cerebras tool calling failed - model generated function calls as Python code")
                    logger.info("   Attempting to extract function calls from error message...")
                    
                    # Extract failed_generation from error
                    failed_gen = None
                    failed_gen_data = error_data.get("error", {}).get("failed_generation")
                    if failed_gen_data:
                        failed_gen = failed_gen_data
                    else:
                        # Try to extract from error message string
                        failed_match = re.search(r"'failed_generation':\s*'([^']+)'", error_msg)
                        if failed_match:
                            failed_gen = failed_match.group(1)
                        else:
                            failed_match = re.search(r'"failed_generation":\s*"([^"]+)"', error_msg)
                            if failed_match:
                                failed_gen = failed_match.group(1)
                    
                    if failed_gen:
                        logger.info(f"   Extracted failed_generation: {failed_gen[:200]}...")
                        tool_calls = []
                        
                        # First, try to parse as JSON format (Cerebras sometimes returns JSON)
                        try:
                            # failed_gen might be a JSON string or already parsed dict
                            failed_gen_parsed = None
                            if isinstance(failed_gen, str):
                                # Try parsing as JSON first
                                try:
                                    failed_gen_parsed = json.loads(failed_gen)
                                except json.JSONDecodeError:
                                    # Not JSON, will try Python format later
                                    pass
                            elif isinstance(failed_gen, dict):
                                # Already parsed
                                failed_gen_parsed = failed_gen
                            
                            if failed_gen_parsed:
                                # Handle single tool call (dict format)
                                if isinstance(failed_gen_parsed, dict):
                                    func_name = failed_gen_parsed.get("name")
                                    func_args_str = failed_gen_parsed.get("arguments")
                                    
                                    if func_name and func_args_str:
                                        # Parse the arguments (which is itself a JSON string)
                                        try:
                                            if isinstance(func_args_str, str):
                                                func_args = json.loads(func_args_str)
                                            else:
                                                func_args = func_args_str
                                            
                                            # Validate function name is in our tools
                                            if tools:
                                                tool_names = [t.get('function', {}).get('name', '') for t in tools]
                                                if func_name in tool_names:
                                                    tool_call_id = f"call_cerebras_{len(tool_calls)}"
                                                    func_obj = type('Function', (), {
                                                        'name': func_name,
                                                        'arguments': json.dumps(func_args)
                                                    })()
                                                    
                                                    tool_call_obj = type('ToolCall', (), {
                                                        'id': tool_call_id,
                                                        'type': 'function',
                                                        'function': func_obj
                                                    })()
                                                    
                                                    tool_calls.append(tool_call_obj)
                                                    logger.info(f"   ✅ Extracted function call from JSON: {func_name} with {len(func_args)} arguments")
                                                else:
                                                    logger.warning(f"   Function '{func_name}' not in available tools, skipping")
                                            else:
                                                logger.warning("   No tools available for validation")
                                        except json.JSONDecodeError as e:
                                            logger.warning(f"   Failed to parse arguments JSON for {func_name}: {e}")
                                
                                # Handle multiple tool calls (list format)
                                elif isinstance(failed_gen_parsed, list):
                                    for tc_data in failed_gen_parsed:
                                        if isinstance(tc_data, dict):
                                            func_name = tc_data.get("name")
                                            func_args_str = tc_data.get("arguments")
                                            if func_name and func_args_str:
                                                try:
                                                    if isinstance(func_args_str, str):
                                                        func_args = json.loads(func_args_str)
                                                    else:
                                                        func_args = func_args_str
                                                    
                                                    if tools:
                                                        tool_names = [t.get('function', {}).get('name', '') for t in tools]
                                                        if func_name in tool_names:
                                                            tool_call_id = f"call_cerebras_{len(tool_calls)}"
                                                            func_obj = type('Function', (), {
                                                                'name': func_name,
                                                                'arguments': json.dumps(func_args)
                                                            })()
                                                            
                                                            tool_call_obj = type('ToolCall', (), {
                                                                'id': tool_call_id,
                                                                'type': 'function',
                                                                'function': func_obj
                                                            })()
                                                            
                                                            tool_calls.append(tool_call_obj)
                                                            logger.info(f"   ✅ Extracted function call from JSON list: {func_name}")
                                                except json.JSONDecodeError as e:
                                                    logger.warning(f"   Failed to parse arguments for {func_name}: {e}")
                        except Exception as json_parse_error:
                            logger.debug(f"   JSON parsing failed: {json_parse_error}, will try Python format...")
                        except Exception as e:
                            logger.debug(f"   JSON parsing attempt failed: {e}, trying Python format...")
                        
                        # If no tool calls extracted from JSON, try Python format
                        if not tool_calls:
                            # Parse function calls from Python format: function_name(arg1=value1, arg2=value2)
                            # Handle multiple function calls separated by newlines
                            lines = failed_gen.split('\n') if isinstance(failed_gen, str) else [str(failed_gen)]
                            
                            for line in lines:
                                line = line.strip()
                                if not line:
                                    continue
                                
                                # Match function call pattern: function_name(...)
                                func_match = re.match(r'(\w+)\s*\((.*)\)', line)
                                if func_match:
                                    func_name = func_match.group(1)
                                    args_str = func_match.group(2)
                                    
                                    # Skip if it contains list comprehensions (can't parse those)
                                    if '[' in args_str and 'for' in args_str and 'in' in args_str:
                                        logger.warning(f"   Skipping {func_name} - contains list comprehension (cannot parse)")
                                        continue
                                    
                                    # Try to parse arguments as Python dict/kwargs
                                    try:
                                        # Check if args contain list comprehensions or function calls (too complex to parse)
                                        if 'for' in args_str and 'in' in args_str:
                                            logger.warning(f"   Skipping {func_name} - arguments contain list comprehensions: {args_str[:100]}")
                                            # For build_itinerary with list comp, we'll skip it and let it be called after search_pois completes
                                            continue
                                        
                                        # Convert Python dict syntax to JSON
                                        # Replace single quotes with double quotes, handle None -> null
                                        args_json_str = args_str.replace("'", '"').replace('None', 'null').replace('True', 'true').replace('False', 'false')
                                        
                                        # Try to parse as JSON (might need to wrap in braces)
                                        try:
                                            if args_json_str.strip().startswith('{'):
                                                func_args = json.loads(args_json_str)
                                            else:
                                                # Try wrapping in braces for kwargs format
                                                func_args = json.loads('{' + args_json_str + '}')
                                        except json.JSONDecodeError:
                                            # If JSON parsing fails, try ast.literal_eval for safe Python literal parsing
                                            try:
                                                import ast
                                                # Parse as Python literal (handles dicts, lists, strings, etc.)
                                                parsed = ast.literal_eval('{' + args_str + '}')
                                                # Convert to JSON-serializable format
                                                func_args = json.loads(json.dumps(parsed))
                                            except:
                                                logger.warning(f"   Cannot parse arguments for {func_name}: {args_str[:100]}")
                                                continue
                                        
                                        # Validate function name is in our tools
                                        if tools:
                                            tool_names = [t.get('function', {}).get('name', '') for t in tools]
                                            if func_name not in tool_names:
                                                logger.warning(f"   Function '{func_name}' not in available tools, skipping")
                                                continue
                                        
                                        # Create tool call object
                                        tool_call_id = f"call_cerebras_{len(tool_calls)}"
                                        func_obj = type('Function', (), {
                                            'name': func_name,
                                            'arguments': json.dumps(func_args)
                                        })()
                                        
                                        tool_call_obj = type('ToolCall', (), {
                                            'id': tool_call_id,
                                            'type': 'function',
                                            'function': func_obj
                                        })()
                                        
                                        tool_calls.append(tool_call_obj)
                                        logger.info(f"   ✅ Extracted function call: {func_name} with {len(func_args)} arguments")
                                        
                                    except Exception as parse_error:
                                        logger.warning(f"   Failed to parse {func_name} arguments: {parse_error}")
                                        continue
                        
                        if tool_calls:
                            logger.info(f"   ✅ Successfully extracted {len(tool_calls)} tool call(s) from error")
                            # Create message object with extracted tool calls
                            message_obj = type('Message', (), {
                                'content': None,
                                'tool_calls': tool_calls
                            })()
                            
                            usage_obj = type('Usage', (), {
                                'prompt_tokens': 0,
                                'completion_tokens': 0,
                                'total_tokens': 0
                            })()
                            
                            return {
                                "message": message_obj,
                                "usage": usage_obj,
                                "model": self.model
                            }
                        else:
                            logger.warning("   Could not extract any valid function calls from failed_generation")
                
                # Format error message with all available details
                error_detail = f"{error_msg}"
                if error_code and error_code != str(response.status_code):
                    error_detail += f" (code: {error_code})"
                if error_type and error_type != "unknown":
                    error_detail += f" (type: {error_type})"
                
                logger.error(f"❌ Cerebras API error ({response.status_code}): {error_detail}")
                raise Exception(f"Cerebras API error ({response.status_code}): {error_detail}")
            
            # Parse response
            data = response.json()
            
            # Log full response structure for debugging
            logger.debug(f"Cerebras response structure: choices={len(data.get('choices', []))}, has_usage={bool(data.get('usage'))}")
            
            # Extract message and tool_calls
            choice = data.get("choices", [{}])[0]
            message_data = choice.get("message", {})
            
            # Log message structure
            logger.debug(f"Cerebras message structure: has_content={bool(message_data.get('content'))}, has_tool_calls={bool(message_data.get('tool_calls'))}, content_preview={str(message_data.get('content', ''))[:100] if message_data.get('content') else 'None'}...")
            
            # Build message object
            message_content = message_data.get("content")
            tool_calls_data = message_data.get("tool_calls", [])
            
            # Log tool calls if present
            if tool_calls_data:
                logger.info(f"✅ Cerebras returned {len(tool_calls_data)} tool call(s)")
                for i, tc in enumerate(tool_calls_data):
                    func_name = tc.get("function", {}).get("name", "unknown")
                    logger.debug(f"   Tool call {i+1}: {func_name}")
            else:
                logger.warning(f"⚠️  Cerebras returned NO tool calls. Message keys: {list(message_data.keys())}")
                if message_content:
                    logger.warning(f"   Response content: {message_content[:200]}...")
                    # Post-process to extract function calls from text (like Groq)
                    logger.info(f"   🔍 Checking if function calls are embedded in text content...")
                    extracted_tool_calls = self._extract_tool_calls_from_text(message_content, tools)
                    if extracted_tool_calls:
                        logger.info(f"   ✅ Extracted {len(extracted_tool_calls)} tool call(s) from text!")
                        tool_calls_data = extracted_tool_calls
                        # Clear content since we have tool calls now
                        message_content = None
            
            # Convert tool_calls to expected format (objects with attributes, not dicts)
            tool_calls = []
            for tc in tool_calls_data:
                # Create function object
                func_obj = type('Function', (), {
                    'name': tc.get("function", {}).get("name", ""),
                    'arguments': tc.get("function", {}).get("arguments", "{}")
                })()
                
                # Create tool call object
                tool_call_obj = type('ToolCall', (), {
                    'id': tc.get("id", ""),
                    'type': tc.get("type", "function"),
                    'function': func_obj
                })()
                
                tool_calls.append(tool_call_obj)
            
            # Create message object (similar to Groq/Gemini format)
            message_obj = type('Message', (), {
                'content': message_content if message_content else None,
                'tool_calls': tool_calls if tool_calls else None
            })()
            
            # Create usage object
            usage_data = data.get("usage", {})
            usage_obj = type('Usage', (), {
                'prompt_tokens': usage_data.get("prompt_tokens", 0),
                'completion_tokens': usage_data.get("completion_tokens", 0),
                'total_tokens': usage_data.get("total_tokens", 0)
            })()
            
            logger.info(f"✅ Cerebras response: {len(tool_calls)} tool calls, {usage_obj.total_tokens} tokens")
            
            return {
                "message": message_obj,
                "usage": usage_obj,
                "model": self.model
            }
            
        except requests.exceptions.RequestException as e:
            error_str = str(e)
            logger.error(f"Cerebras API request error: {error_str}")
            
            # Check for rate limit errors
            if "429" in error_str or "rate limit" in error_str.lower():
                raise Exception(f"Cerebras API rate limit reached. Please wait before trying again.")
            
            raise Exception(f"Cerebras API error: {error_str}")
        except Exception as e:
            error_str = str(e)
            logger.error(f"Cerebras API error: {error_str}")
            raise

