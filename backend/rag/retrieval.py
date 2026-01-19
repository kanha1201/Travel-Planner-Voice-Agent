"""
RAG retrieval module for querying the vector store
"""

from .vector_store import VectorStore
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class RAGRetriever:
    """Retrieves relevant context from RAG system"""
    
    def __init__(self):
        """Initialize RAG retriever"""
        self.vector_store = VectorStore()
    
    def retrieve_context(self, query: str, city: str = "Jaipur", 
                        top_k: int = 5, min_score: float = 0.5) -> List[Dict]:
        """
        Retrieve relevant context for a query
        
        Args:
            query: User query
            city: City name (default: Jaipur)
            top_k: Number of chunks to retrieve
            min_score: Minimum similarity score
        
        Returns:
            List of relevant chunks with citations
        """
        # Query vector store
        chunks = self.vector_store.query(
            query_text=query,
            city=city,
            top_k=top_k,
            min_score=min_score
        )
        
        # Format with citations
        formatted_results = []
        for chunk in chunks:
            formatted_results.append({
                'content': chunk['content'],
                'citation': {
                    'source': chunk['metadata']['source'],
                    'url': chunk['metadata']['source_url'],
                    'section': chunk['metadata']['section'],
                    'section_anchor': chunk['metadata']['section_anchor']
                },
                'similarity_score': chunk['similarity_score']
            })
        
        return formatted_results
    
    def format_context_for_llm(self, chunks: List[Dict]) -> tuple:
        """
        Format retrieved chunks for LLM prompt
        
        Returns:
            (formatted_context_string, citations_list)
        """
        context_parts = []
        citations = []
        
        for idx, chunk in enumerate(chunks, 1):
            context_parts.append(f"[Source {idx}]: {chunk['content']}")
            citations.append({
                'index': idx,
                'source': chunk['citation']['source'],
                'url': chunk['citation']['url'],
                'section': chunk['citation']['section'],
                'anchor': chunk['citation']['section_anchor']
            })
        
        formatted_context = "\n\n".join(context_parts)
        return formatted_context, citations


if __name__ == "__main__":
    # Test retrieval
    logging.basicConfig(level=logging.INFO)
    retriever = RAGRetriever()
    
    test_queries = [
        "What are the must-visit cultural attractions in Jaipur?",
        "What should I know about safety in Jaipur?",
        "What is the local etiquette I should follow?"
    ]
    
    for query in test_queries:
        logger.info(f"\nQuery: {query}")
        results = retriever.retrieve_context(query, top_k=3)
        logger.info(f"Retrieved {len(results)} results")
        
        context, citations = retriever.format_context_for_llm(results)
        logger.info(f"Citations: {len(citations)}")
        for citation in citations:
            logger.info(f"  - {citation['source']}: {citation['section']}")

