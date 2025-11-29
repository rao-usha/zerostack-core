"""MMR (Maximal Marginal Relevance) retrieval utility."""
from typing import List, Dict, Any, Optional
import numpy as np


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Compute cosine similarity between two vectors."""
    if not vec1 or not vec2:
        return 0.0
    
    vec1 = np.array(vec1)
    vec2 = np.array(vec2)
    
    dot_product = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    return float(dot_product / (norm1 * norm2))


def mmr_retrieval(
    query_embedding: List[float],
    candidate_chunks: List[Dict[str, Any]],
    lambda_param: float = 0.5,
    top_k: int = 5
) -> List[str]:
    """
    Maximal Marginal Relevance (MMR) retrieval.
    
    Balances relevance to query and diversity among selected chunks.
    
    Args:
        query_embedding: Query vector embedding
        candidate_chunks: List of chunk dicts with 'id' and 'embedding' keys
        lambda_param: Balance parameter (0.0 = pure relevance, 1.0 = pure diversity)
        top_k: Number of chunks to retrieve
    
    Returns:
        List of chunk IDs selected by MMR
    """
    if not candidate_chunks or not query_embedding:
        return []
    
    # Filter chunks with embeddings
    chunks_with_embeddings = [
        c for c in candidate_chunks 
        if c.get('embedding') and isinstance(c['embedding'], list)
    ]
    
    if not chunks_with_embeddings:
        return []
    
    selected_ids = []
    remaining_chunks = chunks_with_embeddings.copy()
    
    # First chunk: highest relevance
    if remaining_chunks:
        relevance_scores = [
            cosine_similarity(query_embedding, c['embedding'])
            for c in remaining_chunks
        ]
        best_idx = max(range(len(remaining_chunks)), key=lambda i: relevance_scores[i])
        selected_ids.append(remaining_chunks[best_idx]['id'])
        remaining_chunks.pop(best_idx)
    
    # Subsequent chunks: MMR score
    while len(selected_ids) < top_k and remaining_chunks:
        best_score = float('-inf')
        best_idx = None
        
        for i, candidate in enumerate(remaining_chunks):
            # Relevance to query
            relevance = cosine_similarity(query_embedding, candidate['embedding'])
            
            # Max similarity to already selected chunks
            max_similarity = 0.0
            for selected_chunk in chunks_with_embeddings:
                if selected_chunk['id'] in selected_ids:
                    similarity = cosine_similarity(candidate['embedding'], selected_chunk['embedding'])
                    max_similarity = max(max_similarity, similarity)
            
            # MMR score: lambda * relevance - (1 - lambda) * max_similarity
            mmr_score = lambda_param * relevance - (1 - lambda_param) * max_similarity
            
            if mmr_score > best_score:
                best_score = mmr_score
                best_idx = i
        
        if best_idx is not None:
            selected_ids.append(remaining_chunks[best_idx]['id'])
            remaining_chunks.pop(best_idx)
        else:
            break
    
    return selected_ids


def simple_retrieval(
    query_embedding: List[float],
    candidate_chunks: List[Dict[str, Any]],
    top_k: int = 5
) -> List[str]:
    """
    Simple relevance-based retrieval (no diversity).
    
    Args:
        query_embedding: Query vector embedding
        candidate_chunks: List of chunk dicts with 'id' and 'embedding' keys
        top_k: Number of chunks to retrieve
    
    Returns:
        List of chunk IDs sorted by relevance
    """
    if not candidate_chunks or not query_embedding:
        return []
    
    # Filter chunks with embeddings
    chunks_with_embeddings = [
        c for c in candidate_chunks 
        if c.get('embedding') and isinstance(c['embedding'], list)
    ]
    
    if not chunks_with_embeddings:
        return []
    
    # Compute relevance scores
    scored_chunks = [
        {
            'id': c['id'],
            'score': cosine_similarity(query_embedding, c['embedding'])
        }
        for c in chunks_with_embeddings
    ]
    
    # Sort by score descending
    scored_chunks.sort(key=lambda x: x['score'], reverse=True)
    
    # Return top_k IDs
    return [c['id'] for c in scored_chunks[:top_k]]

