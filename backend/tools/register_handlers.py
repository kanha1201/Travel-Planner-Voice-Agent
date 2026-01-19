"""
Register all function handlers with the LLM orchestrator
"""

from llm.orchestrator import LLMOrchestrator
from tools.poi_search import search_pois_handler
from tools.itinerary_builder import build_itinerary_handler
from tools.rag_retrieval import retrieve_city_guidance_handler
from tools.question_generator import ask_clarifying_question_handler
import logging

logger = logging.getLogger(__name__)


def register_all_handlers(orchestrator: LLMOrchestrator):
    """
    Register all function handlers with the orchestrator
    
    Args:
        orchestrator: LLMOrchestrator instance
    """
    orchestrator.register_function_handler("search_pois", search_pois_handler)
    orchestrator.register_function_handler("build_itinerary", build_itinerary_handler)
    orchestrator.register_function_handler("retrieve_city_guidance", retrieve_city_guidance_handler)
    orchestrator.register_function_handler("ask_clarifying_question", ask_clarifying_question_handler)
    
    logger.info("✅ All function handlers registered")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    orchestrator = LLMOrchestrator()
    register_all_handlers(orchestrator)
    
    logger.info("Handlers registered successfully")











