"""Rationales and critique utilities."""
from typing import List, Dict, Any, Optional
import re


def extract_rationale_from_output(output_json: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Extract rationale/chain-of-thought from teacher output.
    
    Looks for common CoT patterns like "Let me think...", "Reasoning:", etc.
    
    Args:
        output_json: Teacher output JSON containing text
    
    Returns:
        Dictionary with rationale structure, or None if not found
    """
    if not output_json:
        return None
    
    text = output_json.get("text", "")
    if not text:
        return None
    
    # Common CoT patterns
    cot_patterns = [
        r"(?i)(?:let me think|reasoning|thinking|analysis|step-by-step)[:\.]?\s*(.+?)(?:\n\n|\Z)",
        r"(?i)(?:first|second|third|finally)[:\.]?\s*(.+?)(?:\n\n|\Z)",
        r"(?i)(?:therefore|thus|hence|conclusion)[:\.]?\s*(.+?)(?:\n\n|\Z)",
    ]
    
    rationale_parts = []
    conclusion = None
    
    # Try to extract reasoning steps
    for pattern in cot_patterns:
        matches = re.finditer(pattern, text, re.DOTALL)
        for match in matches:
            rationale_parts.append(match.group(1).strip())
    
    # Extract conclusion (usually at the end)
    conclusion_match = re.search(r"(?i)(?:conclusion|answer|final answer|result)[:\.]?\s*(.+?)(?:\Z)", text)
    if conclusion_match:
        conclusion = conclusion_match.group(1).strip()
    
    if not rationale_parts and not conclusion:
        return None
    
    return {
        "reasoning_steps": rationale_parts,
        "conclusion": conclusion,
        "full_text": text  # Keep full text for critique
    }


def distill_justification(rationales: List[Dict[str, Any]], max_length: int = 200) -> Optional[str]:
    """
    Distill multiple rationales into a short, verifiable justification.
    
    Removes private CoT details and creates a concise explanation safe for students.
    
    Args:
        rationales: List of rationale dictionaries from teacher runs
        max_length: Maximum length of justification
    
    Returns:
        Short justification string, or None if no rationales
    """
    if not rationales:
        return None
    
    # Extract key points from rationales
    key_points = []
    
    for rationale in rationales:
        if isinstance(rationale, dict):
            conclusion = rationale.get("conclusion")
            reasoning_steps = rationale.get("reasoning_steps", [])
        else:
            # Assume it's a TeacherRun object
            rationale_json = rationale.rationale_json if hasattr(rationale, 'rationale_json') else None
            if not rationale_json:
                continue
            conclusion = rationale_json.get("conclusion")
            reasoning_steps = rationale_json.get("reasoning_steps", [])
        
        # Use conclusion if available, otherwise use first reasoning step
        if conclusion:
            key_points.append(conclusion)
        elif reasoning_steps:
            key_points.append(reasoning_steps[0])
    
    if not key_points:
        return None
    
    # Combine key points into justification
    justification = " ".join(key_points[:3])  # Use up to 3 key points
    
    # Truncate if too long
    if len(justification) > max_length:
        justification = justification[:max_length].rsplit(' ', 1)[0] + "..."
    
    return justification.strip()


def critique_faithfulness(
    output_text: str,
    source_text: Optional[str] = None,
    citations: Optional[List[str]] = None
) -> float:
    """
    Critique faithfulness of output to source material.
    
    Performs simple checks for hallucinations and faithfulness.
    
    Args:
        output_text: Teacher output text to critique
        source_text: Source context text (optional)
        citations: List of citation IDs (optional)
    
    Returns:
        Faithfulness score (0.0-1.0)
    """
    if not output_text:
        return 0.0
    
    score = 1.0
    deductions = []
    
    # Check for citation markers
    has_citations = bool(citations) or bool(re.search(r'\[.*?\]|\(.*?\)', output_text))
    if not has_citations and source_text:
        # Deduct for lack of citations when source is available
        score -= 0.1
        deductions.append("No citations found")
    
    # Check for common hallucination markers
    hallucination_patterns = [
        r"(?i)\b(?:according to|studies show|research indicates|it is known that)\b(?!.*\[)",
        r"(?i)\b(?:always|never|all|every|none)\b",
        r"(?i)\b(?:definitely|certainly|absolutely)\b",
    ]
    
    hallucination_count = 0
    for pattern in hallucination_patterns:
        matches = re.findall(pattern, output_text)
        hallucination_count += len(matches)
    
    if hallucination_count > 3:
        score -= min(0.3, hallucination_count * 0.05)
        deductions.append(f"High certainty language ({hallucination_count} instances)")
    
    # Check for contradictions (simple heuristic)
    contradiction_markers = [
        r"(?i)\b(?:but|however|although|despite|yet)\b",
    ]
    
    contradiction_count = sum(len(re.findall(pattern, output_text)) for pattern in contradiction_markers)
    if contradiction_count > 2:
        score -= min(0.2, contradiction_count * 0.05)
        deductions.append(f"Multiple contradictions ({contradiction_count} instances)")
    
    # Check for vague language (reduces faithfulness)
    vague_patterns = [
        r"(?i)\b(?:maybe|perhaps|possibly|might|could|somewhat|kind of)\b",
    ]
    
    vague_count = sum(len(re.findall(pattern, output_text)) for pattern in vague_patterns)
    if vague_count > 5:
        score -= min(0.15, vague_count * 0.02)
        deductions.append(f"Excessive vague language ({vague_count} instances)")
    
    # Ensure score is in valid range
    score = max(0.0, min(1.0, score))
    
    return score


def perform_critique_pass(
    teacher_runs: List[Any],
    source_text: Optional[str] = None,
    citations: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Perform a critic pass on teacher runs to assess faithfulness.
    
    Args:
        teacher_runs: List of TeacherRun objects or dicts
        source_text: Source context text
        citations: List of citation IDs
    
    Returns:
        Dictionary with critique results:
        {
            "faithfulness_scores": [float, ...],
            "average_faithfulness": float,
            "critique_details": [str, ...]
        }
    """
    if not teacher_runs:
        return {
            "faithfulness_scores": [],
            "average_faithfulness": 0.0,
            "critique_details": []
        }
    
    faithfulness_scores = []
    critique_details = []
    
    for run in teacher_runs:
        if isinstance(run, dict):
            output_json = run.get("output_json") or {}
            text = output_json.get("text", "")
        else:
            # Assume TeacherRun object
            output_json = run.output_json or {}
            text = output_json.get("text", "")
        
        if text:
            score = critique_faithfulness(text, source_text, citations)
            faithfulness_scores.append(score)
            critique_details.append(f"Run {run.id if hasattr(run, 'id') else 'unknown'}: {score:.2f}")
    
    average_faithfulness = sum(faithfulness_scores) / len(faithfulness_scores) if faithfulness_scores else 0.0
    
    return {
        "faithfulness_scores": faithfulness_scores,
        "average_faithfulness": average_faithfulness,
        "critique_details": critique_details
    }

