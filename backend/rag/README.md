# RAG Data Pre-processing (Phase 1)

This module handles fetching, chunking, and storing travel guide data for Jaipur in a vector database.

## Components

- **data_ingestion.py**: Fetches data from Wikivoyage and Wikipedia
- **chunking.py**: Splits text into semantic chunks with metadata
- **vector_store.py**: Manages ChromaDB vector database and embeddings
- **retrieval.py**: Retrieves relevant context from vector store
- **ingest_pipeline.py**: Complete ingestion pipeline script

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the ingestion pipeline:
```bash
cd backend
python -m rag.ingest_pipeline
```

## What It Does

1. **Fetches Data**: Downloads Jaipur travel guides from:
   - Wikivoyage (primary source)
   - Wikipedia (secondary source)

2. **Chunks Text**: Splits content into ~500 token chunks with:
   - Section metadata
   - Source URLs for citations
   - Overlap between chunks for context

3. **Generates Embeddings**: Creates vector embeddings using `all-MiniLM-L6-v2` model

4. **Stores in Vector DB**: Saves chunks in ChromaDB with metadata

5. **Verifies**: Tests retrieval with sample queries

## Output

- Raw data: `data/raw/jaipur/` (JSON files)
- Vector DB: `data/chroma_db/` (ChromaDB database)
- Collection: `jaipur_travel_guides`

## Testing

After ingestion, test retrieval:
```python
from rag.retrieval import RAGRetriever

retriever = RAGRetriever()
results = retriever.retrieve_context(
    "What are the must-visit cultural attractions in Jaipur?",
    top_k=5
)
```

## Notes

- First run will download the embedding model (~80MB)
- Ingestion takes 5-10 minutes depending on network speed
- Vector DB persists between runs (no need to re-ingest unless data changes)















