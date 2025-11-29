"""Embedding generation."""
from typing import List, Optional
from ..config import settings


class Embedder:
    """Generate embeddings for text chunks."""
    
    def __init__(self):
        """Initialize embedder."""
        self.model = None
        if settings.EMBEDDINGS_ENABLED:
            try:
                from sentence_transformers import SentenceTransformer
                self.model = SentenceTransformer('all-MiniLM-L6-v2')
            except ImportError:
                print("Warning: sentence-transformers not installed, embeddings disabled")
                settings.EMBEDDINGS_ENABLED = False
    
    def embed(self, texts: List[str]) -> List[Optional[List[float]]]:
        """
        Generate embeddings for texts.
        
        Returns:
            List of embedding vectors (or None if disabled)
        """
        if not settings.EMBEDDINGS_ENABLED or not self.model:
            return [None] * len(texts)
        
        embeddings = self.model.encode(texts, convert_to_numpy=True)
        return embeddings.tolist()

