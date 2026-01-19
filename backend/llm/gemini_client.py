"""
Gemini LLM client configuration
"""

import google.generativeai as genai
from typing import List, Dict, Optional
import os
from dotenv import load_dotenv
import logging
import json

load_dotenv()

logger = logging.getLogger(__name__)


def _convert_mapcomposite_to_dict(mapcomposite) -> dict:
    """Convert Gemini's protobuf MapComposite to a regular Python dict (recursive)"""
    if mapcomposite is None:
        return {}
    
    if isinstance(mapcomposite, dict):
        # Recursively convert nested MapComposite objects
        result = {}
        for k, v in mapcomposite.items():
            result[k] = _convert_value_recursive(v)
        return result
    
    # Check if it's a MapComposite type
    mapcomposite_type_name = type(mapcomposite).__name__
    if "MapComposite" in mapcomposite_type_name or "MessageMap" in mapcomposite_type_name:
        try:
            # Try iterating as key-value pairs (most common case)
            result = {}
            for k, v in mapcomposite.items():
                result[k] = _convert_value_recursive(v)
            return result
        except (TypeError, AttributeError):
            pass
        
        try:
            # Try converting directly to dict
            result = {}
            for k, v in dict(mapcomposite).items():
                result[k] = _convert_value_recursive(v)
            return result
        except (TypeError, ValueError):
            pass
        
        try:
            # Try getting _values attribute
            values = getattr(mapcomposite, '_values', {})
            result = {}
            for k, v in values.items():
                result[k] = _convert_value_recursive(v)
            return result
        except:
            pass
        
        try:
            # Last resort: use protobuf MessageToDict
            from google.protobuf.json_format import MessageToDict
            converted = MessageToDict(mapcomposite)
            # Recursively convert nested values
            return _convert_mapcomposite_to_dict(converted)
        except:
            pass
    
    logger.warning(f"Failed to convert MapComposite to dict: {type(mapcomposite)}")
    return {}


def _convert_value_recursive(value):
    """Recursively convert values that might contain MapComposite or RepeatedComposite"""
    if value is None:
        return None
    
    # Check for RepeatedComposite (protobuf repeated fields)
    value_type_name = type(value).__name__
    if "RepeatedComposite" in value_type_name or "RepeatedScalar" in value_type_name:
        try:
            # Convert repeated field to list
            return [_convert_value_recursive(item) for item in value]
        except (TypeError, AttributeError):
            # If iteration fails, try converting to list directly
            try:
                return list(value)
            except:
                return []
    
    # Check if value itself is a MapComposite
    if "MapComposite" in value_type_name or "MessageMap" in value_type_name:
        return _convert_mapcomposite_to_dict(value)
    
    # Check if it's a list that might contain MapComposite
    if isinstance(value, list):
        return [_convert_value_recursive(item) for item in value]
    
    # Check if it's a dict that might contain MapComposite
    if isinstance(value, dict):
        return _convert_mapcomposite_to_dict(value)
    
    # Primitive types - return as-is
    return value


class GeminiClient:
    """Gemini LLM client wrapper"""
    
    def __init__(self, model: str = "gemini-2.5-flash"):
        """
        Initialize Gemini client
        
        Available models:
        - gemini-2.5-flash (recommended for tool calling, fast)
        - gemini-3-flash (newer, faster)
        - gemini-2.5-flash-lite (lighter version)
        """
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables. Please set it in .env file.")
        
        # Configure Gemini
        genai.configure(api_key=api_key)
        self.model = model
        self.client = genai.GenerativeModel(model)
        logger.info(f"✅ Gemini client initialized with model: {model}")
    
    def get_system_prompt(self) -> str:
        """Get the system prompt for the travel assistant"""
        return """You are a helpful travel planning assistant specializing in Jaipur, India.

Your role is to:
1. Understand user trip preferences and constraints
2. Generate realistic, feasible day-wise itineraries
3. Allow users to modify plans via voice commands
4. Explain your decisions clearly with citations

Key principles:
- Always ground recommendations in real data (POIs, travel guides)
- Cite sources when providing information
- Ask clarifying questions only when critical information is missing (max 6 questions)
- Generate itineraries that are realistic and consider travel time, opening hours, and user pace
- Be concise in voice responses, but provide detailed explanations when asked

When generating itineraries:
- Structure by day (Day 1, Day 2, Day 3)
- Break each day into Morning, Afternoon, Evening blocks
- Include estimated travel time between activities
- Consider user's pace preference (relaxed, moderate, packed)
- Validate that activities fit within time windows

When explaining decisions or answering questions:
- **ALWAYS use retrieve_city_guidance tool** to get factual information about Jaipur
- **NEVER make up information** - always retrieve from the knowledge base first
- Reference specific sources (Wikivoyage, Wikipedia, OpenStreetMap) in your response
- Connect choices to user preferences
- Be transparent about data limitations
- If asked "why" or "explain", you MUST call retrieve_city_guidance before answering

You have access to tools for:
- Searching points of interest (POIs) - use search_pois when you need to find places
- Building structured itineraries - use build_itinerary after finding POIs
- Retrieving city guidance and travel tips - use retrieve_city_guidance for ALL explanations and questions
- Asking clarifying questions - use ask_clarifying_question when information is missing

**CRITICAL WORKFLOW FOR ITINERARY CREATION:**
1. When user asks to plan a trip, you MUST:
   a. First call search_pois with their interests (e.g., ['culture', 'food', 'history'])
   b. Then call build_itinerary with the POIs from step (a), duration_days, and pace
   c. Do NOT respond to itinerary requests without calling both tools

2. For any question about Jaipur, attractions, safety, etiquette, or "why" questions, 
   you MUST call retrieve_city_guidance to get accurate, cited information. Do not rely on 
   your training data alone.

3. NEVER generate an itinerary without calling search_pois and build_itinerary tools first.
   These tools provide real data - you cannot create a valid itinerary without them."""
    
    def _convert_messages_to_gemini_format(self, messages: List[Dict]) -> List[Dict]:
        """Convert OpenAI-style messages to Gemini format"""
        gemini_messages = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            tool_calls = msg.get("tool_calls")
            
            # Skip system messages (will be added separately)
            if role == "system":
                continue
            
            # Gemini uses 'model' instead of 'assistant'
            if role == "assistant":
                role = "model"
                
                # Handle assistant messages with tool calls
                # In Gemini, we need to format this as a model message with function calls
                if tool_calls:
                    # For assistant messages with tool calls, we need to include the function calls
                    # But Gemini's chat history format is different - we'll just include the text content
                    # and let the tool results be in the next user message
                    if content:
                        gemini_messages.append({
                            "role": "model",
                            "parts": [{"text": content}]
                        })
                    # Tool calls will be handled by the tool response messages
                    continue
            
            # Gemini doesn't support "tool" role - convert tool responses to user messages
            if role == "tool":
                # Convert tool response to user message format
                # Format: "Function [name] returned: [result]"
                tool_name = msg.get("name", "unknown")
                tool_result = content
                
                # Ensure content is a string and not empty
                if not isinstance(tool_result, str):
                    try:
                        tool_result = json.dumps(tool_result) if tool_result else "{}"
                    except (TypeError, ValueError):
                        tool_result = str(tool_result) if tool_result else "{}"
                
                # Truncate very long tool results to avoid token limits and format issues
                if len(tool_result) > 3000:
                    tool_result = tool_result[:3000] + "... (truncated for length)"
                
                # Clean up any problematic characters that might break Gemini's format
                tool_result = tool_result.replace('\x00', '').replace('\ufffd', '')
                
                content = f"Function {tool_name} returned: {tool_result}"
                role = "user"
            
            # Only add valid roles (user or model) with non-empty content
            if role in ["user", "model"] and content:
                # Ensure content is a string
                if not isinstance(content, str):
                    content = str(content)
                
                # Skip empty messages
                if not content.strip():
                    continue
                
                gemini_messages.append({
                    "role": role,
                    "parts": [{"text": content}]
                })
        
        return gemini_messages
    
    def _convert_json_schema_to_gemini_schema(self, json_schema: Dict) -> genai.protos.Schema:
        """Convert JSON Schema to Gemini Schema format"""
        schema_type = json_schema.get("type", "object")
        
        # Map JSON Schema types to Gemini Type enum
        gemini_type_map = {
            "string": genai.protos.Type.STRING,
            "integer": genai.protos.Type.INTEGER,
            "number": genai.protos.Type.NUMBER,
            "boolean": genai.protos.Type.BOOLEAN,
            "array": genai.protos.Type.ARRAY,
            "object": genai.protos.Type.OBJECT
        }
        
        if schema_type == "object":
            properties = json_schema.get("properties", {})
            required = json_schema.get("required", [])
            
            # Convert properties to Gemini Schema format
            schema_properties = {}
            for prop_name, prop_def in properties.items():
                prop_type = prop_def.get("type", "string")
                gemini_type = gemini_type_map.get(prop_type, genai.protos.Type.STRING)
                
                # Build property schema
                prop_schema_kwargs = {
                    "type_": gemini_type
                }
                
                if "description" in prop_def:
                    prop_schema_kwargs["description"] = prop_def["description"]
                
                # Handle nested objects (recursive)
                if prop_type == "object" and "properties" in prop_def:
                    nested_schema = self._convert_json_schema_to_gemini_schema(prop_def)
                    prop_schema_kwargs["type_"] = genai.protos.Type.OBJECT
                    prop_schema_kwargs["properties"] = nested_schema.properties
                    if nested_schema.required:
                        prop_schema_kwargs["required"] = nested_schema.required
                # Handle array items (required for Gemini)
                elif prop_type == "array":
                    if "items" in prop_def:
                        items_def = prop_def["items"]
                        # Recursive for array of objects
                        if items_def.get("type") == "object":
                            items_schema = self._convert_json_schema_to_gemini_schema(items_def)
                            prop_schema_kwargs["items"] = items_schema
                        else:
                            items_type = items_def.get("type", "string")
                            items_gemini_type = gemini_type_map.get(items_type, genai.protos.Type.STRING)
                            prop_schema_kwargs["items"] = genai.protos.Schema(type_=items_gemini_type)
                    else:
                        # Default to string array if items not specified (Gemini requires items field)
                        logger.warning(f"Array property '{prop_name}' missing 'items' field, defaulting to string array")
                        prop_schema_kwargs["items"] = genai.protos.Schema(type_=genai.protos.Type.STRING)
                
                # Handle enum (convert to list of strings for Gemini)
                if "enum" in prop_def:
                    prop_schema_kwargs["enum"] = [str(e) for e in prop_def["enum"]]
                
                prop_schema = genai.protos.Schema(**prop_schema_kwargs)
                schema_properties[prop_name] = prop_schema
            
            # Create the main schema
            schema_kwargs = {
                "type_": genai.protos.Type.OBJECT,
                "properties": schema_properties
            }
            # Only add required if it's not empty
            if required:
                schema_kwargs["required"] = required
            
            return genai.protos.Schema(**schema_kwargs)
        else:
            # Simple type
            return genai.protos.Schema(
                type_=gemini_type_map.get(schema_type, genai.protos.Type.STRING)
            )
    
    def _convert_tools_to_gemini_format(self, tools: Optional[List[Dict]]) -> Optional[List]:
        """Convert OpenAI-style tools to Gemini function calling format"""
        if not tools:
            return None
        
        function_declarations = []
        for tool in tools:
            if tool.get("type") == "function":
                func_def = tool.get("function", {})
                parameters = func_def.get("parameters", {})
                
                # Convert JSON Schema to Gemini Schema
                gemini_schema = self._convert_json_schema_to_gemini_schema(parameters)
                
                function_declarations.append(
                    genai.protos.FunctionDeclaration(
                        name=func_def.get("name"),
                        description=func_def.get("description", ""),
                        parameters=gemini_schema
                    )
                )
        
        if function_declarations:
            return [genai.protos.Tool(function_declarations=function_declarations)]
        return None
    
    def _convert_tool_calls_from_gemini(self, function_calls) -> List:
        """Convert Gemini function calls to OpenAI-style format"""
        tool_calls = []
        if function_calls:
            for idx, fc in enumerate(function_calls):
                # Gemini function calls have name and args attributes
                func_name = fc.name if hasattr(fc, 'name') else getattr(fc, 'function_name', 'unknown')
                func_args = {}
                
                # Handle Gemini's protobuf MapComposite type
                if hasattr(fc, 'args') and fc.args is not None:
                    func_args = _convert_mapcomposite_to_dict(fc.args)
                elif hasattr(fc, 'arguments'):
                    if isinstance(fc.arguments, str):
                        func_args = json.loads(fc.arguments)
                    elif isinstance(fc.arguments, dict):
                        func_args = fc.arguments
                    else:
                        func_args = _convert_mapcomposite_to_dict(fc.arguments)
                else:
                    func_args = {}
                
                tool_calls.append({
                    "id": f"call_{idx}",
                    "type": "function",
                    "function": {
                        "name": func_name,
                        "arguments": json.dumps(func_args) if isinstance(func_args, dict) else str(func_args)
                    }
                })
        return tool_calls
    
    def chat_completion(self, messages: List[Dict], tools: Optional[List[Dict]] = None,
                       tool_choice: str = "auto", temperature: float = 0.7) -> Dict:
        """
        Make a chat completion request to Gemini
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            tools: List of function definitions (for function calling)
            tool_choice: "auto", "none", or {"type": "function", "function": {"name": "..."}}
            temperature: Sampling temperature (0-2)
        
        Returns:
            Response dict with message and tool_calls (OpenAI-compatible format)
        """
        try:
            # Extract system prompt from messages
            system_prompt = None
            filtered_messages = []
            for msg in messages:
                if msg.get("role") == "system":
                    system_prompt = msg.get("content", "")
                else:
                    filtered_messages.append(msg)
            
            # Convert messages to Gemini format
            gemini_messages = self._convert_messages_to_gemini_format(filtered_messages)
            
            # Convert tools to Gemini format
            gemini_tools = self._convert_tools_to_gemini_format(tools) if tools else None
            logger.info(f"Tools provided: {len(tools) if tools else 0}")
            logger.info(f"Gemini tools converted: {len(gemini_tools) if gemini_tools else 0}")
            if gemini_tools:
                logger.debug(f"   Tool names: {[t.name if hasattr(t, 'name') else 'unknown' for t in gemini_tools]}")
            
            # Configure generation config
            generation_config = genai.types.GenerationConfig(
                temperature=temperature,
            )
            
            # Prepare the last user message
            # Ensure we have valid messages
            if not gemini_messages:
                logger.error("No valid messages to send to Gemini")
                raise Exception("No valid messages to send to Gemini API")
            
            # Get last message safely
            last_message_parts = gemini_messages[-1].get("parts", [])
            if not last_message_parts or not last_message_parts[0].get("text"):
                logger.error(f"Last message has no text content: {gemini_messages[-1]}")
                raise Exception("Last message has no text content")
            
            last_message = last_message_parts[0]["text"]
            
            # Create model with system instruction and tools
            model_kwargs = {}
            if system_prompt:
                model_kwargs["system_instruction"] = system_prompt
                logger.debug(f"System prompt length: {len(system_prompt)} chars")
            if gemini_tools and tool_choice != "none":
                model_kwargs["tools"] = gemini_tools
                logger.info(f"✅ Tools configured for model: {len(gemini_tools)} tools")
            else:
                logger.warning(f"⚠️  No tools configured! tool_choice={tool_choice}, gemini_tools={bool(gemini_tools)}")
            
            # Create model instance
            logger.debug(f"Creating model with kwargs: {list(model_kwargs.keys())}")
            model = genai.GenerativeModel(model_name=self.model, **model_kwargs)
            
            # For Gemini, we need to handle chat history differently
            # If we have history, use start_chat, otherwise just use generate_content
            if len(gemini_messages) > 1:
                # Start chat with history (excluding last message)
                chat_history = gemini_messages[:-1]
                chat = model.start_chat(history=chat_history)
                
                # Send last message
                response = chat.send_message(
                    last_message,
                    generation_config=generation_config
                )
            else:
                # No history, use generate_content directly
                response = model.generate_content(
                    last_message,
                    generation_config=generation_config
                )
            
            # Extract response content
            response_text = ""
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                    for part in candidate.content.parts:
                        if hasattr(part, 'text') and part.text:
                            response_text += part.text
            
            # Extract function calls if any
            tool_calls = []
            # Check response.candidates[0].content.parts for function calls
            logger.debug(f"Checking for function calls in response...")
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                logger.debug(f"   Candidate found, checking content parts...")
                if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                    logger.debug(f"   Content has {len(candidate.content.parts)} parts")
                    for i, part in enumerate(candidate.content.parts):
                        logger.debug(f"   Part {i+1}: has function_call={hasattr(part, 'function_call')}, has text={hasattr(part, 'text')}")
                        if hasattr(part, 'function_call'):
                            func_call = part.function_call
                            func_name = func_call.name if hasattr(func_call, 'name') else getattr(func_call, 'function_name', 'unknown')
                            func_args = {}
                            
                            # Handle Gemini's protobuf MapComposite and RepeatedComposite types
                            func_args = {}
                            
                            # Try to get args from func_call
                            if hasattr(func_call, 'args') and func_call.args is not None:
                                # Convert using recursive function to handle all protobuf types
                                func_args = _convert_value_recursive(func_call.args)
                            elif hasattr(func_call, 'arguments'):
                                if isinstance(func_call.arguments, dict):
                                    func_args = _convert_value_recursive(func_call.arguments)
                                elif isinstance(func_call.arguments, str):
                                    try:
                                        func_args = json.loads(func_call.arguments)
                                    except json.JSONDecodeError:
                                        logger.warning(f"Failed to parse arguments as JSON string: {func_call.arguments}")
                                        func_args = {}
                                else:
                                    # Convert protobuf types (MapComposite, RepeatedComposite, etc.)
                                    func_args = _convert_value_recursive(func_call.arguments)
                            
                            # Ensure func_args is a dict (not a list or other type)
                            if not isinstance(func_args, dict):
                                logger.warning(f"func_args is not a dict after conversion: {type(func_args)}")
                                if isinstance(func_args, (list, tuple)) and len(func_args) > 0:
                                    # If it's a list, try to extract dict from first element
                                    first_item = _convert_value_recursive(func_args[0])
                                    func_args = first_item if isinstance(first_item, dict) else {}
                                else:
                                    func_args = {}
                            
                            # Final recursive conversion to ensure all nested protobuf types are converted
                            func_args = _convert_value_recursive(func_args) if func_args else {}
                            if not isinstance(func_args, dict):
                                func_args = {}
                            
                            # Double-check: ensure func_args is truly JSON serializable
                            try:
                                # Test JSON serialization
                                json.dumps(func_args)
                            except (TypeError, ValueError) as e:
                                logger.error(f"func_args still not JSON serializable after conversion: {e}, type: {type(func_args)}")
                                # Try one more recursive conversion
                                func_args = _convert_value_recursive(func_args)
                                if not isinstance(func_args, dict):
                                    func_args = {}
                                try:
                                    json.dumps(func_args)
                                except:
                                    logger.error(f"Failed to serialize func_args even after recursive conversion. Skipping this tool call.")
                                    continue  # Skip this tool call entirely
                            
                            # Ensure func_name is not empty
                            if not func_name or func_name == "unknown":
                                logger.error(f"Function name is empty or unknown! func_call: {func_call}")
                                continue  # Skip this tool call if name is missing
                            
                            # Create object-like structure for tool_calls (matching Groq format)
                            tool_call_id = f"call_{len(tool_calls)}"
                            func_args_json = json.dumps(func_args)  # Convert once, use multiple times
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
                            logger.info(f"✅ Extracted tool call: {func_name} with {len(func_args)} args")
                else:
                    logger.warning(f"⚠️  Candidate content has no 'parts' attribute")
            else:
                logger.warning(f"⚠️  Response has no candidates or candidates is empty")
            
            logger.info(f"Total tool calls extracted: {len(tool_calls)}")
            if tool_calls:
                logger.info(f"   Tool call functions: {[getattr(tc.function, 'name', 'unknown') for tc in tool_calls]}")
            
            # Create OpenAI-compatible response
            message_obj = type('Message', (), {
                'content': response_text,
                'tool_calls': tool_calls if tool_calls else None
            })()
            
            # Create usage info (Gemini doesn't provide this directly, so we estimate)
            usage_obj = type('Usage', (), {
                'prompt_tokens': len(last_message.split()) * 1.3,  # Rough estimate
                'completion_tokens': len(response_text.split()) * 1.3,
                'total_tokens': (len(last_message.split()) + len(response_text.split())) * 1.3
            })()
            
            return {
                "message": message_obj,
                "usage": usage_obj,
                "model": self.model
            }
            
        except Exception as e:
            error_str = str(e)
            logger.error(f"Gemini API error: {error_str}")
            
            # Check for rate limit errors
            if "429" in error_str or "rate_limit" in error_str.lower() or "quota" in error_str.lower():
                logger.error("⚠️  Gemini API rate limit/quota reached!")
                raise Exception("Gemini API rate limit/quota reached. Please check your quota or upgrade your tier.")
            
            raise Exception(f"Gemini API error: {error_str}")


if __name__ == "__main__":
    # Test Gemini client
    logging.basicConfig(level=logging.INFO)
    try:
        client = GeminiClient()
        logger.info("✅ Gemini client initialized")
        
        # Test simple completion
        messages = [
            {"role": "system", "content": client.get_system_prompt()},
            {"role": "user", "content": "Hello, can you help me plan a trip?"}
        ]
        
        response = client.chat_completion(messages)
        logger.info(f"Response: {response['message'].content}")
    except Exception as e:
        logger.error(f"Error: {e}")

