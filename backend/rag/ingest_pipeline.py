"""
Complete RAG data ingestion pipeline for Jaipur
Run this script to fetch, chunk, and store travel guide data
"""

import logging
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from rag.data_ingestion import JaipurDataFetcher
from rag.chunking import TextChunker
from rag.vector_store import VectorStore

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_ingestion_pipeline():
    """Complete RAG data ingestion pipeline"""
    logger.info("=" * 60)
    logger.info("RAG DATA INGESTION PIPELINE - JAIPUR")
    logger.info("=" * 60)
    
    # Step 1: Fetch data
    logger.info("\n📥 Step 1: Fetching data...")
    fetcher = JaipurDataFetcher()
    try:
        data = fetcher.fetch_all()
    except Exception as e:
        logger.error(f"Failed to fetch data: {e}")
        return False
    
    # Step 2: Chunk data
    logger.info("\n✂️  Step 2: Chunking data...")
    chunker = TextChunker(max_tokens=500, overlap_tokens=50)
    all_chunks = []
    
    # Chunk Wikivoyage data
    if data.get('wikivoyage'):
        try:
            wikivoyage_chunks = chunker.chunk_sections(
                sections=data['wikivoyage'],
                source_url="https://en.wikivoyage.org/wiki/Jaipur",
                source_name="wikivoyage"
            )
            all_chunks.extend(wikivoyage_chunks)
            logger.info(f"   ✅ Created {len(wikivoyage_chunks)} chunks from Wikivoyage")
        except Exception as e:
            logger.error(f"Failed to chunk Wikivoyage data: {e}")
    
    # Chunk Wikipedia data
    if data.get('wikipedia'):
        try:
            wikipedia_chunks = chunker.chunk_sections(
                sections=data['wikipedia'],
                source_url="https://en.wikipedia.org/wiki/Jaipur",
                source_name="wikipedia"
            )
            all_chunks.extend(wikipedia_chunks)
            logger.info(f"   ✅ Created {len(wikipedia_chunks)} chunks from Wikipedia")
        except Exception as e:
            logger.warning(f"Failed to chunk Wikipedia data: {e}")
    
    logger.info(f"\n   Total chunks: {len(all_chunks)}")
    
    if not all_chunks:
        logger.error("No chunks created! Cannot proceed.")
        return False
    
    # Step 3: Store in vector DB
    logger.info("\n💾 Step 3: Storing in vector database...")
    try:
        vector_store = VectorStore()
        
        # Clear existing collection (optional - comment out if you want to keep old data)
        # vector_store.collection.delete()
        
        vector_store.add_chunks(all_chunks, batch_size=50)
    except Exception as e:
        logger.error(f"Failed to store in vector DB: {e}")
        return False
    
    # Step 4: Verify
    logger.info("\n✅ Step 4: Verification...")
    try:
        stats = vector_store.get_collection_stats()
        logger.info(f"   Collection size: {stats['total_chunks']} chunks")
        
        # Test query
        logger.info("\n🔍 Testing retrieval...")
        test_query = "What are the must-visit cultural attractions in Jaipur?"
        results = vector_store.query(test_query, top_k=3)
        logger.info(f"   Query: '{test_query}'")
        logger.info(f"   Retrieved {len(results)} results:")
        for i, result in enumerate(results, 1):
            logger.info(f"   {i}. Score: {result['similarity_score']:.3f}")
            logger.info(f"      Section: {result['metadata']['section']}")
            logger.info(f"      Preview: {result['content'][:100]}...")
        
        logger.info("\n" + "=" * 60)
        logger.info("✅ INGESTION PIPELINE COMPLETE!")
        logger.info("=" * 60)
        return True
        
    except Exception as e:
        logger.error(f"Verification failed: {e}")
        return False


if __name__ == "__main__":
    success = run_ingestion_pipeline()
    sys.exit(0 if success else 1)















