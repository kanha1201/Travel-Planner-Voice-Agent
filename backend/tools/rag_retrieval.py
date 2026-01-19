"""
RAG Retrieval Tool - Retrieves city guidance from RAG system
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from rag.retrieval import RAGRetriever
from typing import Dict
import logging

logger = logging.getLogger(__name__)


class RAGRetrievalTool:
    """Tool for retrieving city guidance from RAG system"""
    
    def __init__(self):
        self.retriever = RAGRetriever()
        
        # Validate RAG system is working
        self._validate_rag_system()
        logger.info("✅ RAG Retrieval Tool initialized and validated")
    
    def _validate_rag_system(self):
        """Validate that RAG system has data and is working"""
        try:
            # Check vector store has data
            stats = self.retriever.vector_store.get_collection_stats()
            total_chunks = stats.get('total_chunks', 0)
            
            if total_chunks == 0:
                raise ValueError(
                    "❌ RAG SYSTEM ERROR: Vector database is empty! "
                    "Run Phase 1 ingestion pipeline first: python -m rag.ingest_pipeline"
                )
            
            logger.info(f"✅ RAG System Status: {total_chunks} chunks available in vector database")
            
            # Test retrieval with a simple query
            test_results = self.retriever.retrieve_context(
                query="Jaipur",
                city="Jaipur",
                top_k=1,
                min_score=0.3  # Lower threshold for validation
            )
            
            if not test_results:
                raise ValueError(
                    "❌ RAG SYSTEM ERROR: Vector database retrieval failed! "
                    "No results returned from test query."
                )
            
            logger.info(f"✅ RAG System Validation: Successfully retrieved {len(test_results)} test results")
            
        except Exception as e:
            logger.error(f"❌ RAG SYSTEM VALIDATION FAILED: {e}")
            raise
    
    def retrieve_city_guidance(self, query: str, top_k: int = 5) -> Dict:
        """
        Retrieve city guidance for a query
        
        Args:
            query: Query string
            top_k: Number of results
        
        Returns:
            Dict with chunks and citations
        
        Raises:
            ValueError: If RAG system is not working properly
        """
        logger.info(f"🔍 RAG Retrieval: Querying for '{query}'")
        
        chunks = self.retriever.retrieve_context(
            query=query,
            city="Jaipur",
            top_k=top_k,
            min_score=0.5
        )
        
        # Validate we got results
        if not chunks:
            logger.warning(f"⚠️  RAG Retrieval: No results found for query '{query}'")
            # Don't fail, but log warning
            return {
                "chunks": [],
                "citations": [],
                "count": 0,
                "warning": f"No relevant content found for query: {query}"
            }
        
        # Format for LLM
        formatted_chunks = []
        citations = []
        
        for idx, chunk in enumerate(chunks, 1):
            formatted_chunks.append({
                "content": chunk["content"],
                "similarity_score": chunk["similarity_score"],
                "citation": chunk["citation"]
            })
            citations.append(chunk["citation"])
        
        logger.info(f"✅ RAG Retrieval SUCCESS: Retrieved {len(formatted_chunks)} chunks with citations")
        logger.info(f"   Top similarity score: {formatted_chunks[0]['similarity_score']:.3f}")
        logger.info(f"   Sources: {[c['source'] for c in citations]}")
        
        return {
            "chunks": formatted_chunks,
            "citations": citations,
            "count": len(formatted_chunks),
            "status": "success"
        }


# Function handler for Groq
def retrieve_city_guidance_handler(query: str, top_k: int = 5) -> Dict:
    """
    Handler function for Groq function calling
    
    Args:
        query: Query string
        top_k: Number of results
    
    Returns:
        Dict with chunks and citations
    """
    tool = RAGRetrievalTool()
    return tool.retrieve_city_guidance(query, top_k)


if __name__ == "__main__":
    # Test RAG retrieval
    logging.basicConfig(level=logging.INFO)
    tool = RAGRetrievalTool()
    
    result = tool.retrieve_city_guidance(
        "What are the must-visit cultural attractions in Jaipur?",
        top_k=3
    )
    
    logger.info(f"Retrieved {result['count']} chunks")
    for chunk in result['chunks']:
        logger.info(f"- {chunk['citation']['section']}: {chunk['content'][:100]}...")

