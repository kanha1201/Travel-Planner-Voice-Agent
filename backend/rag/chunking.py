"""
Text chunking module for splitting content into semantic chunks
"""

import tiktoken
from typing import List, Dict
import re
import logging

logger = logging.getLogger(__name__)


class TextChunker:
    """Chunks text into semantic pieces with metadata"""
    
    def __init__(self, max_tokens: int = 500, overlap_tokens: int = 50):
        self.max_tokens = max_tokens
        self.overlap_tokens = overlap_tokens
        # Use cl100k_base encoding (GPT-4 tokenizer)
        try:
            self.encoding = tiktoken.get_encoding("cl100k_base")
        except Exception:
            logger.warning("Could not load tiktoken, using fallback token counting")
            self.encoding = None
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        if self.encoding:
            return len(self.encoding.encode(text))
        else:
            # Fallback: approximate 1 token = 4 characters
            return len(text) // 4
    
    def chunk_by_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        # Simple sentence splitting (can be improved with nltk)
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def chunk_text(self, text: str, section_name: str = "", 
                   chunk_index_offset: int = 0) -> List[Dict]:
        """
        Chunk text into semantic chunks with metadata
        
        Strategy:
        1. Split by sentences
        2. Group sentences into chunks up to max_tokens
        3. Add overlap between chunks
        """
        sentences = self.chunk_by_sentences(text)
        
        if not sentences:
            return []
        
        chunks = []
        current_chunk = []
        current_tokens = 0
        chunk_index = chunk_index_offset
        
        for sentence in sentences:
            sentence_tokens = self.count_tokens(sentence)
            
            # If single sentence exceeds max, split it
            if sentence_tokens > self.max_tokens:
                # Save current chunk if exists
                if current_chunk:
                    chunks.append({
                        'content': ' '.join(current_chunk),
                        'chunk_index': chunk_index,
                        'section': section_name,
                        'tokens': current_tokens
                    })
                    chunk_index += 1
                    current_chunk = []
                    current_tokens = 0
                
                # Split long sentence (simple word-based split)
                words = sentence.split()
                temp_chunk = []
                temp_tokens = 0
                
                for word in words:
                    word_tokens = self.count_tokens(word + ' ')
                    if temp_tokens + word_tokens > self.max_tokens:
                        if temp_chunk:
                            chunks.append({
                                'content': ' '.join(temp_chunk),
                                'chunk_index': chunk_index,
                                'section': section_name,
                                'tokens': temp_tokens
                            })
                            chunk_index += 1
                            temp_chunk = []
                            temp_tokens = 0
                        # Add overlap
                        overlap_words = int(len(temp_chunk) * 0.2) if temp_chunk else 0
                        temp_chunk = temp_chunk[-overlap_words:] if overlap_words > 0 else []
                        temp_tokens = self.count_tokens(' '.join(temp_chunk))
                    
                    temp_chunk.append(word)
                    temp_tokens += word_tokens
                
                if temp_chunk:
                    current_chunk = temp_chunk
                    current_tokens = temp_tokens
            else:
                # Check if adding sentence exceeds limit
                if current_tokens + sentence_tokens > self.max_tokens:
                    # Save current chunk
                    chunks.append({
                        'content': ' '.join(current_chunk),
                        'chunk_index': chunk_index,
                        'section': section_name,
                        'tokens': current_tokens
                    })
                    chunk_index += 1
                    
                    # Start new chunk with overlap
                    overlap_sentences = max(1, int(len(current_chunk) * 0.2))  # 20% overlap
                    overlap_text = ' '.join(current_chunk[-overlap_sentences:]) if current_chunk else ''
                    current_chunk = [overlap_text, sentence] if overlap_text else [sentence]
                    current_tokens = self.count_tokens(' '.join(current_chunk))
                else:
                    current_chunk.append(sentence)
                    current_tokens += sentence_tokens
        
        # Add final chunk
        if current_chunk:
            chunks.append({
                'content': ' '.join(current_chunk),
                'chunk_index': chunk_index,
                'section': section_name,
                'tokens': current_tokens
            })
        
        return chunks
    
    def chunk_sections(self, sections: Dict, source_url: str, 
                      source_name: str) -> List[Dict]:
        """
        Chunk all sections from a data source
        """
        all_chunks = []
        global_chunk_index = 0
        
        for section_name, section_data in sections.items():
            content = section_data.get('content', '')
            if not content or len(content.strip()) < 50:  # Skip very short sections
                continue
            
            chunks = self.chunk_text(
                text=content,
                section_name=section_name,
                chunk_index_offset=global_chunk_index
            )
            
            # Add metadata to each chunk
            for chunk in chunks:
                chunk.update({
                    'source': source_name,
                    'source_url': source_url,
                    'section_anchor': section_data.get('anchor', ''),
                    'city': 'Jaipur'
                })
            
            all_chunks.extend(chunks)
            global_chunk_index += len(chunks)
        
        return all_chunks


if __name__ == "__main__":
    # Test chunking
    logging.basicConfig(level=logging.INFO)
    chunker = TextChunker(max_tokens=500, overlap_tokens=50)
    test_text = "This is a test. " * 100
    chunks = chunker.chunk_text(test_text, "Test Section")
    logger.info(f"Created {len(chunks)} chunks")
    for i, chunk in enumerate(chunks[:3]):
        logger.info(f"Chunk {i}: {chunk['tokens']} tokens")















