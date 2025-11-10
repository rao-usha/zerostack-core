"""Teacher ensemble aggregation utilities."""
from typing import List, Dict, Any, Optional, Tuple
from collections import Counter
import json


def majority_vote(runs: List[Dict[str, Any]], output_key: str = "text") -> Optional[str]:
    """
    Aggregate teacher runs using majority vote.
    
    Args:
        runs: List of teacher run dicts with output_json containing the output_key
        output_key: Key to extract from output_json (default: "text")
    
    Returns:
        Most common output, or None if no runs provided
    """
    if not runs:
        return None
    
    # Extract outputs
    outputs = []
    for run in runs:
        if isinstance(run, dict):
            output_json = run.get("output_json") or {}
            output = output_json.get(output_key)
        else:
            # Assume it's a TeacherRun object
            output_json = run.output_json or {}
            output = output_json.get(output_key)
        
        if output:
            outputs.append(str(output).strip())
    
    if not outputs:
        return None
    
    # Count votes
    counter = Counter(outputs)
    most_common = counter.most_common(1)
    
    if most_common:
        return most_common[0][0]
    
    return None


def borda_count(runs: List[Dict[str, Any]], output_key: str = "text") -> Optional[str]:
    """
    Aggregate teacher runs using Borda count.
    
    Each unique output gets points based on its rank in each run's preference.
    If runs are ordered by quality/confidence, higher-ranked outputs get more points.
    
    Args:
        runs: List of teacher run dicts, optionally sorted by quality/confidence
        output_key: Key to extract from output_json
    
    Returns:
        Output with highest Borda score, or None if no runs provided
    """
    if not runs:
        return None
    
    # Extract outputs with their ranks
    output_scores = {}
    
    for rank, run in enumerate(runs, start=1):
        if isinstance(run, dict):
            output_json = run.get("output_json") or {}
            output = output_json.get(output_key)
            confidence = run.get("confidence", 1.0)
        else:
            # Assume it's a TeacherRun object
            output_json = run.output_json or {}
            output = output_json.get(output_key)
            confidence = run.confidence or 1.0
        
        if output:
            output_str = str(output).strip()
            # Weight by confidence and rank (higher rank = more points)
            points = (len(runs) - rank + 1) * confidence
            output_scores[output_str] = output_scores.get(output_str, 0) + points
    
    if not output_scores:
        return None
    
    # Return output with highest score
    return max(output_scores.items(), key=lambda x: x[1])[0]


def pairwise_preference(runs: List[Dict[str, Any]], output_key: str = "text") -> Optional[str]:
    """
    Aggregate teacher runs using pairwise preference (Condorcet method).
    
    For each pair of outputs, count which one is preferred more often.
    Returns the output that beats all others in pairwise comparisons.
    
    Args:
        runs: List of teacher run dicts
        output_key: Key to extract from output_json
    
    Returns:
        Condorcet winner, or None if no runs provided
    """
    if not runs:
        return None
    
    # Extract unique outputs
    outputs = []
    for run in runs:
        if isinstance(run, dict):
            output_json = run.get("output_json") or {}
            output = output_json.get(output_key)
        else:
            output_json = run.output_json or {}
            output = output_json.get(output_key)
        
        if output:
            output_str = str(output).strip()
            if output_str not in outputs:
                outputs.append(output_str)
    
    if not outputs:
        return None
    
    if len(outputs) == 1:
        return outputs[0]
    
    # Build preference matrix
    # pref_matrix[a][b] = number of runs where a is preferred over b
    pref_matrix = {a: {b: 0 for b in outputs if b != a} for a in outputs}
    
    for run in runs:
        if isinstance(run, dict):
            output_json = run.get("output_json") or {}
            output = output_json.get(output_key)
            confidence = run.get("confidence", 1.0)
        else:
            output_json = run.output_json or {}
            output = output_json.get(output_key)
            confidence = run.confidence or 1.0
        
        if output:
            output_str = str(output).strip()
            # This output is preferred over all others in this run
            for other_output in outputs:
                if other_output != output_str:
                    pref_matrix[output_str][other_output] += confidence
    
    # Find Condorcet winner: output that beats all others
    for candidate in outputs:
        beats_all = all(
            pref_matrix[candidate][other] > pref_matrix[other][candidate]
            for other in outputs
            if other != candidate
        )
        if beats_all:
            return candidate
    
    # No Condorcet winner, use Borda count as fallback
    return borda_count(runs, output_key)


def aggregate_ensemble(
    runs: List[Dict[str, Any]],
    method: str = "majority_vote",
    output_key: str = "text"
) -> Tuple[Optional[str], Dict[str, Any]]:
    """
    Aggregate multiple teacher runs using specified method.
    
    Args:
        runs: List of teacher run dicts or TeacherRun objects
        method: Aggregation method ("majority_vote", "borda_count", "pairwise_preference")
        output_key: Key to extract from output_json
    
    Returns:
        Tuple of (aggregated_output, metadata_dict)
    """
    if not runs:
        return None, {"method": method, "num_runs": 0, "error": "No runs provided"}
    
    # Convert runs to dict format if needed
    run_dicts = []
    for run in runs:
        if isinstance(run, dict):
            run_dicts.append(run)
        else:
            # Convert TeacherRun object to dict
            run_dicts.append({
                "id": run.id,
                "output_json": run.output_json,
                "confidence": run.confidence,
                "quality_scores_json": run.quality_scores_json,
                "rand_seed": run.rand_seed,
                "temperature": run.temperature,
                "decoding_params": run.decoding_params,
                "model": run.model,
                "provider": run.provider
            })
    
    # Aggregate based on method
    if method == "majority_vote":
        aggregated = majority_vote(run_dicts, output_key)
    elif method == "borda_count":
        aggregated = borda_count(run_dicts, output_key)
    elif method == "pairwise_preference":
        aggregated = pairwise_preference(run_dicts, output_key)
    else:
        return None, {"method": method, "error": f"Unknown method: {method}"}
    
    # Build metadata
    metadata = {
        "method": method,
        "num_runs": len(run_dicts),
        "runs_used": [r.get("id", f"run_{i}") for i, r in enumerate(run_dicts)],
        "aggregated": aggregated is not None
    }
    
    # Add per-run details
    run_details = []
    for run in run_dicts:
        output_json = run.get("output_json") or {}
        run_details.append({
            "id": run.get("id"),
            "output": output_json.get(output_key),
            "confidence": run.get("confidence"),
            "model": run.get("model"),
            "provider": run.get("provider"),
            "rand_seed": run.get("rand_seed"),
            "temperature": run.get("temperature")
        })
    metadata["run_details"] = run_details
    
    return aggregated, metadata

