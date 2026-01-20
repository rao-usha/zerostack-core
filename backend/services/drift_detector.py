"""Drift detection service for ML outputs.

Monitors metrics across runs and alerts when significant changes occur.
"""
import asyncio
import logging
from typing import Optional, List, Dict, Any
from decimal import Decimal
from datetime import datetime
from enum import Enum
from dataclasses import dataclass
from uuid import UUID
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from core.config import settings
from services.notifications import get_notification_service

logger = logging.getLogger(__name__)


class ComparisonType(str, Enum):
    """Types of drift comparison."""
    ABSOLUTE = "absolute"  # |new - baseline| > threshold
    PERCENTAGE_INCREASE = "percentage_increase"  # (new - baseline) / baseline > threshold
    PERCENTAGE_DECREASE = "percentage_decrease"  # (baseline - new) / baseline > threshold
    PERCENTAGE_BOTH = "percentage_both"  # |new - baseline| / baseline > threshold


class Severity(str, Enum):
    """Alert severity levels."""
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class DriftCheckResult:
    """Result of a drift check."""
    check_id: str
    check_name: str
    metric: str
    is_breached: bool
    baseline_value: Optional[float]
    current_value: Optional[float]
    change_percent: Optional[float]
    severity: Optional[Severity]
    message: str
    
    def to_dict(self) -> dict:
        return {
            'check_id': self.check_id,
            'check_name': self.check_name,
            'metric': self.metric,
            'is_breached': self.is_breached,
            'baseline_value': self.baseline_value,
            'current_value': self.current_value,
            'change_percent': self.change_percent,
            'severity': self.severity.value if self.severity else None,
            'message': self.message
        }


class DriftDetector:
    """Service for detecting metric drift in ML outputs."""
    
    def __init__(self, engine: Optional[Engine] = None):
        self.engine = engine or create_engine(settings.database_url)
        
        # Threshold for critical vs warning (2x the configured threshold)
        self.critical_multiplier = 2.0
    
    def check_drift(
        self,
        check_id: str,
        current_value: float,
        baseline_value: Optional[float] = None
    ) -> DriftCheckResult:
        """
        Check if a metric has drifted beyond the configured threshold.
        
        Args:
            check_id: The drift check ID
            current_value: Current metric value
            baseline_value: Override baseline (uses stored baseline if not provided)
            
        Returns:
            DriftCheckResult with breach status
        """
        # Get check configuration
        check = self._get_check(check_id)
        if not check:
            return DriftCheckResult(
                check_id=check_id,
                check_name="Unknown",
                metric="unknown",
                is_breached=False,
                baseline_value=None,
                current_value=current_value,
                change_percent=None,
                severity=None,
                message="Check not found"
            )
        
        # Use provided baseline or stored baseline
        if baseline_value is None:
            baseline_value = float(check['baseline_value']) if check['baseline_value'] else None
        
        # If no baseline, can't check drift - set this as the baseline
        if baseline_value is None:
            self._update_baseline(check_id, current_value)
            return DriftCheckResult(
                check_id=check_id,
                check_name=check['name'],
                metric=check['metric'],
                is_breached=False,
                baseline_value=current_value,
                current_value=current_value,
                change_percent=0.0,
                severity=None,
                message="Baseline established"
            )
        
        # Calculate drift
        threshold = float(check['threshold'])
        comparison = check['comparison']
        
        is_breached, change_percent, severity = self._evaluate_drift(
            baseline_value, current_value, threshold, comparison
        )
        
        # Build message
        if is_breached:
            direction = "increased" if current_value > baseline_value else "decreased"
            message = f"{check['metric']} {direction} by {abs(change_percent):.2f}% (threshold: {threshold * 100:.1f}%)"
        else:
            message = f"{check['metric']} within acceptable range"
        
        # Update check status
        self._update_check_status(check_id, current_value, is_breached)
        
        return DriftCheckResult(
            check_id=check_id,
            check_name=check['name'],
            metric=check['metric'],
            is_breached=is_breached,
            baseline_value=baseline_value,
            current_value=current_value,
            change_percent=change_percent,
            severity=severity if is_breached else None,
            message=message
        )
    
    def check_run_metrics(
        self,
        run_id: str,
        metrics: Dict[str, float]
    ) -> List[DriftCheckResult]:
        """
        Check all configured drift checks against a run's metrics.
        
        Args:
            run_id: The run ID
            metrics: Dictionary of metric name -> value
            
        Returns:
            List of DriftCheckResults (only for metrics with configured checks)
        """
        results = []
        
        # Get the run's recipe ID
        run = self._get_run(run_id)
        if not run:
            return results
        
        # Get all active checks for this recipe
        checks = self._get_checks_for_recipe(run['recipe_id'])
        
        for check in checks:
            metric_name = check['metric']
            if metric_name in metrics:
                result = self.check_drift(
                    check_id=str(check['id']),
                    current_value=metrics[metric_name]
                )
                results.append(result)
                
                # Create alert if breached
                if result.is_breached:
                    self._create_alert(check, result, run_id)
        
        return results
    
    def create_check(
        self,
        name: str,
        metric: str,
        threshold: float,
        comparison: ComparisonType = ComparisonType.PERCENTAGE_BOTH,
        recipe_id: str = None,
        asset_id: str = None,
        description: str = None,
        check_frequency: str = 'on_run'
    ) -> str:
        """
        Create a new drift check.
        
        Args:
            name: Human-readable name for the check
            metric: Metric name to monitor (e.g., 'rmse', 'accuracy')
            threshold: Drift threshold (0.1 = 10% for percentage comparisons)
            comparison: Type of comparison
            recipe_id: Recipe to monitor (optional)
            asset_id: Specific asset to monitor (optional)
            description: Description of the check
            check_frequency: 'on_run', 'hourly', or 'daily'
            
        Returns:
            The created check ID
        """
        query = """
            INSERT INTO drift_checks (name, description, metric, threshold, comparison, 
                                      recipe_id, asset_id, check_frequency)
            VALUES (:name, :description, :metric, :threshold, :comparison, 
                    :recipe_id, :asset_id, :check_frequency)
            RETURNING id
        """
        
        with self.engine.begin() as conn:
            result = conn.execute(text(query), {
                'name': name,
                'description': description,
                'metric': metric,
                'threshold': threshold,
                'comparison': comparison.value,
                'recipe_id': recipe_id,
                'asset_id': asset_id,
                'check_frequency': check_frequency
            })
            check_id = str(result.fetchone()[0])
        
        logger.info(f"Created drift check {check_id}: {name} for metric {metric}")
        return check_id
    
    def get_alerts(
        self,
        check_id: str = None,
        unacknowledged_only: bool = False,
        limit: int = 100
    ) -> List[dict]:
        """Get drift alerts with optional filters."""
        query = "SELECT * FROM drift_alerts WHERE 1=1"
        params = {}
        
        if check_id:
            query += " AND drift_check_id = :check_id"
            params['check_id'] = check_id
        
        if unacknowledged_only:
            query += " AND acknowledged = false"
        
        query += " ORDER BY triggered_at DESC LIMIT :limit"
        params['limit'] = limit
        
        with self.engine.connect() as conn:
            result = conn.execute(text(query), params)
            return [dict(row._mapping) for row in result]
    
    def acknowledge_alert(self, alert_id: str, acknowledged_by: str = None):
        """Mark an alert as acknowledged."""
        query = """
            UPDATE drift_alerts 
            SET acknowledged = true, 
                acknowledged_at = NOW(),
                acknowledged_by = :acknowledged_by
            WHERE id = :alert_id
        """
        
        with self.engine.begin() as conn:
            conn.execute(text(query), {
                'alert_id': alert_id,
                'acknowledged_by': acknowledged_by
            })
    
    def _evaluate_drift(
        self,
        baseline: float,
        current: float,
        threshold: float,
        comparison: str
    ) -> tuple:
        """
        Evaluate if drift exceeds threshold.
        
        Returns:
            (is_breached, change_percent, severity)
        """
        if baseline == 0:
            # Avoid division by zero
            if current == 0:
                return False, 0.0, None
            change_percent = 100.0 if current > 0 else -100.0
        else:
            change_percent = ((current - baseline) / abs(baseline)) * 100
        
        is_breached = False
        
        if comparison == ComparisonType.ABSOLUTE.value:
            is_breached = abs(current - baseline) > threshold
        elif comparison == ComparisonType.PERCENTAGE_INCREASE.value:
            is_breached = change_percent > (threshold * 100)
        elif comparison == ComparisonType.PERCENTAGE_DECREASE.value:
            is_breached = change_percent < -(threshold * 100)
        elif comparison == ComparisonType.PERCENTAGE_BOTH.value:
            is_breached = abs(change_percent) > (threshold * 100)
        
        # Determine severity
        severity = None
        if is_breached:
            critical_threshold = threshold * self.critical_multiplier * 100
            if abs(change_percent) > critical_threshold:
                severity = Severity.CRITICAL
            else:
                severity = Severity.WARNING
        
        return is_breached, round(change_percent, 2), severity
    
    def _get_check(self, check_id: str) -> Optional[dict]:
        """Get check configuration by ID."""
        query = "SELECT * FROM drift_checks WHERE id = :check_id"
        
        with self.engine.connect() as conn:
            result = conn.execute(text(query), {'check_id': check_id}).fetchone()
            if result:
                return dict(result._mapping)
        return None
    
    def _get_run(self, run_id: str) -> Optional[dict]:
        """Get run by ID."""
        query = "SELECT * FROM ml_run WHERE id = :run_id"
        
        with self.engine.connect() as conn:
            result = conn.execute(text(query), {'run_id': run_id}).fetchone()
            if result:
                return dict(result._mapping)
        return None
    
    def _get_checks_for_recipe(self, recipe_id: str) -> List[dict]:
        """Get all active checks for a recipe."""
        query = """
            SELECT * FROM drift_checks 
            WHERE recipe_id = :recipe_id AND is_active = true
        """
        
        with self.engine.connect() as conn:
            result = conn.execute(text(query), {'recipe_id': recipe_id})
            return [dict(row._mapping) for row in result]
    
    def _update_baseline(self, check_id: str, value: float):
        """Set the baseline value for a check."""
        query = """
            UPDATE drift_checks 
            SET baseline_value = :value, updated_at = NOW()
            WHERE id = :check_id
        """
        
        with self.engine.begin() as conn:
            conn.execute(text(query), {'check_id': check_id, 'value': value})
    
    def _update_check_status(self, check_id: str, current_value: float, is_breached: bool):
        """Update check with latest value and status."""
        query = """
            UPDATE drift_checks 
            SET latest_value = :value, 
                is_breached = :is_breached,
                last_checked_at = NOW(),
                updated_at = NOW()
            WHERE id = :check_id
        """
        
        with self.engine.begin() as conn:
            conn.execute(text(query), {
                'check_id': check_id,
                'value': current_value,
                'is_breached': is_breached
            })
    
    def _create_alert(self, check: dict, result: DriftCheckResult, run_id: str = None):
        """Create a drift alert."""
        query = """
            INSERT INTO drift_alerts (
                drift_check_id, run_id, severity, baseline_value, 
                current_value, change_percent, message
            )
            VALUES (:check_id, :run_id, :severity, :baseline, :current, :change, :message)
            RETURNING id
        """
        
        with self.engine.begin() as conn:
            result_row = conn.execute(text(query), {
                'check_id': check['id'],
                'run_id': run_id,
                'severity': result.severity.value,
                'baseline': result.baseline_value,
                'current': result.current_value,
                'change': result.change_percent,
                'message': result.message
            })
            alert_id = str(result_row.fetchone()[0])
        
        logger.warning(f"Drift alert created: {result.message}")

        # Send notifications (fire and forget)
        self._send_alert_notification(check, result)

        return alert_id

    def _send_alert_notification(self, check: dict, result: DriftCheckResult):
        """Send notification for drift alert (fire and forget)."""
        try:
            notification_service = get_notification_service()

            # Get notification channels from check config (default to all enabled)
            channels = check.get('notification_channels')

            # Create async task for notification
            async def send_notification():
                try:
                    await notification_service.send_drift_alert(
                        check_name=check.get('name', 'Unknown Check'),
                        metric=check.get('metric_name', 'unknown'),
                        baseline=float(result.baseline_value),
                        current=float(result.current_value),
                        change_percent=float(result.change_percent),
                        severity=result.severity.value,
                        channels=channels
                    )
                except Exception as e:
                    logger.error(f"Failed to send drift notification: {e}")

            # Try to run in existing event loop, or create new one
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(send_notification())
            except RuntimeError:
                # No running loop, run synchronously
                asyncio.run(send_notification())

        except Exception as e:
            logger.error(f"Error setting up drift notification: {e}")


# Singleton instance
_detector_instance: Optional[DriftDetector] = None


def get_drift_detector() -> DriftDetector:
    """Get singleton drift detector instance."""
    global _detector_instance
    if _detector_instance is None:
        _detector_instance = DriftDetector()
    return _detector_instance
