"""
Question Generator Tool - Generates clarifying questions
"""

from typing import Dict
import logging

logger = logging.getLogger(__name__)


def ask_clarifying_question_handler(question_type: str, context: str = "") -> Dict:
    """
    Handler function for generating clarifying questions
    
    Args:
        question_type: Type of question needed
        context: Additional context
    
    Returns:
        Dict with the question
    """
    question_templates = {
        "budget": "What's your budget range for this trip? (budget, mid-range, or luxury)",
        "group_size": "How many people will be traveling?",
        "arrival_time": "What time do you plan to arrive in Jaipur?",
        "departure_time": "What time do you need to depart from Jaipur?",
        "dietary": "Do you have any dietary restrictions or preferences?",
        "accessibility": "Do you have any accessibility requirements?",
        "accommodation": "Do you have a preferred area for accommodation?"
    }
    
    question = question_templates.get(question_type, "Could you provide more details about your preferences?")
    
    if context:
        question = f"{question} ({context})"
    
    logger.info(f"Generated question: {question}")
    
    return {
        "question": question,
        "question_type": question_type
    }











