"""Automatic scoring for teacher runs."""
from typing import Dict, Any, Optional
import re
import math


def score_run(output_text: str, logprobs: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Score a teacher run output.
    
    Returns metrics:
    - length: character count
    - word_count: word count
    - entropy: character entropy (if logprobs unavailable)
    - token_entropy: token-level entropy (if logprobs available)
    - has_newlines: boolean
    - has_punctuation: boolean
    """
    metrics: Dict[str, Any] = {}
    
    # Basic length metrics
    metrics["length"] = len(output_text)
    metrics["word_count"] = len(output_text.split())
    metrics["has_newlines"] = "\n" in output_text
    metrics["has_punctuation"] = bool(re.search(r'[.!?;:]', output_text))
    
    # Character entropy (simple approximation)
    if output_text:
        char_counts = {}
        for char in output_text:
            char_counts[char] = char_counts.get(char, 0) + 1
        
        total_chars = len(output_text)
        entropy = 0.0
        for count in char_counts.values():
            prob = count / total_chars
            if prob > 0:
                entropy -= prob * math.log2(prob)
        metrics["char_entropy"] = entropy
    else:
        metrics["char_entropy"] = 0.0
    
    # Token-level entropy from logprobs (if available)
    if logprobs and "token_logprobs" in logprobs:
        token_logprobs = logprobs["token_logprobs"]
        if token_logprobs:
            # Convert logprobs to probabilities and compute entropy
            probs = [math.exp(lp) if lp is not None else 0.0 for lp in token_logprobs]
            probs = [p for p in probs if p > 0]
            if probs:
                entropy = -sum(p * math.log2(p) for p in probs)
                metrics["token_entropy"] = entropy
                metrics["avg_logprob"] = sum(logprobs["token_logprobs"]) / len(token_logprobs) if token_logprobs else None
    
    return metrics

