"""Reuse-before-rerun engine for ML runs.

Prevents unnecessary duplicate runs by:
1. Computing similarity hash for run inputs
2. Finding existing runs with matching hash
3. Recommending reuse when appropriate
"""
import hashlib
import json
import logging
from typing import Optional, List
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from core.config import settings

logger = logging.getLogger(__name__)


class ReuseAction(str, Enum):
    """Recommended action for a run request."""
    PROCEED = "PROCEED"  # No match found, proceed with new run
    REUSE_RECOMMENDED = "REUSE_RECOMMENDED"  # Match found, recommend reuse
    REUSE_REQUIRED = "REUSE_REQUIRED"  # Strong match, should reuse


@dataclass
class MatchingRun:
    """A run that matches the similarity hash."""
    run_id: str
    status: str
    created_at: datetime
    metrics_json: dict
    similarity_score: float  # 0.0 to 1.0
    cost_usd: Optional[float]
    
    def to_dict(self) -> dict:
        return {
            'run_id': self.run_id,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'metrics_json': self.metrics_json,
            'similarity_score': self.similarity_score,
            'cost_usd': self.cost_usd
        }


@dataclass
class ReuseDecision:
    """Decision on whether to reuse or run."""
    action: ReuseAction
    similarity_hash: str
    matching_runs: List[MatchingRun]
    best_match: Optional[MatchingRun]
    confidence: float  # 0.0 to 1.0
    reason: str
    potential_savings_usd: Optional[float]
    
    def to_dict(self) -> dict:
        return {
            'action': self.action.value,
            'similarity_hash': self.similarity_hash,
            'matching_runs': [r.to_dict() for r in self.matching_runs],
            'best_match': self.best_match.to_dict() if self.best_match else None,
            'confidence': self.confidence,
            'reason': self.reason,
            'potential_savings_usd': self.potential_savings_usd
        }


class ReuseEngine:
    """Engine for detecting reusable runs."""
    
    def __init__(self, engine: Optional[Engine] = None):
        self.engine = engine or create_engine(settings.database_url)
        
        # Configuration
        self.max_age_days = 30  # Only consider runs from last 30 days
        self.min_confidence_for_reuse = 0.8  # Minimum confidence to recommend reuse
    
    @staticmethod
    def compute_similarity_hash(
        recipe_id: str,
        dataset_version_id: str,
        parameters: dict
    ) -> str:
        """
        Compute a deterministic hash for run deduplication.
        
        Same hash = same inputs = candidate for reuse.
        
        Args:
            recipe_id: The recipe being run
            dataset_version_id: The dataset version
            parameters: Run parameters (hyperparameters, etc.)
            
        Returns:
            16-character hex hash
        """
        # Canonicalize the inputs
        canonical = {
            'recipe_id': recipe_id,
            'dataset_version_id': str(dataset_version_id) if dataset_version_id else '',
            'parameters': json.dumps(parameters or {}, sort_keys=True)
        }
        
        content = json.dumps(canonical, sort_keys=True)
        full_hash = hashlib.sha256(content.encode()).hexdigest()
        
        return full_hash[:16]
    
    def find_matching_runs(
        self,
        similarity_hash: str,
        exclude_run_id: str = None,
        include_failed: bool = False
    ) -> List[MatchingRun]:
        """
        Find runs with the same similarity hash.
        
        Args:
            similarity_hash: Hash to search for
            exclude_run_id: Run ID to exclude (e.g., current run)
            include_failed: Whether to include failed runs
            
        Returns:
            List of matching runs, sorted by recency
        """
        cutoff_date = datetime.utcnow() - timedelta(days=self.max_age_days)
        
        query = """
            SELECT 
                id, status, created_at, metrics_json, 
                actual_cost_usd, estimated_cost_usd
            FROM ml_run
            WHERE similarity_hash = :hash
              AND created_at > :cutoff
        """
        params = {'hash': similarity_hash, 'cutoff': cutoff_date}
        
        if exclude_run_id:
            query += " AND id != :exclude_id"
            params['exclude_id'] = exclude_run_id
        
        if not include_failed:
            query += " AND status = 'succeeded'"
        
        query += " ORDER BY created_at DESC LIMIT 10"
        
        matches = []
        with self.engine.connect() as conn:
            result = conn.execute(text(query), params)
            for row in result:
                row_dict = dict(row._mapping)
                matches.append(MatchingRun(
                    run_id=row_dict['id'],
                    status=row_dict['status'],
                    created_at=row_dict['created_at'],
                    metrics_json=row_dict['metrics_json'] or {},
                    similarity_score=1.0,  # Exact hash match = 100%
                    cost_usd=float(row_dict['actual_cost_usd']) if row_dict['actual_cost_usd'] else (
                        float(row_dict['estimated_cost_usd']) if row_dict['estimated_cost_usd'] else None
                    )
                ))
        
        return matches
    
    def evaluate_reuse(
        self,
        recipe_id: str,
        dataset_version_id: str,
        parameters: dict,
        estimated_cost_usd: float = None,
        force_rerun: bool = False
    ) -> ReuseDecision:
        """
        Evaluate whether to reuse an existing run or proceed with a new one.
        
        Args:
            recipe_id: The recipe to run
            dataset_version_id: The dataset version to use
            parameters: Run parameters
            estimated_cost_usd: Estimated cost of a new run
            force_rerun: If True, always recommend proceeding
            
        Returns:
            ReuseDecision with recommendation
        """
        similarity_hash = self.compute_similarity_hash(
            recipe_id, dataset_version_id, parameters
        )
        
        if force_rerun:
            return ReuseDecision(
                action=ReuseAction.PROCEED,
                similarity_hash=similarity_hash,
                matching_runs=[],
                best_match=None,
                confidence=1.0,
                reason="Forced rerun requested",
                potential_savings_usd=None
            )
        
        # Find matching runs
        matches = self.find_matching_runs(similarity_hash)
        
        if not matches:
            return ReuseDecision(
                action=ReuseAction.PROCEED,
                similarity_hash=similarity_hash,
                matching_runs=[],
                best_match=None,
                confidence=1.0,
                reason="No matching runs found",
                potential_savings_usd=None
            )
        
        # Found matches - recommend reuse
        best_match = matches[0]  # Most recent successful run
        
        # Calculate potential savings
        potential_savings = None
        if estimated_cost_usd and best_match.cost_usd:
            potential_savings = estimated_cost_usd
        elif estimated_cost_usd:
            potential_savings = estimated_cost_usd
        
        # Determine confidence based on match quality
        confidence = 1.0  # Exact hash match
        
        # Adjust confidence based on age
        if best_match.created_at:
            age_days = (datetime.utcnow() - best_match.created_at).days
            if age_days > 14:
                confidence *= 0.9  # Slightly reduce for older runs
            if age_days > 21:
                confidence *= 0.9
        
        # Determine action
        if confidence >= 0.95 and best_match.metrics_json:
            action = ReuseAction.REUSE_REQUIRED
            reason = f"Exact match found (run {best_match.run_id}). Reuse strongly recommended."
        elif confidence >= self.min_confidence_for_reuse:
            action = ReuseAction.REUSE_RECOMMENDED
            reason = f"Found {len(matches)} matching run(s). Consider reusing {best_match.run_id}."
        else:
            action = ReuseAction.PROCEED
            reason = "Matches found but confidence too low for automatic reuse."
        
        return ReuseDecision(
            action=action,
            similarity_hash=similarity_hash,
            matching_runs=matches,
            best_match=best_match,
            confidence=round(confidence, 2),
            reason=reason,
            potential_savings_usd=round(potential_savings, 2) if potential_savings else None
        )
    
    def record_similarity_hash(self, run_id: str, similarity_hash: str):
        """
        Record the similarity hash for a run.
        
        Args:
            run_id: The run ID
            similarity_hash: The computed hash
        """
        query = "UPDATE ml_run SET similarity_hash = :hash WHERE id = :run_id"
        with self.engine.begin() as conn:
            conn.execute(text(query), {'hash': similarity_hash, 'run_id': run_id})
    
    def mark_reused_from(self, run_id: str, source_run_id: str):
        """
        Mark a run as reusing results from another run.
        
        Args:
            run_id: The new run ID
            source_run_id: The run being reused
        """
        query = """
            UPDATE ml_run 
            SET reused_from_run_id = :source_id, status = 'succeeded'
            WHERE id = :run_id
        """
        with self.engine.begin() as conn:
            conn.execute(text(query), {'source_id': source_run_id, 'run_id': run_id})
        
        logger.info(f"Run {run_id} reused results from {source_run_id}")


# Singleton instance
_engine_instance: Optional[ReuseEngine] = None


def get_reuse_engine() -> ReuseEngine:
    """Get singleton reuse engine instance."""
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = ReuseEngine()
    return _engine_instance
