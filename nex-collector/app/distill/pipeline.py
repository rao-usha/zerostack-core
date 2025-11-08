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
        from ..models import TeacherRun, RunScore
        
        run = self.db.query(TeacherRun).filter(TeacherRun.id == run_id).first()
        if not run:
            raise ValueError(f"Run {run_id} not found")
        
        if not run.output_blob or not run.output_blob.get("text"):
            return  # Nothing to score
        
        text = run.output_blob["text"]
        logprobs = run.logprobs_blob
        
        # Score the run
        metrics = score_run(text, logprobs)
        
        # Save score
        existing_score = self.db.query(RunScore).filter(RunScore.run_id == run_id).first()
        if existing_score:
            existing_score.metrics_json = metrics
        else:
            score = RunScore(
                id=f"score-{run_id}",
                run_id=run_id,
                metrics_json=metrics
            )
            self.db.add(score)
        
        self.db.commit()
    
    def build_dataset(
        self,
        dataset_id: str,
        name: str,
        version: str,
        kind: str,
        context_ref_id: str,
        batch_ids: List[str],
        filters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Build a dataset from runs."""
        return build_dataset(
            self.db,
            dataset_id,
            name,
            version,
            kind,
            context_ref_id,
            batch_ids,
            filters
        )

