"""Text chunking for retrieval."""
from typing import List
from ..config import settings


class Chunker:
    """Chunk text for retrieval/embeddings."""
    
    def __init__(self, chunk_size: int = 500, overlap: int = 50):
        """Initialize chunker."""
        self.chunk_size = chunk_size
        self.overlap = overlap
    
    def chunk(self, text: str) -> List[str]:
        """
        Chunk text into overlapping segments.
        
        Returns:
            List of chunk texts
        """
        chunks = []
        
        # Simple sentence-aware chunking
        sentences = text.split('. ')
        current_chunk = []
        current_length = 0
        
        for sentence in sentences:
            sentence_length = len(sentence)
            
            if current_length + sentence_length > self.chunk_size and current_chunk:
                # Save current chunk
                chunk_text = '. '.join(current_chunk)
                if chunk_text:
                    chunks.append(chunk_text)
                
                # Start new chunk with overlap
                overlap_sentences = current_chunk[-self.overlap//50:] if self.overlap > 0 else []
                current_chunk = overlap_sentences + [sentence]
                current_length = sum(len(s) for s in current_chunk)
            else:
                current_chunk.append(sentence)
                current_length += sentence_length
        
        # Add final chunk
        if current_chunk:
            chunk_text = '. '.join(current_chunk)
            if chunk_text:
                chunks.append(chunk_text)
        
        return chunks if chunks else [text]

