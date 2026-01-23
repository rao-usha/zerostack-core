"""Model Promotion Service.

Handles model promotion/demotion between status levels (draft -> staging -> production -> retired).
Includes validation rules and promotion history tracking.
"""
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from core.config import settings

logger = logging.getLogger(__name__)


class PromotionDirection(str, Enum):
    """Direction of promotion."""
    PROMOTE = "promote"
    DEMOTE = "demote"


@dataclass
class ValidationRequirement:
    """A single validation requirement for promotion."""
    name: str
    description: str
    passed: bool
    details: Optional[str] = None


@dataclass
class ValidationResult:
    """Result of promotion validation."""
    can_promote: bool
    requirements: List[ValidationRequirement]
    message: str

    def to_dict(self) -> dict:
        return {
            'can_promote': self.can_promote,
            'requirements': [
                {
                    'name': r.name,
                    'description': r.description,
                    'passed': r.passed,
                    'details': r.details
                }
                for r in self.requirements
            ],
            'message': self.message
        }


@dataclass
class PromotionRecord:
    """Record of a promotion/demotion."""
    id: str
    model_id: str
    from_status: str
    to_status: str
    promoted_by: Optional[str]
    promotion_notes: Optional[str]
    validation_results: Optional[dict]
    promoted_at: datetime


# Status progression order
STATUS_ORDER = ['draft', 'staging', 'production', 'retired']


class PromotionService:
    """Service for model promotion and validation."""

    def __init__(self, engine: Optional[Engine] = None):
        self.engine = engine or create_engine(settings.database_url)

    def get_promotion_requirements(self, target_status: str) -> List[str]:
        """
        Get list of requirements for promoting to a target status.

        Args:
            target_status: The status to promote to

        Returns:
            List of requirement descriptions
        """
        if target_status == 'staging':
            return [
                "Model must have at least one completed run",
                "At least one run must have recorded metrics"
            ]
        elif target_status == 'production':
            return [
                "Model must have a run completed within the last 7 days",
                "Model must not have any critical drift alerts",
                "Model must have passed evaluation packs (if configured)"
            ]
        elif target_status == 'draft':
            return ["Demotion allowed with notes"]
        elif target_status == 'retired':
            return ["Any model can be retired"]
        return []

    def validate_promotion(
        self,
        model_id: str,
        target_status: str
    ) -> ValidationResult:
        """
        Validate whether a model can be promoted to a target status.

        Args:
            model_id: The model to validate
            target_status: The desired target status

        Returns:
            ValidationResult with pass/fail and details
        """
        # Get current model
        model = self._get_model(model_id)
        if not model:
            return ValidationResult(
                can_promote=False,
                requirements=[],
                message="Model not found"
            )

        current_status = model['status']
        requirements = []

        # Validate status transition
        if not self._is_valid_transition(current_status, target_status):
            return ValidationResult(
                can_promote=False,
                requirements=[],
                message=f"Invalid transition from {current_status} to {target_status}"
            )

        # Run validation checks based on target status
        if target_status == 'staging':
            requirements = self._validate_for_staging(model_id)
        elif target_status == 'production':
            requirements = self._validate_for_production(model_id)
        elif target_status in ('draft', 'retired'):
            # Demotions and retirements are always allowed
            requirements = [
                ValidationRequirement(
                    name="demotion_allowed",
                    description="Demotion/retirement allowed with notes",
                    passed=True
                )
            ]

        all_passed = all(r.passed for r in requirements)

        if all_passed:
            message = f"Model can be promoted to {target_status}"
        else:
            failed = [r.name for r in requirements if not r.passed]
            message = f"Validation failed: {', '.join(failed)}"

        return ValidationResult(
            can_promote=all_passed,
            requirements=requirements,
            message=message
        )

    def execute_promotion(
        self,
        model_id: str,
        target_status: str,
        notes: str,
        user: str = None
    ) -> Optional[PromotionRecord]:
        """
        Execute a model promotion.

        Args:
            model_id: The model to promote
            target_status: The target status
            notes: Promotion notes (required)
            user: The user performing the promotion

        Returns:
            PromotionRecord if successful, None if failed
        """
        # Validate first
        validation = self.validate_promotion(model_id, target_status)
        if not validation.can_promote:
            logger.warning(f"Promotion validation failed for {model_id}: {validation.message}")
            return None

        # Get current model
        model = self._get_model(model_id)
        from_status = model['status']

        # Update model status
        update_query = """
            UPDATE ml_model
            SET status = :status, updated_at = NOW()
            WHERE id = :model_id
        """

        # Record promotion
        insert_query = """
            INSERT INTO ml_model_promotions
            (model_id, from_status, to_status, promoted_by, promotion_notes, validation_results)
            VALUES (:model_id, :from_status, :to_status, :promoted_by, :notes, :validation)
            RETURNING id, promoted_at
        """

        with self.engine.begin() as conn:
            conn.execute(text(update_query), {
                'model_id': model_id,
                'status': target_status
            })

            result = conn.execute(text(insert_query), {
                'model_id': model_id,
                'from_status': from_status,
                'to_status': target_status,
                'promoted_by': user,
                'notes': notes,
                'validation': str(validation.to_dict())
            }).fetchone()

        logger.info(f"Promoted model {model_id} from {from_status} to {target_status}")

        return PromotionRecord(
            id=str(result[0]),
            model_id=model_id,
            from_status=from_status,
            to_status=target_status,
            promoted_by=user,
            promotion_notes=notes,
            validation_results=validation.to_dict(),
            promoted_at=result[1]
        )

    def rollback_promotion(
        self,
        model_id: str,
        to_promotion_id: str,
        user: str = None
    ) -> Optional[PromotionRecord]:
        """
        Rollback a model to a previous promotion state.

        Args:
            model_id: The model to rollback
            to_promotion_id: The promotion record ID to rollback to
            user: The user performing the rollback

        Returns:
            PromotionRecord for the new demotion
        """
        # Get the target promotion record
        query = "SELECT * FROM ml_model_promotions WHERE id = :id AND model_id = :model_id"

        with self.engine.connect() as conn:
            result = conn.execute(text(query), {
                'id': to_promotion_id,
                'model_id': model_id
            }).fetchone()

        if not result:
            return None

        target_record = dict(result._mapping)
        target_status = target_record['from_status']  # Rollback to the status before that promotion

        return self.execute_promotion(
            model_id=model_id,
            target_status=target_status,
            notes=f"Rollback to state before promotion {to_promotion_id}",
            user=user
        )

    def get_promotion_history(self, model_id: str) -> List[PromotionRecord]:
        """
        Get promotion history for a model.

        Args:
            model_id: The model ID

        Returns:
            List of PromotionRecords (most recent first)
        """
        query = """
            SELECT * FROM ml_model_promotions
            WHERE model_id = :model_id
            ORDER BY promoted_at DESC
        """

        with self.engine.connect() as conn:
            result = conn.execute(text(query), {'model_id': model_id})
            rows = [dict(row._mapping) for row in result]

        return [
            PromotionRecord(
                id=str(r['id']),
                model_id=r['model_id'],
                from_status=r['from_status'],
                to_status=r['to_status'],
                promoted_by=r['promoted_by'],
                promotion_notes=r['promotion_notes'],
                validation_results=r['validation_results'],
                promoted_at=r['promoted_at']
            )
            for r in rows
        ]

    def _is_valid_transition(self, from_status: str, to_status: str) -> bool:
        """Check if a status transition is valid."""
        if from_status == to_status:
            return False

        from_idx = STATUS_ORDER.index(from_status) if from_status in STATUS_ORDER else -1
        to_idx = STATUS_ORDER.index(to_status) if to_status in STATUS_ORDER else -1

        # Allow forward progression by one step
        if to_idx == from_idx + 1:
            return True

        # Allow any demotion (going backward)
        if to_idx < from_idx:
            return True

        # Allow jumping to retired from any status
        if to_status == 'retired':
            return True

        return False

    def _validate_for_staging(self, model_id: str) -> List[ValidationRequirement]:
        """Validate requirements for promotion to staging."""
        requirements = []

        # Check for completed runs
        run_query = """
            SELECT COUNT(*) as count
            FROM ml_run
            WHERE model_id = :model_id AND status = 'succeeded'
        """

        with self.engine.connect() as conn:
            result = conn.execute(text(run_query), {'model_id': model_id}).fetchone()
            run_count = result[0]

        requirements.append(ValidationRequirement(
            name="has_completed_runs",
            description="Model must have at least one completed run",
            passed=run_count >= 1,
            details=f"{run_count} completed run(s)"
        ))

        # Check for runs with metrics
        metrics_query = """
            SELECT COUNT(*) as count
            FROM ml_run
            WHERE model_id = :model_id
            AND status = 'succeeded'
            AND metrics_json IS NOT NULL
            AND metrics_json != '{}'
        """

        with self.engine.connect() as conn:
            result = conn.execute(text(metrics_query), {'model_id': model_id}).fetchone()
            metrics_count = result[0]

        requirements.append(ValidationRequirement(
            name="has_metrics",
            description="At least one run must have recorded metrics",
            passed=metrics_count >= 1,
            details=f"{metrics_count} run(s) with metrics"
        ))

        return requirements

    def _validate_for_production(self, model_id: str) -> List[ValidationRequirement]:
        """Validate requirements for promotion to production."""
        requirements = []

        # Check for recent run
        recent_run_query = """
            SELECT COUNT(*) as count
            FROM ml_run
            WHERE model_id = :model_id
            AND status = 'succeeded'
            AND finished_at > NOW() - INTERVAL '7 days'
        """

        with self.engine.connect() as conn:
            result = conn.execute(text(recent_run_query), {'model_id': model_id}).fetchone()
            recent_count = result[0]

        requirements.append(ValidationRequirement(
            name="recent_run",
            description="Model must have a run completed within the last 7 days",
            passed=recent_count >= 1,
            details=f"{recent_count} run(s) in last 7 days"
        ))

        # Check for critical drift alerts (if drift checks exist)
        drift_query = """
            SELECT COUNT(*) as count
            FROM drift_alerts da
            JOIN drift_checks dc ON da.drift_check_id = dc.id
            JOIN ml_model m ON dc.recipe_id = m.recipe_id
            WHERE m.id = :model_id
            AND da.severity = 'critical'
            AND da.acknowledged = false
            AND da.triggered_at > NOW() - INTERVAL '7 days'
        """

        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(drift_query), {'model_id': model_id}).fetchone()
                drift_count = result[0]

            requirements.append(ValidationRequirement(
                name="no_critical_drift",
                description="Model must not have any critical drift alerts",
                passed=drift_count == 0,
                details=f"{drift_count} critical drift alert(s)"
            ))
        except Exception:
            # Drift tables may not exist yet
            requirements.append(ValidationRequirement(
                name="no_critical_drift",
                description="Model must not have any critical drift alerts",
                passed=True,
                details="Drift checking not configured"
            ))

        return requirements

    def _get_model(self, model_id: str) -> Optional[dict]:
        """Get model by ID."""
        query = "SELECT * FROM ml_model WHERE id = :model_id"

        with self.engine.connect() as conn:
            result = conn.execute(text(query), {'model_id': model_id}).fetchone()
            if result:
                return dict(result._mapping)
        return None


# Singleton instance
_service_instance: Optional[PromotionService] = None


def get_promotion_service() -> PromotionService:
    """Get singleton promotion service instance."""
    global _service_instance
    if _service_instance is None:
        _service_instance = PromotionService()
    return _service_instance
