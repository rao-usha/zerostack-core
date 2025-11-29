"""Soft label extraction and aggregation utilities."""
from typing import List, Dict, Any, Optional
import math
from collections import Counter
import numpy as np


def extract_logprobs_to_probs(logprobs: Dict[str, Any]) -> Optional[Dict[str, float]]:
    """
    Extract probability distributions from logprobs.
    
    Args:
        logprobs: Dictionary containing logprobs data (e.g., from OpenAI API)
            Expected format:
            {
                "token_logprobs": [float, ...],
                "top_logprobs": [{"token": str, "logprob": float}, ...],
                "tokens": [str, ...]
            }
    
    Returns:
        Dictionary mapping tokens/classes to probabilities, or None if invalid
    """
    if not logprobs:
        return None
    
    probs = {}
    
    # Extract token-level probabilities
    if "token_logprobs" in logprobs and "tokens" in logprobs:
        token_logprobs = logprobs["token_logprobs"]
        tokens = logprobs["tokens"]
        
        if len(token_logprobs) == len(tokens):
            for token, logprob in zip(tokens, token_logprobs):
                if logprob is not None:
                    prob = math.exp(logprob)
                    probs[token] = prob
    
    # Extract top-k probabilities if available
    if "top_logprobs" in logprobs:
        top_logprobs = logprobs["top_logprobs"]
        if isinstance(top_logprobs, list):
            for entry in top_logprobs:
                if isinstance(entry, dict):
                    token = entry.get("token")
                    logprob = entry.get("logprob")
                    if token and logprob is not None:
                        prob = math.exp(logprob)
                        probs[token] = max(probs.get(token, 0), prob)  # Take max if duplicate
    
    return probs if probs else None


def aggregate_probs_from_runs(runs: List[Dict[str, Any]], method: str = "mean") -> Dict[str, float]:
    """
    Aggregate probability distributions from multiple teacher runs.
    
    Args:
        runs: List of run dicts with 'output_json' containing logprobs
        method: Aggregation method ('mean', 'max', 'weighted_mean')
    
    Returns:
        Aggregated probability distribution
    """
    if not runs:
        return {}
    
    all_probs = []
    weights = []
    
    for run in runs:
        if isinstance(run, dict):
            output_json = run.get("output_json") or {}
            confidence = run.get("confidence", 1.0)
        else:
            # Assume TeacherRun object
            output_json = run.output_json or {}
            confidence = run.confidence or 1.0
        
        logprobs = output_json.get("logprobs")
        if logprobs:
            probs = extract_logprobs_to_probs(logprobs)
            if probs:
                all_probs.append(probs)
                weights.append(confidence)
    
    if not all_probs:
        return {}
    
    # Collect all unique tokens/classes
    all_tokens = set()
    for probs in all_probs:
        all_tokens.update(probs.keys())
    
    # Aggregate probabilities
    aggregated = {}
    
    if method == "mean":
        for token in all_tokens:
            values = [p.get(token, 0.0) for p in all_probs]
            aggregated[token] = sum(values) / len(values)
    
    elif method == "max":
        for token in all_tokens:
            values = [p.get(token, 0.0) for p in all_probs]
            aggregated[token] = max(values)
    
    elif method == "weighted_mean":
        if len(weights) != len(all_probs):
            weights = [1.0] * len(all_probs)
        
        total_weight = sum(weights)
        if total_weight == 0:
            weights = [1.0] * len(all_probs)
            total_weight = len(all_probs)
        
        for token in all_tokens:
            weighted_sum = sum(p.get(token, 0.0) * w for p, w in zip(all_probs, weights))
            aggregated[token] = weighted_sum / total_weight
    
    else:
        raise ValueError(f"Unknown aggregation method: {method}")
    
    # Normalize probabilities
    total = sum(aggregated.values())
    if total > 0:
        aggregated = {k: v / total for k, v in aggregated.items()}
    
    return aggregated


def extract_text_class_probs(text: str, logprobs: Dict[str, Any]) -> Optional[Dict[str, float]]:
    """
    Extract class-level probabilities from text and logprobs.
    
    For classification tasks, maps text outputs to probability distributions over classes.
    
    Args:
        text: Output text (e.g., "Answer A", "low", "high")
        logprobs: Logprobs data from model
    
    Returns:
        Dictionary mapping class labels to probabilities
    """
    if not text or not logprobs:
        return None
    
    # Extract token probabilities
    token_probs = extract_logprobs_to_probs(logprobs)
    if not token_probs:
        return None
    
    # Simple heuristic: if text matches a token exactly, use that token's probability
    # Otherwise, aggregate probabilities of tokens in the text
    text_lower = text.lower().strip()
    
    # Check for exact match
    if text_lower in token_probs:
        return {text_lower: token_probs[text_lower]}
    
    # Aggregate probabilities of tokens that appear in the text
    class_probs = {}
    for token, prob in token_probs.items():
        token_lower = token.lower()
        if token_lower in text_lower or text_lower in token_lower:
            class_probs[text_lower] = class_probs.get(text_lower, 0) + prob
    
    if class_probs:
        # Normalize
        total = sum(class_probs.values())
        if total > 0:
            class_probs = {k: v / total for k, v in class_probs.items()}
        return class_probs
    
    # Fallback: create a distribution with the text as the primary class
    return {text_lower: 1.0}


def create_soft_labels_from_runs(
    runs: List[Dict[str, Any]],
    aggregation_method: str = "weighted_mean",
    include_token_probs: bool = True,
    include_class_probs: bool = True
) -> Dict[str, Any]:
    """
    Create soft labels from multiple teacher runs.
    
    Args:
        runs: List of teacher run dicts or TeacherRun objects
        aggregation_method: Method to aggregate probabilities ('mean', 'max', 'weighted_mean')
        include_token_probs: Whether to include token-level probabilities
        include_class_probs: Whether to include class-level probabilities
    
    Returns:
        Dictionary with soft label data:
        {
            "token_probs": {token: prob, ...},
            "class_probs": {class: prob, ...},
            "num_runs": int,
            "aggregation_method": str
        }
    """
    result = {
        "num_runs": len(runs),
        "aggregation_method": aggregation_method
    }
    
    # Convert runs to dict format if needed
    run_dicts = []
    for run in runs:
        if isinstance(run, dict):
            run_dicts.append(run)
        else:
            run_dicts.append({
                "output_json": run.output_json,
                "confidence": run.confidence
            })
    
    # Extract token-level probabilities
    if include_token_probs:
        token_probs = aggregate_probs_from_runs(run_dicts, method=aggregation_method)
        if token_probs:
            result["token_probs"] = token_probs
    
    # Extract class-level probabilities
    if include_class_probs:
        class_probs_dict = {}
        for run in run_dicts:
            output_json = run.get("output_json") or {}
            text = output_json.get("text", "")
            logprobs = output_json.get("logprobs")
            
            if text and logprobs:
                class_probs = extract_text_class_probs(text, logprobs)
                if class_probs:
                    # Aggregate class probabilities
                    for class_label, prob in class_probs.items():
                        confidence = run.get("confidence", 1.0)
                        if class_label not in class_probs_dict:
                            class_probs_dict[class_label] = []
                        class_probs_dict[class_label].append(prob * confidence)
        
        # Aggregate class probabilities
        if class_probs_dict:
            aggregated_class_probs = {}
            total_weight = sum(sum(probs) for probs in class_probs_dict.values())
            
            if total_weight > 0:
                for class_label, probs in class_probs_dict.items():
                    aggregated_class_probs[class_label] = sum(probs) / total_weight
                
                result["class_probs"] = aggregated_class_probs
    
    return result

