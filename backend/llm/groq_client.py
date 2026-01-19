"""
Groq LLM client configuration
"""

import groq
from typing import List, Dict, Optional
import os
from dotenv import load_dotenv
import logging
import json
import re

load_dotenv()

logger = logging.getLogger(__name__)


class GroqClient:
    """Groq LLM client wrapper"""
    
    def __init__(self, model: str = "llama-3.3-70b-versatile"):
        """
        Initialize Groq client
        
        Available models:
        - llama-3.3-70b-versatile (default)
        - llama-3.1-70b-versatile
        - llama-3.1-8b-instant (faster, cheaper)
        - mixtral-8x7b-32768
        """
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not found in environment variables. Please set it in .env file.")
        
        # Initialize Groq client
        # The groq package version 0.11.0 should work with standard initialization
        self.client = groq.Groq(api_key=api_key)
        self.model = model
        logger.info(f"✅ Groq client initialized with model: {model}")
    
    def get_system_prompt(self) -> str:
        """Get the system prompt for the travel assistant"""
        return """You are a helpful travel planning assistant specializing in Jaipur, India.

**CRITICAL FUNCTION CALLING INSTRUCTIONS:**
You have access to function calling tools. When you need to use a tool:
- Use the standard function calling API (NOT text format, NOT XML tags, NOT <function=...>)
- The system will automatically call the functions for you
- DO NOT wrap function calls in any tags or text format
- DO NOT write <function=name> or similar XML-like syntax
- Simply use the function calling mechanism provided

Available tools:
1. search_pois - Search for points of interest in Jaipur
2. build_itinerary - Build a structured day-wise itinerary
3. retrieve_city_guidance - Get factual information about Jaipur
4. ask_clarifying_question - Ask the user for missing information

**WORKFLOW FOR ITINERARY CREATION:**
When user asks to plan a trip:
1. Use the search_pois function with their interests
2. Use the build_itinerary function with the results, duration_days, and pace
3. Present the itinerary to the user

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
- Always use retrieve_city_guidance function first
- Never make up information

Your role:
- Understand user preferences
- Generate realistic itineraries
- Explain decisions with citations
- Ask questions when information is missing"""
    
    def chat_completion(self, messages: List[Dict], tools: Optional[List[Dict]] = None,
                       tool_choice: str = "auto", temperature: float = 0.7) -> Dict:
        """
        Make a chat completion request to Groq
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            tools: List of function definitions (for function calling)
            tool_choice: "auto", "none", or {"type": "function", "function": {"name": "..."}}
            temperature: Sampling temperature (0-2)
        
        Returns:
            Response dict with message and tool_calls
        """
        try:
            # Clean messages - ensure tool responses are in correct format
            cleaned_messages = self._clean_messages(messages)
            
            # Log tool configuration
            logger.info(f"Groq request: {len(cleaned_messages)} messages, {len(tools) if tools else 0} tools")
            if tools:
                tool_names = [t.get('function', {}).get('name', 'unknown') for t in tools]
                logger.info(f"   Tool names: {tool_names}")
            
            # Build request parameters
            # For llama-3.3-70b-versatile: Don't pass tool_choice explicitly when it's "auto"
            # Let Groq use its default (which is "auto" when tools are present)
            # This helps avoid the model generating function calls as text
            request_params = {
                "model": self.model,
                "messages": cleaned_messages,
                "temperature": temperature
            }
            
            # Add tools if provided
            if tools:
                request_params["tools"] = tools
                # For llama-3.3-70b-versatile, try "required" to force tool usage when appropriate
                # This helps when the model keeps writing function calls as text
                if tool_choice == "none":
                    request_params["tool_choice"] = "none"
                elif isinstance(tool_choice, dict):
                    # Specific function requested
                    request_params["tool_choice"] = tool_choice
                elif tool_choice == "auto":
                    # Don't use "required" - it causes llama-3.3-70b-versatile to generate invalid XML formats
                    # Instead, use "auto" and rely on post-processing to extract function calls from text
                    logger.debug(f"   Using tool_choice='auto' (Groq default)")
                    # Don't set tool_choice - let Groq default to "auto"
            
            logger.debug(f"   Request: model={self.model}, tools={len(tools) if tools else 0}, tool_choice={'default (auto)' if tools and tool_choice == 'auto' else tool_choice}")
            
            response = self.client.chat.completions.create(**request_params)
            
            # Check if response has tool_calls - if not, check if content contains function calls as text
            message = response.choices[0].message
            
            # Post-process to handle llama-3.3-70b-versatile bug where it returns function calls as text
            if not message.tool_calls and message.content:
                logger.warning(f"⚠️  No tool_calls in response, but content exists. Checking for function calls in text...")
                logger.info(f"   📝 Full content length: {len(message.content)} chars")
                logger.info(f"   📝 Content preview (first 1000 chars): {message.content[:1000]}")
                
                # Pattern 1a: function=name{json} format (no parentheses, with "function=" prefix)
                # Example: function=ask_clarifying_question{"context": "trip planning"}
                function_equals_matches = []
                # Find all instances of "function=" followed by name and opening brace
                func_equals_calls = re.finditer(r'function\s*=\s*(\w+)\s*\{', message.content)
                for match in func_equals_calls:
                    func_name = match.group(1)
                    start_pos = match.end() - 1  # Position of opening brace
                    
                    # Extract JSON by finding balanced braces
                    brace_count = 0
                    json_str = ""
                    for i in range(start_pos, len(message.content)):
                        char = message.content[i]
                        if char == '{':
                            brace_count += 1
                        elif char == '}':
                            brace_count -= 1
                        
                        json_str += char
                        
                        if brace_count == 0:
                            # Found complete JSON object
                            function_equals_matches.append((func_name, json_str))
                            break
                
                # Pattern 1b: function_name{json} format (no parentheses, no "function=" prefix)
                # Example: search_pois{"interests": ["culture"], "constraints": {"pace": "relaxed"}}
                # This is what we're actually seeing in the logs!
                direct_function_matches = []
                # Find function names that are in our tools list, followed directly by {
                if tools:
                    tool_names = [t.get('function', {}).get('name', '') for t in tools]
                    # Create pattern that matches any of our tool names followed by {
                    tool_names_pattern = '|'.join(re.escape(name) for name in tool_names)
                    pattern = rf'\b({tool_names_pattern})\s*{{'
                    logger.debug(f"   Searching for pattern: {pattern[:100]}...")
                    
                    for match in re.finditer(pattern, message.content):
                        func_name = match.group(1)
                        start_pos = match.end() - 1  # Position of opening brace
                        
                        # Extract JSON by finding balanced braces
                        brace_count = 0
                        json_str = ""
                        for i in range(start_pos, len(message.content)):
                            char = message.content[i]
                            if char == '{':
                                brace_count += 1
                            elif char == '}':
                                brace_count -= 1
                            
                            json_str += char
                            
                            if brace_count == 0:
                                # Found complete JSON object
                                direct_function_matches.append((func_name, json_str))
                                logger.debug(f"   Found direct format: {func_name} with {len(json_str)} char args")
                                break
                
                # Pattern 2: XML-wrapped function calls: <function=name>args</function>
                # Need to handle nested content properly
                wrapped_matches = []
                wrapped_start_pattern = r'<function=([^>]+)>'
                for match in re.finditer(wrapped_start_pattern, message.content):
                    func_name_raw = match.group(1).strip()
                    start_pos = match.end()
                    # Find the matching closing tag
                    end_tag = message.content.find('</function>', start_pos)
                    if end_tag != -1:
                        func_args_str = message.content[start_pos:end_tag].strip()
                        wrapped_matches.append((func_name_raw, func_args_str))
                
                # Pattern 3: Plain text function calls: function_name({"arg": "value"})
                # This is what we're seeing in the logs: search_pois({"interests": [...]})
                # Use a simpler approach: find function name, then extract JSON manually
                plain_matches = []
                # Find all potential function calls: word followed by opening paren and brace
                # Make sure we only match valid function names (word characters only, no parentheses)
                if tools:
                    tool_names = [t.get('function', {}).get('name', '') for t in tools]
                    # Match any tool name followed by ( and {
                    tool_names_pattern = '|'.join(re.escape(name) for name in tool_names)
                    pattern = rf'\b({tool_names_pattern})\s*\(\s*{{'
                    func_calls = re.finditer(pattern, message.content)
                else:
                    # Fallback: match any word followed by ( and {
                    func_calls = re.finditer(r'(\w+)\s*\(\s*\{', message.content)
                
                for match in func_calls:
                    func_name = match.group(1).strip()
                    # Ensure function name is clean (no parentheses or invalid chars)
                    func_name = func_name.rstrip('()').strip()
                    start_pos = match.end() - 1  # Position of opening brace
                    
                    # #region agent log
                    try:
                        with open(r'e:\Tech\Work Folders\Trip Planner Product\.cursor\debug.log', 'a', encoding='utf-8') as f:
                            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"H5","location":"groq_client.py:217","message":"Found plain text function call pattern","data":{"func_name_raw":match.group(1),"func_name_clean":func_name,"start_pos":start_pos},"timestamp":int(__import__('time').time()*1000)}) + '\n')
                    except: pass
                    # #endregion
                    
                    # Extract JSON by finding balanced braces
                    brace_count = 0
                    json_str = ""
                    for i in range(start_pos, len(message.content)):
                        char = message.content[i]
                        if char == '{':
                            brace_count += 1
                        elif char == '}':
                            brace_count -= 1
                        
                        json_str += char
                        
                        if brace_count == 0:
                            # Found complete JSON object
                            # Check if next non-whitespace is closing paren
                            remaining = message.content[i+1:].strip()
                            if remaining.startswith(')'):
                                plain_matches.append((func_name, json_str))
                            break
                
                # Combine all patterns
                all_matches = []
                
                # Add direct function_name{json} matches (THIS IS WHAT WE'RE SEEING!)
                for func_name, func_args_str in direct_function_matches:
                    func_name_clean = func_name.strip().rstrip('()').strip()
                    all_matches.append((func_name_clean, func_args_str.strip()))
                    logger.info(f"   ✅ Found direct format: {func_name_clean}")
                
                # Add function=name{json} matches
                for func_name, func_args_str in function_equals_matches:
                    func_name_clean = func_name.strip().rstrip('()').strip()
                    all_matches.append((func_name_clean, func_args_str.strip()))
                    logger.info(f"   ✅ Found function= format: {func_name_clean}")
                
                # Add wrapped matches
                for func_match in wrapped_matches:
                    func_name = func_match[0].split('{')[0] if '{' in func_match[0] else func_match[0]
                    func_name_clean = func_name.strip().rstrip('()').strip()
                    func_args_str = func_match[1].strip()
                    all_matches.append((func_name_clean, func_args_str))
                    logger.debug(f"   Found XML-wrapped format: {func_name_clean}")
                
                # Add plain matches (function_name({json}))
                for func_name, func_args_str in plain_matches:
                    func_name_clean = func_name.strip().rstrip('()').strip()
                    all_matches.append((func_name_clean, func_args_str.strip()))
                    logger.debug(f"   Found plain format: {func_name_clean}")
                
                logger.info(f"   🔍 Pattern matching results:")
                logger.info(f"      - Direct function_name{{json}} format: {len(direct_function_matches)} matches")
                logger.info(f"      - function=name{{json}} format: {len(function_equals_matches)} matches")
                logger.info(f"      - XML-wrapped format: {len(wrapped_matches)} matches")
                logger.info(f"      - Plain function_name({{json}}) format: {len(plain_matches)} matches")
                logger.info(f"      - Total matches: {len(all_matches)}")
                
                if len(all_matches) == 0:
                    logger.error(f"   ❌ NO FUNCTION CALLS DETECTED in content!")
                    logger.error(f"   This means the regex patterns are not matching the actual format")
                    logger.error(f"   Content sample for debugging: {message.content[:500]}")
                
                if all_matches:
                    logger.warning(f"   ✅ Found {len(all_matches)} function call(s) in text format (known llama-3.3-70b-versatile bug)")
                    logger.info(f"   📋 Function calls found: {[name for name, _ in all_matches]}")
                    logger.info(f"   🔧 Attempting to extract and convert to proper tool calls...")
                    
                    # Try to extract function calls from text
                    tool_calls = []
                    for idx, (func_name, func_args_str) in enumerate(all_matches, 1):
                        # Clean function name - remove any trailing parentheses, spaces, or invalid chars
                        func_name_clean = func_name.strip().rstrip('()').strip()
                        logger.info(f"   [{idx}/{len(all_matches)}] Processing: '{func_name}' -> cleaned: '{func_name_clean}'")
                        logger.info(f"      Args string length: {len(func_args_str)} chars")
                        logger.info(f"      Args preview: {func_args_str[:200]}...")
                        
                        # Use cleaned function name
                        func_name = func_name_clean
                        
                        # #region agent log
                        try:
                            with open(r'e:\Tech\Work Folders\Trip Planner Product\.cursor\debug.log', 'a', encoding='utf-8') as f:
                                f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"H5","location":"groq_client.py:286","message":"Extracting function call","data":{"original_name":func_name_clean,"args_length":len(func_args_str)},"timestamp":int(__import__('time').time()*1000)}) + '\n')
                        except: pass
                        # #endregion
                        
                        # Try to parse the arguments
                        try:
                            # The args might be in the format: {"key": "value"} or just the JSON
                            if func_args_str.startswith('{'):
                                func_args = json.loads(func_args_str)
                            else:
                                # Try to find JSON in the string
                                json_match = re.search(r'\{.*\}', func_args_str, re.DOTALL)
                                if json_match:
                                    func_args = json.loads(json_match.group(0))
                                else:
                                    logger.warning(f"   Could not parse arguments for {func_name}")
                                    continue
                            
                            # Validate function name is in our tools
                            if tools:
                                tool_names = [t.get('function', {}).get('name', '') for t in tools]
                                logger.info(f"      Available tools: {tool_names}")
                                
                                # #region agent log
                                try:
                                    with open(r'e:\Tech\Work Folders\Trip Planner Product\.cursor\debug.log', 'a', encoding='utf-8') as f:
                                        f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"H5","location":"groq_client.py:308","message":"Validating function name","data":{"func_name":func_name,"in_tools":func_name in tool_names,"tool_names":tool_names},"timestamp":int(__import__('time').time()*1000)}) + '\n')
                                except: pass
                                # #endregion
                                
                                if func_name not in tool_names:
                                    logger.warning(f"      ❌ Function '{func_name}' not in available tools, skipping")
                                    logger.warning(f"      Available tools are: {tool_names}")
                                    # #region agent log
                                    try:
                                        with open(r'e:\Tech\Work Folders\Trip Planner Product\.cursor\debug.log', 'a', encoding='utf-8') as f:
                                            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"H5","location":"groq_client.py:315","message":"Function name validation failed","data":{"func_name":func_name,"reason":"not_in_tools"},"timestamp":int(__import__('time').time()*1000)}) + '\n')
                                    except: pass
                                    # #endregion
                                    continue
                                logger.info(f"      ✅ Function '{func_name}' is in available tools")
                            
                            # Validate func_args is a dict
                            if not isinstance(func_args, dict):
                                logger.error(f"      ❌ func_args is not a dict: {type(func_args)}")
                                continue
                            
                            # Create a tool call object
                            tool_call_id = f"call_extracted_{len(tool_calls)}"
                            func_args_json = json.dumps(func_args)
                            logger.info(f"      ✅ Parsed arguments: {len(func_args)} keys")
                            logger.debug(f"      Arguments: {func_args_json[:300]}...")
                            
                            func_obj = type('Function', (), {
                                'name': func_name,
                                'arguments': func_args_json
                            })()
                            
                            tool_call_obj = type('ToolCall', (), {
                                'id': tool_call_id,
                                'type': 'function',
                                'function': func_obj
                            })()
                            
                            tool_calls.append(tool_call_obj)
                            logger.info(f"      ✅ Successfully created tool call object for {func_name}")
                            
                        except json.JSONDecodeError as e:
                            logger.warning(f"   Failed to parse arguments for {func_name}: {e}")
                            logger.debug(f"   Raw args: {func_args_str[:200]}")
                            continue
                        except Exception as e:
                            logger.error(f"   Error extracting {func_name}: {e}")
                            continue
                    
                    if tool_calls:
                        # Replace message with one that has tool_calls
                        logger.info(f"   ✅ Successfully extracted {len(tool_calls)} tool call(s)")
                        logger.info(f"   📋 Tool calls: {[tc.function.name for tc in tool_calls]}")
                        message.tool_calls = tool_calls
                        message.content = None  # Clear content since we have tool calls
                        logger.info(f"   ✅ Successfully converted {len(tool_calls)} text function calls to proper format")
                        logger.info(f"   ✅ Message now has tool_calls: {bool(message.tool_calls)}")
                        logger.info(f"   ✅ Message tool_calls count: {len(message.tool_calls) if message.tool_calls else 0}")
                    else:
                        logger.error(f"   ❌ Could not extract any valid function calls from text")
                        logger.error(f"   📋 All matches were: {all_matches}")
                        logger.error(f"   🔍 This means extraction failed for all {len(all_matches)} detected function calls")
            
            return {
                "message": message,
                "usage": response.usage,
                "model": response.model
            }
        except Exception as e:
            error_str = str(e)
            logger.error(f"Groq API error: {error_str}")
            
            # #region agent log
            try:
                with open(r'e:\Tech\Work Folders\Trip Planner Product\.cursor\debug.log', 'a', encoding='utf-8') as f:
                    f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"H6","location":"groq_client.py:416","message":"Groq API exception caught","data":{"error_type":type(e).__name__,"error_str_preview":error_str[:500],"has_tool_use_failed":"tool_use_failed" in error_str.lower()},"timestamp":int(__import__('time').time()*1000)}) + '\n')
            except: pass
            # #endregion
            
            # Check for tool_use_failed errors - extract function calls from wrapped format
            if "tool_use_failed" in error_str.lower():
                logger.warning("⚠️  Groq tool calling failed - model generated wrapped function calls (known llama-3.3-70b-versatile bug)")
                logger.info("   Attempting to extract function calls from error message...")
                
                # #region agent log
                try:
                    with open(r'e:\Tech\Work Folders\Trip Planner Product\.cursor\debug.log', 'a', encoding='utf-8') as f:
                        f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"H6","location":"groq_client.py:421","message":"tool_use_failed detected","data":{"error_str_length":len(error_str)},"timestamp":int(__import__('time').time()*1000)}) + '\n')
                except: pass
                # #endregion
                
                # Try multiple patterns to extract the failed generation
                failed_gen = None
                
                # Strategy: Look for the actual function call pattern in the error string
                # This is more robust than trying to parse the dict structure
                # The function call will be in the format: <function=name({...})</function>
                function_call_match = re.search(r'<function=[^<]+</function>', error_str)
                if function_call_match:
                    failed_gen = function_call_match.group(0)
                    # #region agent log
                    try:
                        with open(r'e:\Tech\Work Folders\Trip Planner Product\.cursor\debug.log', 'a', encoding='utf-8') as f:
                            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"H6","location":"groq_client.py:440","message":"Extracted via function call pattern","data":{"failed_gen":failed_gen},"timestamp":int(__import__('time').time()*1000)}) + '\n')
                    except: pass
                    # #endregion
                else:
                    # Fallback: Try to extract from 'failed_generation' key
                    # Pattern 1: 'failed_generation': '...'
                    failed_match = re.search(r"'failed_generation':\s*'([^']+)'", error_str)
                    if failed_match:
                        failed_gen = failed_match.group(1)
                    else:
                        # Pattern 2: "failed_generation": "..."
                        failed_match = re.search(r'"failed_generation":\s*"([^"]+)"', error_str)
                        if failed_match:
                            failed_gen = failed_match.group(1)
                        else:
                            # Pattern 3: Extract manually by finding the start and end
                            # Look for 'failed_generation': and extract until we find </function>
                            start_match = re.search(r"'failed_generation':\s*'", error_str)
                            if start_match:
                                start_pos = start_match.end()
                                # Find </function> which marks the end
                                end_match = re.search(r'</function>', error_str[start_pos:])
                                if end_match:
                                    end_pos = start_pos + end_match.end()
                                    failed_gen = error_str[start_pos:end_pos]
                            else:
                                # Try with double quotes
                                start_match = re.search(r'"failed_generation":\s*"', error_str)
                                if start_match:
                                    start_pos = start_match.end()
                                    end_match = re.search(r'</function>', error_str[start_pos:])
                                    if end_match:
                                        end_pos = start_pos + end_match.end()
                                        failed_gen = error_str[start_pos:end_pos]
                                else:
                                    # Pattern 4: failed_generation: ... (no quotes)
                                    failed_match = re.search(r'failed_generation[:\s]+([^\n,}]+)', error_str)
                                    if failed_match:
                                        failed_gen = failed_match.group(1).strip().strip("'\"")
                
                if not failed_gen:
                    logger.warning(f"   Could not extract failed_generation from error message")
                    # #region agent log
                    try:
                        with open(r'e:\Tech\Work Folders\Trip Planner Product\.cursor\debug.log', 'a', encoding='utf-8') as f:
                            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"H6","location":"groq_client.py:450","message":"Failed to extract failed_generation","data":{"error_str_sample":error_str[:1000]},"timestamp":int(__import__('time').time()*1000)}) + '\n')
                    except: pass
                    # #endregion
                    # Try to extract directly from error_str if failed_gen not found
                    failed_gen = error_str
                
                if failed_gen:
                    logger.debug(f"   Failed generation: {failed_gen[:300]}")
                    # #region agent log
                    try:
                        with open(r'e:\Tech\Work Folders\Trip Planner Product\.cursor\debug.log', 'a', encoding='utf-8') as f:
                            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"H6","location":"groq_client.py:444","message":"Extracted failed_generation","data":{"failed_gen_preview":failed_gen[:500]},"timestamp":int(__import__('time').time()*1000)}) + '\n')
                    except: pass
                    # #endregion
                    
                    # Use the same robust pattern matching as the main post-processing
                    # This ensures we catch all the same formats
                    all_matches = []
                    
                    # #region agent log
                    try:
                        with open(r'e:\Tech\Work Folders\Trip Planner Product\.cursor\debug.log', 'a', encoding='utf-8') as f:
                            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"H6","location":"groq_client.py:475","message":"Starting pattern matching","data":{"failed_gen_length":len(failed_gen),"failed_gen_full":failed_gen,"has_function_tag":"<function=" in failed_gen},"timestamp":int(__import__('time').time()*1000)}) + '\n')
                    except: pass
                    # #endregion
                    
                    # Pattern 1: function=name{json} format (no parentheses)
                    function_equals_pattern = r'function\s*=\s*(\w+)\s*(\{.*?\})'
                    for match in re.finditer(function_equals_pattern, failed_gen, re.DOTALL):
                        func_name = match.group(1).strip()
                        json_str = match.group(2).strip()
                        # Use balanced brace counting for nested JSON
                        brace_count = json_str.count('{') - json_str.count('}')
                        if brace_count > 0:
                            # Need to find the complete JSON
                            start_pos = match.end() - len(json_str)
                            full_json = ""
                            brace_count = 0
                            for i in range(start_pos, len(failed_gen)):
                                char = failed_gen[i]
                                if char == '{':
                                    brace_count += 1
                                elif char == '}':
                                    brace_count -= 1
                                full_json += char
                                if brace_count == 0:
                                    break
                            all_matches.append((func_name, full_json, "function=name{json}"))
                        else:
                            all_matches.append((func_name, json_str, "function=name{json}"))
                    
                    # Pattern 2: XML-wrapped function calls: <function=name>args</function>
                    wrapped_start_pattern = r'<function=([^>]+)>'
                    for match in re.finditer(wrapped_start_pattern, failed_gen):
                        func_name_raw = match.group(1).strip()
                        start_pos = match.end()
                        end_tag_match = re.search(r'</function>', failed_gen[start_pos:])
                        if end_tag_match:
                            end_tag = start_pos + end_tag_match.start()
                            func_args_str = failed_gen[start_pos:end_tag].strip()
                            func_name = func_name_raw.split('{')[0].strip() if '{' in func_name_raw else func_name_raw
                            all_matches.append((func_name, func_args_str, "XML-wrapped"))
                    
                    # Pattern 2b: XML-wrapped with function call inside tag: <function=name({json})</function>
                    # This is a malformed format that Groq sometimes generates: <function=search_pois({...})</function>
                    # Note: The format can be either <function=name({json})</function> or <function=name({json}</function>
                    # Match the opening tag with function call inside
                    wrapped_call_pattern = r'<function=(\w+)\s*\(\s*\{'
                    for match in re.finditer(wrapped_call_pattern, failed_gen):
                        func_name = match.group(1).strip()
                        # Find the opening brace position (the { after the opening parenthesis)
                        brace_start = match.end() - 1
                        # Find the matching closing brace
                        brace_count = 0
                        json_str = ""
                        for i in range(brace_start, len(failed_gen)):
                            char = failed_gen[i]
                            if char == '{':
                                brace_count += 1
                            elif char == '}':
                                brace_count -= 1
                            json_str += char
                            if brace_count == 0:
                                # Check if next is ')' followed by '</function>' OR just '</function>'
                                remaining = failed_gen[i+1:].strip()
                                # Handle both formats: <function=name({json})</function> and <function=name({json}</function>
                                # Also handle cases where there's no closing paren: <function=name({json}</function>
                                if '</function>' in remaining:
                                    # #region agent log
                                    try:
                                        with open(r'e:\Tech\Work Folders\Trip Planner Product\.cursor\debug.log', 'a', encoding='utf-8') as f:
                                            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"H6","location":"groq_client.py:538","message":"Found XML-wrapped pattern","data":{"func_name":func_name,"json_preview":json_str[:100],"remaining_preview":remaining[:50]},"timestamp":int(__import__('time').time()*1000)}) + '\n')
                                    except: pass
                                    # #endregion
                                    all_matches.append((func_name, json_str, "XML-wrapped-with-paren"))
                                break
                    
                    # Pattern 3: Plain text function calls: function_name({"arg": "value"})
                    if tools:
                        tool_names = [t.get('function', {}).get('name', '') for t in tools]
                        tool_names_pattern = '|'.join(re.escape(name) for name in tool_names)
                        pattern = rf'\b({tool_names_pattern})\s*\(\s*{{'
                        func_calls = re.finditer(pattern, failed_gen)
                    else:
                        func_calls = re.finditer(r'(\w+)\s*\(\s*\{', failed_gen)
                    
                    for match in func_calls:
                        func_name = match.group(1).strip().rstrip('()').strip()
                        start_pos = match.end() - 1
                        brace_count = 0
                        json_str = ""
                        for i in range(start_pos, len(failed_gen)):
                            char = failed_gen[i]
                            if char == '{':
                                brace_count += 1
                            elif char == '}':
                                brace_count -= 1
                            json_str += char
                            if brace_count == 0:
                                remaining = failed_gen[i+1:].strip()
                                if remaining.startswith(')'):
                                    all_matches.append((func_name, json_str, "plain_with_paren"))
                                break
                    
                    # Pattern 4: Direct function_name{json} (no prefix, no parentheses)
                    if tools:
                        tool_names = [t.get('function', {}).get('name', '') for t in tools]
                        tool_names_pattern = '|'.join(re.escape(name) for name in tool_names)
                        pattern = rf'\b({tool_names_pattern})\s*{{'
                        for match in re.finditer(pattern, failed_gen):
                            func_name = match.group(1).strip()
                            start_pos = match.end() - 1
                            brace_count = 0
                            json_str = ""
                            for i in range(start_pos, len(failed_gen)):
                                char = failed_gen[i]
                                if char == '{':
                                    brace_count += 1
                                elif char == '}':
                                    brace_count -= 1
                                json_str += char
                                if brace_count == 0:
                                    all_matches.append((func_name, json_str, "direct_no_paren"))
                                    break
                    
                    # #region agent log
                    try:
                        with open(r'e:\Tech\Work Folders\Trip Planner Product\.cursor\debug.log', 'a', encoding='utf-8') as f:
                            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"H6","location":"groq_client.py:480","message":"Pattern matching results","data":{"matches_count":len(all_matches),"matches":[(name, pattern_type) for name, _, pattern_type in all_matches],"failed_gen_sample":failed_gen[:200]},"timestamp":int(__import__('time').time()*1000)}) + '\n')
                    except: pass
                    # #endregion
                    
                    if not all_matches:
                        logger.warning(f"   No function call patterns matched in failed_generation")
                        raise Exception(f"Groq model (llama-3.3-70b-versatile) generated function calls wrapped in XML tags. Failed to extract function call from error message.")
                    
                    # Process the first match (most likely to be correct)
                    func_name, func_args_str, pattern_type = all_matches[0]
                    func_name = func_name.strip().rstrip('()').strip()
                    
                    logger.info(f"   ✅ Extracted function call from error: {func_name} (pattern: {pattern_type})")
                    
                    try:
                        # Parse the arguments - use balanced brace matching for nested JSON
                        if func_args_str.startswith('{'):
                            # Use balanced brace matching for nested JSON
                            brace_count = 0
                            json_end = -1
                            for i, char in enumerate(func_args_str):
                                if char == '{':
                                    brace_count += 1
                                elif char == '}':
                                    brace_count -= 1
                                    if brace_count == 0:
                                        json_end = i + 1
                                        break
                            
                            if json_end > 0:
                                func_args = json.loads(func_args_str[:json_end])
                            else:
                                func_args = json.loads(func_args_str)
                        else:
                            # Try to find JSON in the string
                            json_match = re.search(r'\{.*\}', func_args_str, re.DOTALL)
                            if json_match:
                                func_args = json.loads(json_match.group(0))
                            else:
                                raise ValueError("Could not find JSON arguments")
                        
                        # Validate function name is in our tools
                        if tools:
                            tool_names = [t.get('function', {}).get('name', '') for t in tools]
                            if func_name not in tool_names:
                                logger.warning(f"   Function '{func_name}' not in available tools, skipping")
                                raise Exception(f"Groq model (llama-3.3-70b-versatile) generated function calls wrapped in XML tags. Failed to extract function call from error message.")
                        
                        logger.info(f"   ✅ Successfully extracted: {func_name} with {len(func_args)} arguments")
                        
                        # Create a mock response with the extracted tool call
                        tool_call_id = f"call_extracted_0"
                        func_obj = type('Function', (), {
                            'name': func_name,
                            'arguments': json.dumps(func_args)
                        })()
                        
                        tool_call_obj = type('ToolCall', (), {
                            'id': tool_call_id,
                            'type': 'function',
                            'function': func_obj
                        })()
                        
                        message_obj = type('Message', (), {
                            'content': None,
                            'tool_calls': [tool_call_obj]
                        })()
                        
                        # Return the extracted tool call as if it was a successful response
                        logger.info(f"   ✅ Returning extracted tool call as valid response")
                        return {
                            "message": message_obj,
                            "usage": type('Usage', (), {
                                'prompt_tokens': 0,
                                'completion_tokens': 0,
                                'total_tokens': 0
                            })(),
                            "model": self.model
                        }
                        
                    except (json.JSONDecodeError, ValueError) as e:
                        logger.error(f"   ❌ Could not parse function arguments: {e}")
                        logger.error(f"   Raw args string: {func_args_str[:200]}")
                
                # If we couldn't extract, raise the original error
                raise Exception(f"Groq model (llama-3.3-70b-versatile) generated function calls wrapped in XML tags. Failed to extract function call from error message.")
            
            # Check for rate limit errors
            if "429" in error_str or "rate_limit" in error_str.lower() or "Rate limit" in error_str:
                logger.error("⚠️  Groq API rate limit reached!")
                if "Please try again in" in error_str:
                    # Extract wait time from error message
                    wait_match = re.search(r'Please try again in ([\dhms.]+)', error_str)
                    if wait_match:
                        wait_time = wait_match.group(1)
                        raise Exception(f"Groq API rate limit reached. Please wait {wait_time} before trying again. Or upgrade your tier at https://console.groq.com/settings/billing")
                raise Exception("Groq API rate limit reached. Please wait before trying again or upgrade your tier.")
            
            raise Exception(f"Groq API error: {error_str}")
    
    def _clean_messages(self, messages: List[Dict]) -> List[Dict]:
        """
        Clean messages to ensure they're in the correct format for Groq
        Converts any Gemini-formatted tool responses back to Groq format
        Removes unsupported fields like 'timestamp'
        """
        cleaned = []
        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content", "")
            
            # Skip empty messages
            if not content and role != "system":
                continue
            
            # Create cleaned message with only supported fields
            cleaned_msg = {
                "role": role,
                "content": content
            }
            
            # Add tool_calls if present (for assistant messages)
            if "tool_calls" in msg:
                cleaned_msg["tool_calls"] = msg["tool_calls"]
            
            # Add tool response fields if present (for tool messages)
            if role == "tool":
                if "tool_call_id" in msg:
                    cleaned_msg["tool_call_id"] = msg["tool_call_id"]
                if "name" in msg:
                    cleaned_msg["name"] = msg["name"]
            
            # If it's a user message that looks like a Gemini tool response, try to convert it
            if role == "user" and content.startswith("Function ") and " returned: " in content:
                # This is a Gemini-formatted tool response - we need to convert it back
                # But we don't have the tool_call_id, so we'll keep it as a user message
                # Groq should be able to handle this, but log it
                logger.warning(f"⚠️  Found Gemini-formatted tool response in messages - keeping as user message")
            
            cleaned.append(cleaned_msg)
        
        return cleaned


if __name__ == "__main__":
    # Test Groq client
    logging.basicConfig(level=logging.INFO)
    try:
        client = GroqClient()
        logger.info("✅ Groq client initialized")
        
        # Test simple completion
        messages = [
            {"role": "system", "content": client.get_system_prompt()},
            {"role": "user", "content": "Hello, can you help me plan a trip?"}
        ]
        
        response = client.chat_completion(messages)
        logger.info(f"Response: {response['message'].content}")
    except Exception as e:
        logger.error(f"Error: {e}")

