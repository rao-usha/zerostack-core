"""Filtering logic for distillation."""
from typing import Dict, Any, List
from ..models import SyntheticExample, TeacherRun


def apply_filters(
    examples: List[SyntheticExample],
    filters: Dict[str, Any],
    require_approval: bool = False
) -> List[SyntheticExample]:
    """
    Apply filters to examples.
    
    Supported filters:
    - min_length: minimum output text length
    - max_length: maximum output text length
    - has_teacher_output: require teacher run
    - domain: filter by domain
    - persona: filter by persona
    - task: filter by task
    """
    filtered = []
    
    for example in examples:
        # Check domain/persona/task filters
        if "domain" in filters and example.variant.domain != filters["domain"]:
            continue
        if "persona" in filters and example.variant.persona != filters["persona"]:
            continue
        if "task" in filters and example.variant.task != filters["task"]:
            continue
        
        # Check teacher output
        if filters.get("has_teacher_output", False):
            if not example.teacher_runs or not example.teacher_runs[-1].output_json:
                continue
        
        # Check output length (if teacher run exists)
        if example.teacher_runs:
            teacher_run = example.teacher_runs[-1]
            if teacher_run.output_json:
                text = teacher_run.output_json.get("text", "")
                length = len(text)
                
                if "min_length" in filters and length < filters["min_length"]:
                    continue
                if "max_length" in filters and length > filters["max_length"]:
                    continue
        
        filtered.append(example)
    
    return filtered
