# Datasets Reference

This document lists all datasets and data sources used in the Voice Travel Planner system.

## Overview

The system uses multiple data sources:
1. **RAG Knowledge Base**: Travel guides from Wikivoyage and Wikipedia
2. **POI Database**: OpenStreetMap (OSM) for points of interest
3. **Embeddings**: Pre-trained sentence-transformers model

---

## 1. RAG Knowledge Base

### Source: Wikivoyage

**URL**: https://en.wikivoyage.org/wiki/Jaipur

**Content**:
- Travel guide sections:
  - Understand (overview, history, culture)
  - Get in (transportation)
  - Get around (local transport)
  - See (attractions)
  - Do (activities)
  - Buy (shopping)
  - Eat (restaurants)
  - Drink (nightlife)
  - Sleep (accommodations)
  - Stay safe (safety tips)
  - Connect (communication)
  - Go next (nearby destinations)

**Format**: HTML → Parsed JSON → Chunked text

**Storage**: 
- Raw: `backend/data/raw/jaipur/wikivoyage_jaipur.json`
- Processed: ChromaDB vector database

**Ingestion**: `backend/rag/data_ingestion.py`

**Metadata Preserved**:
- Section names
- Source URLs
- Section anchors (for deep linking)

---

### Source: Wikipedia

**URL**: https://en.wikipedia.org/wiki/Jaipur

**Content**:
- Comprehensive city information:
  - History
  - Geography
  - Demographics
  - Economy
  - Culture
  - Tourism
  - Notable landmarks

**Format**: HTML → Parsed JSON → Chunked text

**Storage**: 
- Raw: `backend/data/raw/jaipur/wikipedia_jaipur.json` (if fetched)
- Processed: ChromaDB vector database

**Ingestion**: `backend/rag/data_ingestion.py`

**Note**: Wikipedia ingestion is optional and can be added to the pipeline.

---

### Vector Database: ChromaDB

**Location**: `backend/data/chroma_db/`

**Collection**: `jaipur_travel_guides`

**Embedding Model**: `all-MiniLM-L6-v2`
- **Dimensions**: 384
- **Provider**: sentence-transformers
- **Size**: ~80MB (downloads on first use)

**Chunking Strategy**:
- **Chunk Size**: ~500 tokens
- **Overlap**: 50 tokens between chunks
- **Method**: Semantic chunking (preserves context)

**Metadata Fields**:
- `source`: "Wikivoyage" or "Wikipedia"
- `url`: Source URL
- `section`: Section name
- `section_anchor`: Anchor for deep linking
- `chunk_index`: Chunk position in document

**Retrieval**: Top-k semantic search (default: k=3)

---

## 2. POI Database: OpenStreetMap

### Source: OpenStreetMap (OSM)

**API**: Overpass API
- **Endpoint**: https://overpass-api.de/api/interpreter
- **Query Language**: Overpass QL

**Data Types Retrieved**:
- **Tourism**: Attractions, museums, monuments
- **Amenities**: Restaurants, cafes, hotels
- **Shops**: Shopping centers, markets
- **Historic**: Historical sites, heritage buildings
- **Leisure**: Parks, gardens, entertainment

**Query Parameters**:
- **Location**: Jaipur bounding box (26.7°N to 27.0°N, 75.6°E to 76.0°E)
- **Categories**: Filtered by user interests
- **Tags**: OSM tags (tourism, amenity, shop, historic, leisure)

**Data Fields Extracted**:
- `id`: OSM node ID
- `name`: POI name
- `lat`, `lon`: Coordinates
- `category`: OSM category
- `tags`: Additional OSM tags (opening hours, rating, etc.)

**Distance Calculation**:
- From Jaipur center: 26.9124°N, 75.7873°E
- Haversine formula for distance

**Visit Duration Estimation**:
- Based on category:
  - Museums: 60-120 minutes
  - Monuments: 30-60 minutes
  - Restaurants: 60-90 minutes
  - Parks: 30-60 minutes
  - Shops: 30-45 minutes

**Source Attribution**:
- `source`: "openstreetmap"
- `source_url`: `https://www.openstreetmap.org/node/{node_id}`

**Caching**: 7 days TTL (POIs don't change frequently)

**Handler**: `backend/tools/poi_search.py`

---

## 3. Embedding Model

### Model: all-MiniLM-L6-v2

**Provider**: sentence-transformers

**Specifications**:
- **Dimensions**: 384
- **Model Size**: ~80MB
- **Language**: English
- **Task**: Semantic similarity

**Usage**:
- RAG chunk embeddings
- Query embeddings for retrieval
- Semantic search in ChromaDB

**Download**: Automatic on first use (via sentence-transformers)

**Storage**: Cached in `~/.cache/huggingface/transformers/`

---

## 4. Data Processing Pipeline

### Ingestion Flow

```
Wikivoyage/Wikipedia HTML
    ↓
BeautifulSoup Parsing
    ↓
Section Extraction
    ↓
JSON Storage (raw/)
    ↓
Text Chunking (~500 tokens)
    ↓
Embedding Generation (all-MiniLM-L6-v2)
    ↓
ChromaDB Storage
    ↓
Vector Database (chroma_db/)
```

### Chunking Details

**Strategy**: Semantic chunking with overlap
- Preserves sentence boundaries
- Maintains context across chunks
- Overlap ensures continuity

**Metadata Preservation**:
- Source attribution
- Section information
- URL for citations

---

## 5. Data Updates

### RAG Knowledge Base

**Update Frequency**: Manual (when needed)

**Update Process**:
```bash
cd backend
python -m rag.ingest_pipeline
```

**When to Update**:
- New travel guide content available
- Major changes to Jaipur attractions
- Data quality improvements

### POI Database

**Update Frequency**: Real-time (via OpenStreetMap API)

**Caching**: 7 days (balance between freshness and API calls)

**Manual Refresh**: Clear cache or wait for TTL expiry

---

## 6. Data Quality

### RAG Data

**Quality Measures**:
- Source verification (official travel guides)
- Citation tracking (URLs preserved)
- Section metadata (for context)

**Limitations**:
- Static snapshot (not real-time)
- English only
- Focus on tourist information

### POI Data

**Quality Measures**:
- OpenStreetMap community-maintained
- Real-time updates
- Geographic accuracy

**Limitations**:
- Incomplete data for some POIs
- Opening hours may be missing
- Ratings not always available

---

## 7. Data Privacy

### User Data

**Session Data**:
- Stored in memory (not persisted)
- Contains conversation history
- Includes itinerary and sources
- Cleared on session timeout (30 minutes)

**No Personal Data**: System does not collect or store personal information.

### External Data

**RAG Data**: Public domain (Wikivoyage, Wikipedia)

**POI Data**: OpenStreetMap (ODbL license)

**Embeddings**: Pre-trained model (no user data)

---

## 8. Data Sources Summary

| Source | Type | Update Frequency | License | Location |
|--------|------|------------------|---------|----------|
| Wikivoyage | Travel Guide | Manual | CC BY-SA 3.0 | `data/raw/jaipur/` |
| Wikipedia | Encyclopedia | Manual | CC BY-SA 3.0 | `data/raw/jaipur/` |
| OpenStreetMap | POI Database | Real-time | ODbL | API calls |
| ChromaDB | Vector DB | On ingestion | Apache 2.0 | `data/chroma_db/` |
| all-MiniLM-L6-v2 | Embeddings | Static | Apache 2.0 | HuggingFace cache |

---

## 9. Adding New Data Sources

To add a new data source:

1. **Create fetcher** in `backend/rag/data_ingestion.py`:
   ```python
   def fetch_new_source(self) -> Dict:
       # Fetch and parse data
       return parsed_data
   ```

2. **Update ingestion pipeline** in `backend/rag/ingest_pipeline.py`:
   ```python
   fetcher.fetch_new_source()
   ```

3. **Re-run ingestion**:
   ```bash
   python -m rag.ingest_pipeline
   ```

4. **Verify** in ChromaDB that new data is indexed

---

## See Also

- [TOOLS.md](TOOLS.md) - Tools that use these datasets
- [README.md](README.md) - System architecture
- [EVALS.md](EVALS.md) - Testing data quality

