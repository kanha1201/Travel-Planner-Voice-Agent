"""
LLM Orchestrator - Handles LLM calls with function calling
"""

from .llm_client import LLMClient
from .functions import get_function_definitions
from core.session_manager import SessionManager
from core.response_cache import get_cache
from core.tool_cache import get_tool_cache
from typing import Dict, List, Optional
import json
import logging
import hashlib

logger = logging.getLogger(__name__)


class LLMOrchestrator:
    """
    Orchestrates LLM calls with function calling
    Supports Cerebras, Groq, and Gemini providers with automatic fallback
    Fallback chain: Cerebras -> Groq -> Gemini
    """
    
    def __init__(self, provider: Optional[str] = None):
        """
        Initialize LLM Orchestrator
        
        Args:
            provider: "cerebras", "groq", "gemini", or None (auto-detect from LLM_PROVIDER env var)
        """
        self.llm_client = LLMClient(provider=provider)
        self.functions = get_function_definitions()
        self.session_manager = SessionManager()
        # Function handlers (will be registered in Phase 3)
        self.function_handlers = {}
        # Caching
        self.response_cache = get_cache()
        self.tool_cache = get_tool_cache()
        # Tools hash for cache key
        self.tools_hash = hashlib.md5(json.dumps(self.functions, sort_keys=True).encode()).hexdigest()
        logger.info(f"LLM Orchestrator initialized with provider: {self.llm_client.provider}")
        
        # Auto-register handlers if available
        try:
            from tools.register_handlers import register_all_handlers
            register_all_handlers(self)
        except ImportError:
            logger.warning("Could not auto-register function handlers")
    
    def _format_itinerary_summary(self, itinerary: Dict) -> str:
        """
        Format itinerary as a summary string for LLM context
        
        Args:
            itinerary: The itinerary dict with day_1, day_2, etc.
        
        Returns:
            Formatted string summary
        """
        if not itinerary:
            return "No itinerary exists yet."
        
        summary_lines = []
        for day_key in ["day_1", "day_2", "day_3"]:
            if day_key in itinerary and itinerary[day_key]:
                day = itinerary[day_key]
                day_num = day_key.split("_")[1]
                activities = []
                
                for slot in ["morning", "afternoon", "evening"]:
                    slot_activities = day.get(slot, [])
                    if slot_activities:
                        for act in slot_activities:
                            name = act.get("name", "Unknown")
                            time = f"{act.get('start_time', '?')}-{act.get('end_time', '?')}"
                            activities.append(f"  {slot.capitalize()}: {name} ({time})")
                
                if activities:
                    summary_lines.append(f"Day {day_num}:")
                    summary_lines.extend(activities)
                else:
                    summary_lines.append(f"Day {day_num}: No activities")
        
        return "\n".join(summary_lines) if summary_lines else "Empty itinerary"
    
    def register_function_handler(self, function_name: str, handler):
        """Register a function handler"""
        self.function_handlers[function_name] = handler
        logger.info(f"Registered handler for function: {function_name}")
    
    def process_user_request(self, user_message: str, session_id: str) -> Dict:
        """
        Process user request through LLM with function calling
        
        Returns:
            {
                "response": str,
                "tool_calls": List[Dict],
                "session_id": str,
                "usage": Dict
            }
        """
        # Get session
        session = self.session_manager.get_session(session_id)
        if not session:
            session_id = self.session_manager.create_session()
            session = self.session_manager.get_session(session_id)
            logger.info(f"Created new session: {session_id}")
        
        # Build messages
        messages = [
            {"role": "system", "content": self.llm_client.get_system_prompt()}
        ]
        
        # Add conversation history (optimized: reduce to last 10 messages to save tokens)
        # Only include recent context, not full history
        history = self.session_manager.get_conversation_history(session_id, max_messages=10)
        messages.extend(history)
        
        # If provider switched to Groq due to quota, log it
        if self.llm_client.provider == "groq" and hasattr(self.llm_client, '_switched_from_gemini'):
            logger.info("ℹ️  Using Groq (switched from Gemini due to quota)")
        
        # Check if this is an edit request and include current itinerary in context
        is_edit_request = any(keyword in user_message.lower() for keyword in 
                             ['edit', 'change', 'modify', 'remove', 'delete', 'add', 'update', 'cancel'])
        current_itinerary = session.get("current_itinerary") if session else None
        
        if is_edit_request and current_itinerary:
            # Include current itinerary in context so LLM can edit it properly
            itinerary_summary = self._format_itinerary_summary(current_itinerary)
            context_message = f"""Current itinerary structure:
{itinerary_summary}

IMPORTANT: When editing this itinerary, you MUST call build_itinerary again with the updated POI list to ensure the UI reflects the changes."""
            messages.append({"role": "system", "content": context_message})
            logger.info(f"📋 Added current itinerary context for edit request ({len(current_itinerary)} days)")
        
        # Add current user message
        messages.append({"role": "user", "content": user_message})
        
        # Check cache first (only for simple queries without tool calls expected)
        # Skip cache for itinerary creation/editing requests
        is_itinerary_request = any(keyword in user_message.lower() for keyword in 
                                   ['plan', 'itinerary', 'trip', 'day', 'edit', 'change', 'modify'])
        
        if not is_itinerary_request:
            cached_response = self.response_cache.get(messages, self.tools_hash)
            if cached_response:
                logger.info("✅ Using cached response")
                self.session_manager.add_message(session_id, "user", user_message)
                self.session_manager.add_message(session_id, "assistant", cached_response.get("response", ""))
                return {
                    "response": cached_response.get("response", ""),
                    "tool_calls": [],
                    "session_id": session_id,
                    "usage": cached_response.get("usage"),
                    "cached": True
                }
        
        # Track tool calls
        all_tool_calls = []
        max_iterations = 3  # Reduced from 5 to minimize API calls and rate limiting
        iteration = 0
        consecutive_errors = 0  # Track consecutive errors to prevent loops
        last_error_type = None  # Track last error to detect loops
        
        logger.info(f"Processing request for session {session_id}")
        
        while iteration < max_iterations:
            iteration += 1
            logger.info(f"🔄 LLM Iteration {iteration}/{max_iterations}")
            
            # Check for error loop - if same error 2+ times, stop retrying
            if consecutive_errors >= 2:
                logger.error(f"⚠️  Detected error loop (same error {consecutive_errors} times). Stopping retries to prevent rate limiting.")
                break
            
            try:
                # Call LLM (Groq or Gemini)
                logger.info(f"Calling {self.llm_client.provider.upper()} with {len(messages)} messages, {len(self.functions)} tools available")
                
                # #region agent log
                try:
                    msg_details = []
                    for i, m in enumerate(messages[-5:]):  # Last 5 messages
                        msg_info = {"index":len(messages)-5+i,"role":m.get("role")}
                        if m.get("role") == "tool":
                            msg_info["tool_name"] = m.get("name")
                            msg_info["content_length"] = len(m.get("content",""))
                            msg_info["tool_call_id"] = m.get("tool_call_id")
                        elif m.get("role") == "assistant" and m.get("tool_calls"):
                            msg_info["tool_calls"] = [tc.get("function",{}).get("name","unknown") for tc in m.get("tool_calls",[])]
                        msg_details.append(msg_info)
                    with open(r'e:\Tech\Work Folders\Trip Planner Product\.cursor\debug.log', 'a', encoding='utf-8') as f:
                        f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"H2,H3,H4","location":"orchestrator.py:134","message":"About to call LLM","data":{"iteration":iteration,"messages_count":len(messages),"recent_messages":msg_details,"all_tool_calls_so_far":[tc.get("function") for tc in all_tool_calls]},"timestamp":int(__import__('time').time()*1000)}) + '\n')
                except: pass
                # #endregion
                
                # Log last user message for context
                if messages:
                    last_msg = messages[-1]
                    if isinstance(last_msg, dict) and last_msg.get("role") == "user":
                        logger.info(f"   User message: {last_msg.get('content', '')[:100]}...")
                
                response = self.llm_client.chat_completion(
                    messages=messages,
                    tools=self.functions,
                    tool_choice="auto"
                )
                
                message = response["message"]
                
                # Detailed logging of response
                has_tool_calls = bool(message.tool_calls)
                has_content = bool(message.content)
                tool_calls_count = len(message.tool_calls) if message.tool_calls else 0
                content_preview = message.content[:200] if message.content else "(no content)"
                
                logger.info(f"{self.llm_client.provider.upper()} response received:")
                logger.info(f"   - Has tool_calls: {has_tool_calls} (count: {tool_calls_count})")
                logger.info(f"   - Has content: {has_content}")
                logger.info(f"   - Content preview: {content_preview}...")
                
                if message.tool_calls:
                    logger.info(f"   - Tool call details:")
                    for i, tc in enumerate(message.tool_calls):
                        func_name = getattr(tc.function, 'name', 'unknown') if hasattr(tc, 'function') else 'unknown'
                        func_args = getattr(tc.function, 'arguments', '{}') if hasattr(tc, 'function') else '{}'
                        logger.info(f"      [{i+1}] {func_name}: {func_args[:100]}...")
                else:
                    logger.warning(f"   ⚠️  No tool calls in response! LLM returned only text content.")
                    if message.content:
                        logger.warning(f"   Response content: {message.content[:500]}")
                
                # Reset error counter on successful LLM call
                consecutive_errors = 0
                last_error_type = None
                
                # Check if LLM wants to call functions
                if message.tool_calls:
                    logger.info(f"🔧 LLM requested {len(message.tool_calls)} tool call(s)")
                    tool_call_names = [tc.function.name for tc in message.tool_calls]
                    for tc in message.tool_calls:
                        logger.info(f"   - {tc.function.name}")
                    
                    # #region agent log
                    try:
                        with open(r'e:\Tech\Work Folders\Trip Planner Product\.cursor\debug.log', 'a', encoding='utf-8') as f:
                            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"H3","location":"orchestrator.py:179","message":"LLM requested tool calls","data":{"iteration":iteration,"tool_calls":tool_call_names,"previous_tool_calls":[tc.get("function") for tc in all_tool_calls]},"timestamp":int(__import__('time').time()*1000)}) + '\n')
                    except: pass
                    # #endregion
                    
                    # Add assistant message with tool calls
                    messages.append({
                        "role": "assistant",
                        "content": message.content,
                        "tool_calls": [
                            {
                                "id": tc.id,
                                "type": tc.type,
                                "function": {
                                    "name": tc.function.name,
                                    "arguments": tc.function.arguments
                                }
                            }
                            for tc in message.tool_calls
                        ]
                    })
                    
                    # Track if any tool call failed due to parsing
                    parsing_failed = False
                    
                    # Execute each tool call
                    for tool_call in message.tool_calls:
                        function_name = tool_call.function.name
                        try:
                            function_args = json.loads(tool_call.function.arguments)
                            
                            # Validate function_args - if it contains error key, parsing failed
                            if isinstance(function_args, dict) and "error" in function_args:
                                logger.error(f"❌ Function arguments contain error: {function_args.get('error')}. Stopping to prevent retry loop.")
                                parsing_failed = True
                                consecutive_errors += 1
                                last_error_type = "function_args_parse_error"
                                break  # Break out of tool call loop
                            
                        except json.JSONDecodeError as e:
                            logger.error(f"❌ Failed to parse function arguments: {e}. Stopping to prevent retry loop.")
                            function_args = {}
                            parsing_failed = True
                            consecutive_errors += 1
                            last_error_type = "json_decode_error"
                            break  # Break out of tool call loop
                        
                        # If parsing failed, don't continue processing tool calls
                        if parsing_failed:
                            break
                        
                        # Track tool call
                        all_tool_calls.append({
                            "function": function_name,
                            "arguments": function_args
                        })
                        
                        logger.info(f"Executing function: {function_name}")
                        
                        # #region agent log
                        try:
                            with open(r'e:\Tech\Work Folders\Trip Planner Product\.cursor\debug.log', 'a', encoding='utf-8') as f:
                                f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"H1","location":"orchestrator.py:236","message":"About to execute function","data":{"function_name":function_name,"function_args_keys":list(function_args.keys()) if isinstance(function_args,dict) else "not_dict","iteration":iteration},"timestamp":int(__import__('time').time()*1000)}) + '\n')
                        except: pass
                        # #endregion
                        
                        # Check tool cache first
                        cached_result = self.tool_cache.get(function_name, function_args)
                        if cached_result:
                            logger.info(f"✅ Using cached result for {function_name}")
                            result = cached_result
                        elif function_name in self.function_handlers:
                            try:
                                logger.info(f"Executing {function_name} with args: {json.dumps(function_args, indent=2)[:200]}...")
                                result = self.function_handlers[function_name](**function_args)
                                logger.info(f"✅ Function {function_name} executed successfully")
                                
                                # #region agent log
                                try:
                                    result_summary = {"result_type":type(result).__name__,"result_keys":list(result.keys()) if isinstance(result,dict) else "not_dict","result_size":len(str(result))}
                                    if isinstance(result,dict) and "pois" in result:
                                        result_summary["pois_count"] = len(result.get("pois",[]))
                                    with open(r'e:\Tech\Work Folders\Trip Planner Product\.cursor\debug.log', 'a', encoding='utf-8') as f:
                                        f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"H1","location":"orchestrator.py:247","message":"Function executed - result summary","data":{"function_name":function_name,"result":result_summary},"timestamp":int(__import__('time').time()*1000)}) + '\n')
                                except: pass
                                # #endregion
                                
                                # Cache the result (except for build_itinerary which is session-specific)
                                if function_name != "build_itinerary":
                                    self.tool_cache.set(function_name, function_args, result)
                                logger.debug(f"Result keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
                                
                                # Store itinerary in session if build_itinerary was called
                                if function_name == "build_itinerary":
                                    if "itinerary" in result:
                                        session = self.session_manager.get_session(session_id)
                                        if session:
                                            session["current_itinerary"] = result.get("itinerary")
                                            self.session_manager.update_session(session_id, session)
                                            logger.info(f"✅ Stored itinerary in session ({len(result.get('itinerary', {}))} days)")
                                    else:
                                        logger.warning(f"⚠️  build_itinerary result missing 'itinerary' key. Keys: {list(result.keys())}")
                                
                                # Store sources if RAG retrieval was called
                                if function_name == "retrieve_city_guidance":
                                    if "citations" in result:
                                        session = self.session_manager.get_session(session_id)
                                        if session:
                                            if "sources" not in session:
                                                session["sources"] = []
                                            session["sources"].extend(result.get("citations", []))
                                            self.session_manager.update_session(session_id, session)
                                            logger.info(f"✅ Stored {len(result.get('citations', []))} citations in session")
                                    else:
                                        logger.warning(f"⚠️  retrieve_city_guidance result missing 'citations' key. Keys: {list(result.keys())}")
                                
                                # Store sources from POI search results
                                if function_name == "search_pois":
                                    if "pois" in result:
                                        pois = result.get("pois", [])
                                        # Extract unique sources from POIs
                                        seen_urls = set()
                                        poi_sources = []
                                        for poi in pois:
                                            source_name = poi.get("source", "OpenStreetMap")
                                            source_url = poi.get("source_url", "")
                                            
                                            # Skip duplicates by URL
                                            if source_url and source_url in seen_urls:
                                                continue
                                            if source_url:
                                                seen_urls.add(source_url)
                                            
                                            # Create citation format similar to RAG citations
                                            citation = {
                                                "source": source_name,
                                                "url": source_url,
                                                "section": "POI Data",
                                                "section_anchor": ""
                                            }
                                            poi_sources.append(citation)
                                        
                                        if poi_sources:
                                            session = self.session_manager.get_session(session_id)
                                            if session:
                                                if "sources" not in session:
                                                    session["sources"] = []
                                                session["sources"].extend(poi_sources)
                                                self.session_manager.update_session(session_id, session)
                                                logger.info(f"✅ Stored {len(poi_sources)} sources from POI search in session")
                                
                            except Exception as e:
                                logger.error(f"❌ Error executing {function_name}: {e}")
                                import traceback
                                logger.error(f"Traceback:\n{traceback.format_exc()}")
                                result = {"error": str(e), "function": function_name}
                                # Track execution errors
                                consecutive_errors += 1
                                last_error_type = "execution_error"
                        else:
                            logger.error(f"❌ No handler registered for {function_name}")
                            logger.error(f"   Available handlers: {list(self.function_handlers.keys())}")
                            result = {"error": f"Handler not found for {function_name}"}
                            consecutive_errors += 1
                            last_error_type = "handler_not_found"
                        
                        # If parsing failed, don't add tool results and break early
                        if parsing_failed:
                            logger.error(f"⚠️  Skipping tool result addition due to parsing failure. Stopping iteration.")
                            break
                        
                        # Add tool result to messages
                        # Ensure result is JSON serializable and optimize for token usage
                        try:
                            result_json = json.dumps(result)
                            
                            # #region agent log
                            try:
                                with open(r'e:\Tech\Work Folders\Trip Planner Product\.cursor\debug.log', 'a', encoding='utf-8') as f:
                                    f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"H1,H2","location":"orchestrator.py:300","message":"Before truncation","data":{"function_name":function_name,"result_json_length":len(result_json),"result_json_preview":result_json[:500]},"timestamp":int(__import__('time').time()*1000)}) + '\n')
                            except: pass
                            # #endregion
                            
                            # Aggressive truncation to reduce token usage
                            if len(result_json) > 5000:  # Reduced threshold from 10000
                                logger.warning(f"Tool result is large ({len(result_json)} chars), truncating...")
                                result_truncated = json.loads(result_json)
                                
                                # #region agent log
                                try:
                                    with open(r'e:\Tech\Work Folders\Trip Planner Product\.cursor\debug.log', 'a', encoding='utf-8') as f:
                                        f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"H1","location":"orchestrator.py:306","message":"Truncating large result","data":{"function_name":function_name,"original_size":len(result_json)},"timestamp":int(__import__('time').time()*1000)}) + '\n')
                                except: pass
                                # #endregion
                                
                                if isinstance(result_truncated, dict):
                                    # For POI search, aggressively limit and simplify
                                    if "pois" in result_truncated:
                                        pois = result_truncated["pois"]
                                        # Limit to 10 POIs (reduced from 20)
                                        limited_pois = pois[:10]
                                        
                                        # Simplify POI data - remove descriptions, keep only essentials
                                        simplified_pois = []
                                        for poi in limited_pois:
                                            simplified_poi = {
                                                "name": poi.get("name", ""),
                                                "category": poi.get("category", ""),
                                                "type": poi.get("type", ""),
                                                "location": poi.get("location", {}),
                                                "activity_id": poi.get("activity_id", "")
                                            }
                                            # Only include description if very short
                                            if "description" in poi and len(poi.get("description", "")) < 100:
                                                simplified_poi["description"] = poi["description"]
                                            simplified_pois.append(simplified_poi)
                                        
                                        result_truncated["pois"] = simplified_pois
                                        result_truncated["total_found"] = len(pois)  # Keep count
                                        result_truncated["note"] = f"Showing 10 of {len(pois)} POIs. Full details available on request."
                                    
                                    # For other large results, truncate strings
                                    for key, value in result_truncated.items():
                                        if isinstance(value, str) and len(value) > 500:
                                            result_truncated[key] = value[:500] + "... (truncated)"
                                        elif isinstance(value, list) and len(value) > 20:
                                            result_truncated[key] = value[:20]
                                            result_truncated[f"{key}_truncated"] = True
                                
                                result_json = json.dumps(result_truncated)
                                logger.info(f"Truncated tool result from {len(json.dumps(result))} to {len(result_json)} chars")
                                
                        except (TypeError, ValueError) as e:
                            logger.error(f"Error serializing tool result: {e}")
                            result_json = json.dumps({"error": "Failed to serialize result", "function": function_name})
                        
                        tool_result_message = {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "name": function_name,
                            "content": result_json
                        }
                        messages.append(tool_result_message)
                        logger.info(f"✅ Added {function_name} result to messages (size: {len(result_json)} chars)")
                        
                        # #region agent log
                        try:
                            with open(r'e:\Tech\Work Folders\Trip Planner Product\.cursor\debug.log', 'a', encoding='utf-8') as f:
                                f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"H2,H4","location":"orchestrator.py:355","message":"Tool result added to messages","data":{"function_name":function_name,"tool_call_id":tool_call.id,"result_size":len(result_json),"messages_count":len(messages),"last_3_messages_roles":[m.get("role") for m in messages[-3:]]},"timestamp":int(__import__('time').time()*1000)}) + '\n')
                        except: pass
                        # #endregion
                    
                    # If parsing failed, don't continue - break out of iteration loop
                    if parsing_failed:
                        logger.error(f"⚠️  Parsing failed for tool calls. Stopping iterations to prevent rate limiting.")
                        break
                    
                    # Continue loop to get LLM response with tool results
                    logger.info("🔄 Continuing to next iteration with tool results...")
                    
                    # #region agent log
                    try:
                        msg_summary = [{"role":m.get("role"),"has_content":bool(m.get("content")),"has_tool_calls":bool(m.get("tool_calls")),"tool_call_count":len(m.get("tool_calls",[])) if m.get("tool_calls") else 0} for m in messages[-5:]]
                        with open(r'e:\Tech\Work Folders\Trip Planner Product\.cursor\debug.log', 'a', encoding='utf-8') as f:
                            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"H3,H4","location":"orchestrator.py:363","message":"Before next LLM call","data":{"iteration":iteration,"messages_count":len(messages),"recent_messages":msg_summary,"all_tool_calls_so_far":[tc.get("function") for tc in all_tool_calls]},"timestamp":int(__import__('time').time()*1000)}) + '\n')
                    except: pass
                    # #endregion
                    
                    continue
                else:
                    # LLM has final response (no tool calls)
                    final_response = message.content or ""
                    logger.info("✅ LLM generated final response (no tool calls)")
                    
                    # Check if this was an edit request but no build_itinerary was called
                    is_edit_request = any(keyword in user_message.lower() for keyword in 
                                         ['edit', 'change', 'modify', 'remove', 'delete', 'add', 'update'])
                    has_existing_itinerary = session.get("current_itinerary") is not None
                    build_itinerary_called = any(tc.get("function") == "build_itinerary" for tc in all_tool_calls)
                    
                    if is_edit_request and has_existing_itinerary and not build_itinerary_called:
                        logger.warning(f"⚠️  EDIT REQUEST DETECTED but build_itinerary was NOT called!")
                        logger.warning(f"   User message: {user_message[:100]}...")
                        logger.warning(f"   This means the itinerary in the UI will NOT be updated.")
                        logger.warning(f"   The LLM should have called build_itinerary to update the structured itinerary.")
                    
                    logger.warning(f"⚠️  WARNING: LLM returned text response instead of calling tools!")
                    logger.warning(f"   This might indicate:")
                    logger.warning(f"   1. LLM didn't understand it should use tools")
                    logger.warning(f"   2. Tools are not properly configured")
                    logger.warning(f"   3. Rate limiting or API error")
                    logger.info(f"   Response content: {final_response[:500]}...")
                    logger.info(f"   Tool calls made so far: {len(all_tool_calls)}")
                    
                    # Update session
                    self.session_manager.add_message(session_id, "user", user_message)
                    self.session_manager.add_message(session_id, "assistant", final_response)
                    
                    # Extract usage info
                    usage_info = response.get("usage")
                    usage_dict = None
                    if usage_info:
                        usage_dict = {
                            "prompt_tokens": getattr(usage_info, "prompt_tokens", None),
                            "completion_tokens": getattr(usage_info, "completion_tokens", None),
                            "total_tokens": getattr(usage_info, "total_tokens", None)
                        }
                    
                    # Cache the response (if no tool calls were made)
                    if not all_tool_calls and not is_itinerary_request:
                        self.response_cache.set(
                            messages, 
                            {
                                "response": final_response,
                                "usage": usage_dict
                            },
                            self.tools_hash,
                            has_tool_calls=False
                        )
                    
                    return {
                        "response": final_response,
                        "tool_calls": all_tool_calls,
                        "session_id": session_id,
                        "usage": usage_dict
                    }
                    
            except Exception as e:
                logger.error(f"❌ Error in LLM orchestration: {e}")
                import traceback
                error_traceback = traceback.format_exc()
                logger.error(f"Full traceback:\n{error_traceback}")
                
                # Check for rate limit errors
                error_str = str(e)
                if "rate limit" in error_str.lower() or "429" in error_str:
                    user_message = "I've hit the API rate limit. Please wait a bit before trying again, or upgrade your Groq API tier for higher limits."
                else:
                    # Include error in response for debugging
                    error_summary = f"Error: {type(e).__name__}: {str(e)}"
                    user_message = f"I encountered an error processing your request: {error_summary}. Please check server logs for details."
                
                return {
                    "response": user_message,
                    "tool_calls": all_tool_calls,
                    "session_id": session_id,
                    "error": str(e),
                    "error_type": type(e).__name__
                }
        
        # Max iterations reached
        logger.warning(f"⚠️  Max iterations ({max_iterations}) reached for session {session_id}")
        logger.warning(f"   Tool calls made: {len(all_tool_calls)}")
        logger.warning(f"   Last message count: {len(messages)}")
        
        # Try to get a final response even if max iterations reached
        try:
            response = self.llm_client.chat_completion(
                messages=messages,
                tools=self.functions,
                tool_choice="none"  # Force no more tool calls
            )
            final_response = response["message"].content
            logger.info("✅ Got final response after max iterations")
        except Exception as e:
            logger.error(f"Failed to get final response: {e}")
            final_response = "I'm having trouble completing your request. Please try rephrasing or breaking it into smaller parts."
        
        return {
            "response": final_response,
            "tool_calls": all_tool_calls,
            "session_id": session_id,
            "error": "max_iterations_reached"
        }


if __name__ == "__main__":
    # Test orchestrator (without function handlers)
    logging.basicConfig(level=logging.INFO)
    orchestrator = LLMOrchestrator()
    
    session_id = orchestrator.session_manager.create_session()
    
    result = orchestrator.process_user_request(
        "Plan a 2-day cultural trip to Jaipur with a relaxed pace",
        session_id
    )
    
    logger.info(f"Response: {result['response']}")
    logger.info(f"Tool calls: {len(result['tool_calls'])}")

