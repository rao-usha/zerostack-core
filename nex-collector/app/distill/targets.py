"""Extract targets from teacher runs."""
from typing import List, Optional
import pandas as pd
from ..models import SyntheticExample, TeacherRun, Targets
from .soft_labels import create_soft_labels_from_runs
from .rationales import (
    extract_rationale_from_output,
    distill_justification,
    perform_critique_pass
)


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
        # Get all teacher runs for this example (for soft labels)
        teacher_runs = list(example.teacher_runs) if example.teacher_runs else []
        
        if not teacher_runs:
            continue
        
        # Use latest run for text
        teacher_run = teacher_runs[-1]
        
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
        
        # Extract soft labels from all runs
        if teacher_runs:
            soft_labels = create_soft_labels_from_runs(
                teacher_runs,
                aggregation_method="weighted_mean",
                include_token_probs=True,
                include_class_probs=True
            )
            if soft_labels:
                row["y_probs"] = soft_labels
        
        # Extract usage/scores
        if teacher_run.usage_json:
            row["y_scores"] = {
                "tokens": teacher_run.usage_json.get("total_tokens", 0),
                "prompt_tokens": teacher_run.usage_json.get("prompt_tokens", 0),
                "completion_tokens": teacher_run.usage_json.get("completion_tokens", 0)
            }
        
        rows.append(row)
    
    return pd.DataFrame(rows)


def create_target_with_soft_labels(
    example: SyntheticExample,
    teacher_runs: List[TeacherRun],
    target_id: Optional[str] = None,
    source_text: Optional[str] = None,
    citations: Optional[List[str]] = None
) -> Targets:
    """
    Create a Targets object with soft labels extracted from teacher runs.
    
    Args:
        example: SyntheticExample to create target for
        teacher_runs: List of TeacherRun objects to extract soft labels from
        target_id: Optional target ID (defaults to f"target-{example.id}")
        source_text: Optional source text for faithfulness critique
        citations: Optional list of citation IDs
    
    Returns:
        Targets object with y_probs_json, justification, and faithfulness_score populated
    """
    if not teacher_runs:
        raise ValueError("At least one teacher run required")
    
    # Get text from latest run
    latest_run = teacher_runs[-1]
    if not latest_run.output_json:
        raise ValueError("Latest run has no output")
    
    text = latest_run.output_json.get("text", "")
    if not text:
        raise ValueError("Latest run has no text output")
    
    # Extract soft labels
    soft_labels = create_soft_labels_from_runs(
        teacher_runs,
        aggregation_method="weighted_mean",
        include_token_probs=True,
        include_class_probs=True
    )
    
    # Extract and distill rationales
    rationales = []
    for run in teacher_runs:
        if run.output_json:
            rationale = extract_rationale_from_output(run.output_json)
            if rationale:
                rationales.append(rationale)
                # Store rationale in run (if not already stored)
                if not run.rationale_json:
                    run.rationale_json = rationale
    
    justification = distill_justification(rationales) if rationales else None
    
    # Perform critique pass
    critique_result = perform_critique_pass(teacher_runs, source_text, citations)
    faithfulness_score = critique_result.get("average_faithfulness", None)
    
    # Create target
    import uuid
    target = Targets(
        id=target_id or f"target-{example.id}",
        example_id=example.id,
        y_text=text,
        y_probs_json=soft_labels if soft_labels else None,
        justification=justification,
        faithfulness_score=faithfulness_score
    )
    
    return target
