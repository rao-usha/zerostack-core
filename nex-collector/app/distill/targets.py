"""Extract targets from teacher runs."""
from typing import List, Optional
import pandas as pd
from ..models import SyntheticExample, TeacherRun, Targets


def extract_targets_from_runs(examples: List[SyntheticExample]) -> pd.DataFrame:
    """
    Extract targets from teacher runs for examples.
    
    Returns DataFrame with columns:
    - example_id
    - y_text: output text
    - y_probs: class probabilities (if available)
    - y_scores: quality scores
    """
    rows = []
    
    for example in examples:
        # Get latest teacher run for this example
        teacher_run = None
        if example.teacher_runs:
            teacher_run = example.teacher_runs[-1]  # Latest
        
        if not teacher_run or not teacher_run.output_json:
            continue
        
        output = teacher_run.output_json
        text = output.get("text", "")
        
        if not text:
            continue
        
        row = {
            "example_id": example.id,
            "y_text": text
        }
        
        # Extract logprobs if available
        if "logprobs" in output:
            logprobs = output["logprobs"]
            if "token_logprobs" in logprobs:
                import math
                token_probs = [math.exp(lp) if lp is not None else 0.0 
                              for lp in logprobs["token_logprobs"]]
                row["y_probs"] = token_probs
        
        # Extract usage/scores
        if teacher_run.usage_json:
            row["y_scores"] = {
                "tokens": teacher_run.usage_json.get("total_tokens", 0),
                "prompt_tokens": teacher_run.usage_json.get("prompt_tokens", 0),
                "completion_tokens": teacher_run.usage_json.get("completion_tokens", 0)
            }
        
        rows.append(row)
    
    return pd.DataFrame(rows)
