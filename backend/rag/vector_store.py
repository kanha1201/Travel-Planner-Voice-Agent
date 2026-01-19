"""
Vector store module for storing and retrieving embeddings
"""

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Optional
import os
from pathlib import Path
import logging
import warnings

# Suppress ChromaDB telemetry warnings
warnings.filterwarnings("ignore", category=UserWarning, module="chromadb")

logger = logging.getLogger(__name__)
# Suppress ChromaDB telemetry logging
logging.getLogger("chromadb").setLevel(logging.ERROR)


class VectorStore:
    """Manages vector database for RAG"""
    
    def __init__(self, collection_name: str = "jaipur_travel_guides",
                 persist_directory: str = "data/chroma_db"):
        """
        Initialize ChromaDB vector store
        """
        # Create persist directory
        Path(persist_directory).mkdir(parents=True, exist_ok=True)
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}  # Cosine similarity
        )
        
        # Initialize embedding model
        # Using a lightweight model for now (can upgrade to larger model)
        logger.info("Loading embedding model...")
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.embedding_dim = 384  # Dimension for all-MiniLM-L6-v2
        logger.info("✅ Embedding model loaded")
        
        logger.info(f"✅ Vector store initialized: {collection_name}")
        logger.info(f"   Collection size: {self.collection.count()}")
    
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for texts"""
        embeddings = self.embedding_model.encode(texts, show_progress_bar=True)
        return embeddings.tolist()
    
    def add_chunks(self, chunks: List[Dict], batch_size: int = 100):
        """
        Add chunks to vector store
        
        Args:
            chunks: List of chunk dictionaries with 'content' and metadata
            batch_size: Number of chunks to process at once
        """
        total_chunks = len(chunks)
        logger.info(f"🔄 Adding {total_chunks} chunks to vector store...")
        
        # Process in batches
        for i in range(0, total_chunks, batch_size):
            batch = chunks[i:i + batch_size]
            
            # Extract texts for embedding
            texts = [chunk['content'] for chunk in batch]
            
            # Generate embeddings
            logger.info(f"   Generating embeddings for batch {i//batch_size + 1}...")
            embeddings = self.generate_embeddings(texts)
            
            # Prepare data for ChromaDB
            ids = [f"jaipur_{chunk['section']}_{chunk['chunk_index']}" 
                   for chunk in batch]
            documents = texts
            metadatas = [
                {
                    'city': chunk.get('city', 'Jaipur'),
                    'section': chunk.get('section', ''),
                    'source': chunk.get('source', ''),
                    'source_url': chunk.get('source_url', ''),
                    'section_anchor': chunk.get('section_anchor', ''),
                    'chunk_index': chunk.get('chunk_index', 0),
                    'tokens': chunk.get('tokens', 0)
                }
                for chunk in batch
            ]
            
            # Add to collection
            self.collection.add(
                ids=ids,
                documents=documents,
                metadatas=metadatas,
                embeddings=embeddings
            )
            
            logger.info(f"   ✅ Added batch {i//batch_size + 1} ({len(batch)} chunks)")
        
        logger.info(f"✅ All chunks added! Total: {self.collection.count()}")
    
    def query(self, query_text: str, city: str = "Jaipur", 
              top_k: int = 5, min_score: float = 0.5) -> List[Dict]:
        """
        Query the vector store
        
        Args:
            query_text: Query string
            city: Filter by city (default: Jaipur)
            top_k: Number of results to return
            min_score: Minimum similarity score
        
        Returns:
            List of relevant chunks with metadata
        """
        # Generate query embedding
        query_embedding = self.embedding_model.encode([query_text])[0].tolist()
        
        # Build where filter
        where_filter = {"city": city} if city else None
        
        # Query collection
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where_filter if where_filter else None
        )
        
        # Format results
        retrieved_chunks = []
        if results['ids'] and len(results['ids'][0]) > 0:
            for i in range(len(results['ids'][0])):
                # Convert distance to similarity score (1 - distance for cosine)
                distance = results['distances'][0][i]
                similarity_score = 1 - distance
                
                if similarity_score >= min_score:
                    retrieved_chunks.append({
                        'content': results['documents'][0][i],
                        'metadata': results['metadatas'][0][i],
                        'similarity_score': similarity_score,
                        'id': results['ids'][0][i]
                    })
        
        return retrieved_chunks
    
    def get_collection_stats(self) -> Dict:
        """Get statistics about the collection"""
        count = self.collection.count()
        return {
            'total_chunks': count,
            'collection_name': self.collection.name
        }


if __name__ == "__main__":
    # Test vector store
    logging.basicConfig(level=logging.INFO)
    store = VectorStore()
    stats = store.get_collection_stats()
    logger.info(f"Collection stats: {stats}")





