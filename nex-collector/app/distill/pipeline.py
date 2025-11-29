"""Distillation pipeline orchestrator."""
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from .scorer import score_run
from .builder import build_dataset


class DistillationPipeline:
    """Orchestrates the distillation pipeline."""
    
    def __init__(self, db: Session):
        """Initialize pipeline."""
        self.db = db
    
    def process_run(self, run_id: str):
        """Process a single run: score it."""
        from ..models import TeacherRun
        
        run = self.db.query(TeacherRun).filter(TeacherRun.id == run_id).first()
        if not run:
            raise ValueError(f"Run {run_id} not found")
        
        if not run.output_json or not run.output_json.get("text"):
            return  # Nothing to score
        
        text = run.output_json["text"]
        logprobs = run.output_json.get("logprobs")
        
        # Score the run
        metrics = score_run(text, logprobs)
        
        # Save score in quality_scores_json (RunScore model doesn't exist)
        run.quality_scores_json = metrics
        self.db.commit()
    
    def build_dataset(
        self,
        dataset_id: str,
        name: str,
        version: str,
        kind: str,
        variant_ids: List[str],
        filters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Build a dataset from variants."""
        from ..models import DatasetKind
        kind_enum = DatasetKind(kind)
        return build_dataset(
            self.db,
            dataset_id,
            name,
            version,
            kind_enum,
            variant_ids,
            filters
        )

