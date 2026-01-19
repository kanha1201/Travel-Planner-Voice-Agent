"""
Function definitions for Groq LLM tool calling
These functions will be called by the LLM to perform actions
"""

from typing import List, Dict

def get_function_definitions() -> List[Dict]:
    """
    Define all functions available to Groq LLM
    
    These functions will be called by the LLM using function calling
    """
    return [
        {
            "type": "function",
            "function": {
                "name": "search_pois",
                "description": "Search for points of interest (POIs) in Jaipur based on user interests and constraints. Use this when you need to find attractions, restaurants, or activities. IMPORTANT: For multi-day trips, use max_results=20 or more to get enough POIs for itinerary building.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "interests": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "User interests (e.g., ['culture', 'food', 'history', 'shopping'])"
                        },
                        "constraints": {
                            "type": "object",
                            "properties": {
                                "budget": {
                                    "type": "string",
                                    "enum": ["budget", "mid-range", "luxury"],
                                    "description": "Budget level"
                                },
                                "pace": {
                                    "type": "string",
                                    "enum": ["relaxed", "moderate", "packed"],
                                    "description": "Travel pace preference"
                                },
                                "indoor_only": {
                                    "type": "boolean",
                                    "description": "Only indoor activities"
                                },
                                "accessibility": {
                                    "type": "boolean",
                                    "description": "Accessibility requirements"
                                }
                            }
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "Maximum number of POIs to return (default: 30)",
                            "default": 30
                        }
                    },
                    "required": ["interests"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "build_itinerary",
                "description": "Build a structured day-wise itinerary from candidate POIs. Use this after searching for POIs to create the actual travel plan. CRITICAL REQUIREMENTS: 1) Pass MANY POI objects (at least 8-10 for 2-day trip, 12-15 for 3-day trip) - DO NOT pass just 2-3 POIs. 2) Include evening activities! Pass POIs suitable for evening (restaurants, markets, cultural venues, night views) along with morning and afternoon attractions. 3) Pass the COMPLETE POI objects returned by search_pois (with id, name, location, visit_duration_minutes, distance_km, category fields). 4) DO NOT pass incomplete data like just {\"id\": 1}. The function will intelligently select and schedule the best POIs across morning, afternoon, AND evening time slots based on pace and time constraints.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "candidate_pois": {
                            "type": "array",
                            "description": "List of COMPLETE POI objects from search_pois results. Each POI must have: id, name, location (with lat/lon), visit_duration_minutes, distance_km, category. Pass the FULL objects, not just IDs.",
                            "items": {"type": "object"}
                        },
                        "duration_days": {
                            "type": "integer",
                            "description": "Number of days (1-3)",
                            "minimum": 1,
                            "maximum": 3
                        },
                        "date_range": {
                            "type": "object",
                            "properties": {
                                "start_date": {"type": "string", "format": "date"},
                                "end_date": {"type": "string", "format": "date"}
                            },
                            "description": "Travel dates"
                        },
                        "pace": {
                            "type": "string",
                            "enum": ["relaxed", "moderate", "packed"],
                            "description": "Travel pace"
                        },
                        "daily_start_time": {
                            "type": "string",
                            "description": "Daily start time (e.g., '09:00')",
                            "default": "09:00"
                        },
                        "daily_end_time": {
                            "type": "string",
                            "description": "Daily end time (e.g., '20:00')",
                            "default": "20:00"
                        },
                        "edit_mode": {
                            "type": "boolean",
                            "description": "Whether this is an edit to existing itinerary",
                            "default": False
                        },
                        "edit_constraints": {
                            "type": "object",
                            "description": "Constraints for editing (if edit_mode is true)",
                            "properties": {
                                "target_day": {"type": "integer"},
                                "edit_type": {"type": "string"},
                                "preserve_activities": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "List of activity IDs to preserve during edit"
                                }
                            }
                        }
                    },
                    "required": ["candidate_pois", "duration_days", "pace"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "retrieve_city_guidance",
                "description": "**REQUIRED** Retrieve city-specific travel guidance, tips, and recommendations from the knowledge base. You MUST use this tool for: explaining why you chose an activity, answering questions about Jaipur attractions, providing safety tips, explaining local etiquette, or any factual information about Jaipur. Do NOT answer questions about Jaipur without calling this function first.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Query about the city, activity, or topic. Examples: 'Why is City Palace recommended?', 'What should I know about safety in Jaipur?', 'What is the local etiquette?'"
                        },
                        "top_k": {
                            "type": "integer",
                            "description": "Number of results to retrieve (default: 5)",
                            "default": 5,
                            "minimum": 1,
                            "maximum": 10
                        }
                    },
                    "required": ["query"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "ask_clarifying_question",
                "description": "Generate a natural clarifying question when critical information is missing. Use this sparingly - only for essential information needed to create a good itinerary.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "question_type": {
                            "type": "string",
                            "enum": ["budget", "group_size", "arrival_time", "departure_time", "dietary", "accessibility", "accommodation"],
                            "description": "Type of information needed"
                        },
                        "context": {
                            "type": "string",
                            "description": "Additional context for the question"
                        }
                    },
                    "required": ["question_type"]
                }
            }
        }
    ]

