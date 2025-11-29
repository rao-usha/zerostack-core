"""Sample examples from context variants."""
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from ..models import ContextVariant, SyntheticExample, ExampleType
import uuid


class ExampleSampler:
    """Sample synthetic examples from variants."""
    
    def sample(
        self,
        db: Session,
        variant_ids: List[str],
        example_type: ExampleType,
        quota_per_variant: int = 10,
        rules: Dict[str, Any] = None
    ) -> List[str]:
        """
        Sample examples from variants.
        
        Returns:
            List of created example IDs
        """
        rules = rules or {}
        created_ids = []
        
        for variant_id in variant_ids:
            variant = db.query(ContextVariant).filter(ContextVariant.id == variant_id).first()
            if not variant:
                continue
            
            # Generate examples based on type
            for i in range(quota_per_variant):
                example_id = f"ex-{uuid.uuid4().hex[:12]}"
                
                # Create input based on example type
                input_json = self._create_input(variant, example_type, i)
                
                example = SyntheticExample(
                    id=example_id,
                    variant_id=variant_id,
                    example_type=example_type,
                    input_json=input_json,
                    constraints_json=variant.constraints_json or {},
                    tags=self._extract_tags(variant)
                )
                db.add(example)
                created_ids.append(example_id)
        
        db.commit()
        return created_ids
    
    def _create_input(self, variant: ContextVariant, example_type: ExampleType, index: int) -> Dict[str, Any]:
        """Create input JSON for example."""
        preview = (variant.body_text or "")[:200] + "..." if variant.body_text else ""
        
        if example_type == ExampleType.INSTRUCTION:
            return {
                "instruction": f"Based on the {variant.domain or 'general'} context, provide instructions for: {variant.task or 'task'}",
                "context_preview": preview,
                "domain": variant.domain,
                "persona": variant.persona
            }
        elif example_type == ExampleType.QA:
            return {
                "question": f"What does the {variant.domain or 'general'} context say about {variant.task or 'the topic'}?",
                "context_preview": preview,
                "domain": variant.domain
            }
        else:  # TASK
            return {
                "task": variant.task or "general",
                "input": f"Process this {variant.domain or 'general'} context",
                "context_preview": preview,
                "domain": variant.domain,
                "persona": variant.persona
            }
    
    def _extract_tags(self, variant: ContextVariant) -> List[str]:
        """Extract tags from variant."""
        tags = []
        if variant.domain:
            tags.append(f"domain:{variant.domain}")
        if variant.persona:
            tags.append(f"persona:{variant.persona}")
        if variant.task:
            tags.append(f"task:{variant.task}")
        if variant.style:
            tags.append(f"style:{variant.style}")
        return tags

