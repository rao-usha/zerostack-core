"""Semantic hashing and drift detection utilities."""
from typing import List, Optional, Dict, Any
import hashlib
import json
import numpy as np


def compute_simhash(text: str, hash_bits: int = 64) -> str:
    """
    Compute SimHash (locality-sensitive hash) for near-duplicate detection.
    
    SimHash produces similar hashes for similar texts, enabling efficient
    near-duplicate detection.
    
    Args:
        text: Text to hash
        hash_bits: Number of bits in the hash (default: 64)
    
    Returns:
        Hexadecimal string representation of SimHash
    """
    if not text:
        return "0" * (hash_bits // 4)
    
    # Tokenize text (simple word-based)
    words = text.lower().split()
    if not words:
        return "0" * (hash_bits // 4)
    
    # Initialize bit vector
    v = [0] * hash_bits
    
    # For each word, compute hash and update bit vector
    for word in words:
        # Compute hash of word
        word_hash = int(hashlib.md5(word.encode()).hexdigest(), 16)
        
        # Update bit vector
        for i in range(hash_bits):
            if word_hash & (1 << i):
                v[i] += 1
            else:
                v[i] -= 1
    
    # Convert to binary hash
    simhash = 0
    for i in range(hash_bits):
        if v[i] > 0:
            simhash |= (1 << i)
    
    # Return as hex string
    return format(simhash, f'0{hash_bits // 4}x')


def compute_minhash(text: str, num_perm: int = 128) -> List[int]:
    """
    Compute MinHash signature for near-duplicate detection.
    
    MinHash is another locality-sensitive hashing technique.
    
    Args:
        text: Text to hash
        num_perm: Number of permutations (default: 128)
    
    Returns:
        List of hash values (signature)
    """
    if not text:
        return [0] * num_perm
    
    # Tokenize text (simple word-based)
    words = text.lower().split()
    if not words:
        return [0] * num_perm
    
    # Create shingles (n-grams)
    shingles = set()
    for i in range(len(words) - 1):
        shingle = " ".join(words[i:i+2])
        shingles.add(shingle)
    
    if not shingles:
        return [0] * num_perm
    
    # Compute MinHash signature
    signature = []
    for i in range(num_perm):
        min_hash = float('inf')
        for shingle in shingles:
            # Use different hash seeds for each permutation
            hash_value = int(hashlib.sha256(f"{shingle}_{i}".encode()).hexdigest(), 16)
            min_hash = min(min_hash, hash_value)
        signature.append(min_hash)
    
    return signature


def semantic_hash_from_embedding(embedding: List[float], method: str = "simhash") -> str:
    """
    Compute semantic hash from embedding vector.
    
    Args:
        embedding: Embedding vector
        method: Hash method ("simhash" or "minhash")
    
    Returns:
        Hash string
    """
    if not embedding:
        return "0" * 16
    
    if method == "simhash":
        # Convert embedding to text-like representation for SimHash
        # Use quantized values
        quantized = [int(v * 1000) for v in embedding[:64]]  # Use first 64 dimensions
        text_repr = " ".join(str(v) for v in quantized)
        return compute_simhash(text_repr)
    else:
        # MinHash from embedding
        quantized = [int(v * 1000) for v in embedding[:128]]
        text_repr = " ".join(str(v) for v in quantized)
        signature = compute_minhash(text_repr, num_perm=64)
        # Convert signature to hex string
        return hashlib.sha256(json.dumps(signature).encode()).hexdigest()[:16]


def hamming_distance(hash1: str, hash2: str) -> int:
    """
    Compute Hamming distance between two hash strings.
    
    Args:
        hash1: First hash (hex string)
        hash2: Second hash (hex string)
    
    Returns:
        Hamming distance (number of differing bits)
    """
    if len(hash1) != len(hash2):
        return max(len(hash1), len(hash2)) * 4  # Max distance
    
    # Convert hex to binary
    bin1 = bin(int(hash1, 16))[2:].zfill(len(hash1) * 4)
    bin2 = bin(int(hash2, 16))[2:].zfill(len(hash2) * 4)
    
    # Count differing bits
    return sum(c1 != c2 for c1, c2 in zip(bin1, bin2))


def is_near_duplicate(hash1: str, hash2: str, threshold: int = 3) -> bool:
    """
    Check if two semantic hashes represent near-duplicates.
    
    Args:
        hash1: First semantic hash
        hash2: Second semantic hash
        threshold: Maximum Hamming distance for near-duplicate (default: 3)
    
    Returns:
        True if near-duplicate, False otherwise
    """
    if not hash1 or not hash2:
        return False
    
    distance = hamming_distance(hash1, hash2)
    return distance <= threshold


def compute_embedding_centroid(embeddings: List[List[float]]) -> Optional[List[float]]:
    """
    Compute centroid (average) of embedding vectors.
    
    Args:
        embeddings: List of embedding vectors
    
    Returns:
        Centroid vector, or None if no embeddings
    """
    if not embeddings:
        return None
    
    # Filter out None embeddings
    valid_embeddings = [e for e in embeddings if e is not None]
    if not valid_embeddings:
        return None
    
    # Convert to numpy array
    embeddings_array = np.array(valid_embeddings)
    
    # Compute mean along axis 0
    centroid = np.mean(embeddings_array, axis=0)
    
    return centroid.tolist()


def cosine_distance(vec1: List[float], vec2: List[float]) -> float:
    """
    Compute cosine distance between two vectors.
    
    Args:
        vec1: First vector
        vec2: Second vector
    
    Returns:
        Cosine distance (1 - cosine similarity)
    """
    if not vec1 or not vec2 or len(vec1) != len(vec2):
        return 1.0
    
    vec1 = np.array(vec1)
    vec2 = np.array(vec2)
    
    dot_product = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    
    if norm1 == 0 or norm2 == 0:
        return 1.0
    
    cosine_sim = dot_product / (norm1 * norm2)
    return 1.0 - cosine_sim


def detect_concept_drift(
    old_centroid: List[float],
    new_centroid: List[float],
    threshold: float = 0.2
) -> Dict[str, Any]:
    """
    Detect concept drift by comparing embedding centroids.
    
    Args:
        old_centroid: Previous version's embedding centroid
        new_centroid: New version's embedding centroid
        threshold: Cosine distance threshold for drift detection (default: 0.2)
    
    Returns:
        Dictionary with drift detection results:
        {
            "has_drift": bool,
            "distance": float,
            "threshold": float,
            "severity": str  # "none", "low", "medium", "high"
        }
    """
    if not old_centroid or not new_centroid:
        return {
            "has_drift": False,
            "distance": 1.0,
            "threshold": threshold,
            "severity": "none"
        }
    
    distance = cosine_distance(old_centroid, new_centroid)
    has_drift = distance > threshold
    
    # Determine severity
    if distance < threshold:
        severity = "none"
    elif distance < threshold * 1.5:
        severity = "low"
    elif distance < threshold * 2.0:
        severity = "medium"
    else:
        severity = "high"
    
    return {
        "has_drift": has_drift,
        "distance": float(distance),
        "threshold": threshold,
        "severity": severity
    }

