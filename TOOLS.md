# Tools Reference

This document lists all tools/functions available to the LLM orchestrator for trip planning and information retrieval.

## Overview

The system uses function calling to enable the LLM to interact with external tools. All tools are registered in `backend/tools/register_handlers.py` and called through the `LLMOrchestrator`.

## Available Tools

### 1. `search_pois`

**Purpose**: Search for Points of Interest (POIs) in Jaipur based on user interests and constraints.

**Handler**: `tools.poi_search.search_pois_handler`

**Function Definition**:
```python
{
    "name": "search_pois",
    "description": "Search for points of interest (POIs) in Jaipur based on interests, budget, pace, and other constraints",
    "parameters": {
        "type": "object",
        "properties": {
            "interests": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of interests (e.g., ['culture', 'food', 'history', 'shopping', 'architecture'])"
            },
            "constraints": {
                "type": "object",
                "properties": {
                    "budget": {"type": "string", "enum": ["budget", "mid-range", "luxury"]},
                    "pace": {"type": "string", "enum": ["relaxed", "moderate", "packed"]},
                    "indoor_only": {"type": "boolean"},
                    "accessibility": {"type": "boolean"}
                }
            },
            "max_results": {"type": "integer", "default": 20}
        },
        "required": ["interests"]
    }
}
```

**Data Source**: OpenStreetMap (OSM) via Overpass API

**Returns**:
- List of POI objects with:
  - `id`: Unique identifier
  - `name`: POI name
  - `location`: `{"lat": float, "lon": float}`
  - `category`: Category (e.g., "tourism", "restaurant", "shop")
  - `visit_duration_minutes`: Estimated visit duration
  - `distance_km`: Distance from Jaipur center
  - `source`: "openstreetmap"
  - `source_url`: OSM node URL

**Usage Example**:
```python
# LLM calls:
search_pois(
    interests=["history", "architecture"],
    constraints={"budget": "mid-range", "pace": "moderate"},
    max_results=20
)
```

**When to Use**:
- User asks to plan a trip
- User wants to find specific attractions
- User requests activities by category (e.g., "find restaurants", "show me museums")

---

### 2. `build_itinerary`

**Purpose**: Create a structured day-wise itinerary from a list of POIs.

**Handler**: `tools.itinerary_builder.build_itinerary_handler`

**Function Definition**:
```python
{
    "name": "build_itinerary",
    "description": "Build a structured day-wise itinerary from candidate POIs",
    "parameters": {
        "type": "object",
        "properties": {
            "candidate_pois": {
                "type": "array",
                "items": {"type": "object"},
                "description": "List of POI objects from search_pois"
            },
            "duration_days": {"type": "integer", "minimum": 1, "maximum": 7},
            "pace": {"type": "string", "enum": ["relaxed", "moderate", "packed"]},
            "start_time": {"type": "string", "default": "09:00"}
        },
        "required": ["candidate_pois", "duration_days", "pace"]
    }
}
```

**Returns**:
- Structured itinerary object:
  ```python
  {
      "days": [
          {
              "day": 1,
              "activities": [
                  {
                      "time_period": "morning",
                      "start_time": "09:00",
                      "end_time": "11:00",
                      "poi": {...},  # POI object
                      "travel_time_minutes": 15
                  },
                  # ... more activities
              ]
          }
      ]
  }
  ```

**Features**:
- Splits days into Morning, Afternoon, Evening blocks
- Calculates travel time between activities
- Respects pace preferences (relaxed: 2-3 activities/day, moderate: 3-4, packed: 4-5)
- Validates time windows
- Includes buffer time between activities

**Usage Example**:
```python
# LLM calls:
build_itinerary(
    candidate_pois=[...],  # List of POI objects from search_pois
    duration_days=2,
    pace="moderate"
)
```

**When to Use**:
- After `search_pois` to structure the results
- When user requests itinerary modifications (must rebuild)
- When user changes trip duration or pace

**Important**: Always call `build_itinerary` after any itinerary modification request, as the UI depends on the structured itinerary format.

---

### 3. `retrieve_city_guidance`

**Purpose**: Retrieve factual information about Jaipur from the RAG knowledge base.

**Handler**: `tools.rag_retrieval.retrieve_city_guidance_handler`

**Function Definition**:
```python
{
    "name": "retrieve_city_guidance",
    "description": "Retrieve factual information and travel guidance about Jaipur from the knowledge base",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Question or topic to search for"
            },
            "top_k": {
                "type": "integer",
                "default": 3,
                "description": "Number of relevant chunks to retrieve"
            }
        },
        "required": ["query"]
    }
}
```

**Data Source**: ChromaDB vector database (Wikivoyage, Wikipedia)

**Returns**:
- List of context chunks with:
  - `text`: Chunk content
  - `source`: Source name (e.g., "Wikivoyage", "Wikipedia")
  - `url`: Source URL
  - `section`: Section name
  - `section_anchor`: Section anchor (if available)
  - `score`: Relevance score

**Citations**: Automatically stored in session for source display

**Usage Example**:
```python
# LLM calls:
retrieve_city_guidance(
    query="Why is Hawa Mahal a recommended tourist destination?",
    top_k=3
)
```

**When to Use**:
- User asks "why" questions about attractions
- User requests factual information about Jaipur
- User asks about culture, history, safety, etiquette
- User wants explanations or recommendations

**Important**: Always use this tool for factual questions. Never make up information.

---

### 4. `ask_clarifying_question`

**Purpose**: Generate clarifying questions when critical information is missing.

**Handler**: `tools.question_generator.ask_clarifying_question_handler`

**Function Definition**:
```python
{
    "name": "ask_clarifying_question",
    "description": "Ask the user a clarifying question when critical information is missing",
    "parameters": {
        "type": "object",
        "properties": {
            "question": {
                "type": "string",
                "description": "The clarifying question to ask"
            },
            "context": {
                "type": "string",
                "description": "Context about why this question is needed"
            }
        },
        "required": ["question"]
    }
}
```

**Returns**:
- Question object with `question` and optional `context`

**Usage Example**:
```python
# LLM calls:
ask_clarifying_question(
    question="How many days would you like to spend in Jaipur?",
    context="Need to know trip duration to create itinerary"
)
```

**When to Use**:
- Critical information is missing (duration, pace, interests)
- User request is ambiguous
- Need to narrow down options

**Best Practice**: Limit to 1-2 questions per interaction to avoid frustrating the user.

---

## Tool Execution Flow

### Typical Itinerary Creation Flow

1. **User**: "Plan a 2-day trip to Jaipur"
2. **LLM calls**: `search_pois(interests=["culture", "history"], max_results=20)`
3. **System returns**: List of POIs
4. **LLM calls**: `build_itinerary(candidate_pois=[...], duration_days=2, pace="moderate")`
5. **System returns**: Structured itinerary
6. **LLM responds**: Formatted itinerary with activities

### Question Answering Flow

1. **User**: "Why is Hawa Mahal recommended?"
2. **LLM calls**: `retrieve_city_guidance(query="Why is Hawa Mahal a recommended tourist destination?", top_k=3)`
3. **System returns**: Context chunks with citations
4. **LLM responds**: Answer with source citations

### Itinerary Modification Flow

1. **User**: "Remove Day 1 morning activity"
2. **LLM**: Extracts current itinerary from context
3. **LLM calls**: `build_itinerary(candidate_pois=[...], duration_days=2, pace="moderate")` (with modified POI list)
4. **System returns**: Updated itinerary
5. **LLM responds**: Confirmation with updated itinerary

**Critical**: Always call `build_itinerary` after modifications, as the UI depends on the structured format.

---

## Tool Registration

All tools are auto-registered in `LLMOrchestrator.__init__()` via:

```python
from tools.register_handlers import register_all_handlers
register_all_handlers(self)
```

This registers handlers for:
- `search_pois` → `search_pois_handler`
- `build_itinerary` → `build_itinerary_handler`
- `retrieve_city_guidance` → `retrieve_city_guidance_handler`
- `ask_clarifying_question` → `ask_clarifying_question_handler`

---

## Tool Caching

Tool results are cached to reduce redundant API calls:
- **POI Cache**: 7 days TTL (POIs don't change frequently)
- **RAG Cache**: 24 hours TTL (knowledge base updates infrequently)
- **Tool Cache**: 24 hours TTL (general tool results)

Cache keys are based on function name and parameters hash.

---

## Error Handling

All tools include:
- Retry logic with exponential backoff
- Error logging
- Graceful fallbacks
- User-friendly error messages

Tool errors are caught by the orchestrator and returned to the LLM for appropriate handling.

---

## Adding New Tools

To add a new tool:

1. **Create handler function** in `backend/tools/`:
   ```python
   def my_new_tool_handler(arg1: str, arg2: int) -> dict:
       # Tool logic
       return {"result": "..."}
   ```

2. **Add function definition** in `backend/llm/functions.py`:
   ```python
   {
       "name": "my_new_tool",
       "description": "...",
       "parameters": {...}
   }
   ```

3. **Register handler** in `backend/tools/register_handlers.py`:
   ```python
   orchestrator.register_function_handler("my_new_tool", my_new_tool_handler)
   ```

4. **Update system prompts** in LLM clients to mention the new tool

---

## See Also

- [DATASETS.md](DATASETS.md) - Data sources for tools
- [EVALS.md](EVALS.md) - Testing tool functionality
- [README.md](README.md) - System architecture

