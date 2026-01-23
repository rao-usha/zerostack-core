"""Model Monitoring Service.

Handles latency metrics recording, error tracking, health score calculation,
and SLA compliance checking for production ML models.
"""
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from decimal import Decimal
import statistics
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class LatencyMetrics:
    """Latency percentile metrics for a time window."""
    id: str
    model_id: str
    recorded_at: datetime
    p50_ms: float
    p95_ms: float
    p99_ms: float
    request_count: int
    window_minutes: int


@dataclass
class ErrorMetrics:
    """Error rate metrics for a time window."""
    id: str
    model_id: str
    recorded_at: datetime
    total_requests: int
    error_count: int
    error_rate: float
    error_types: Dict[str, int]
    window_minutes: int


@dataclass
class HealthScore:
    """Health score with component breakdown."""
    overall: int  # 0-100
    latency_score: int  # 0-100
    error_score: int  # 0-100
    latency_details: str
    error_details: str


@dataclass
class SLAConfig:
    """SLA configuration for a model."""
    id: str
    model_id: str
    max_latency_p95_ms: int
    max_error_rate_percent: float
    alerting_enabled: bool


@dataclass
class SLAStatus:
    """Current SLA compliance status."""
    model_id: str
    is_compliant: bool
    latency_compliant: bool
    error_rate_compliant: bool
    current_p95_ms: Optional[float]
    current_error_rate: Optional[float]
    sla_config: SLAConfig
    message: str


@dataclass
class MonitoringSummary:
    """Complete monitoring summary for a model."""
    model_id: str
    model_name: str
    health_score: HealthScore
    sla_status: Optional[SLAStatus]
    recent_latency: List[LatencyMetrics]
    recent_errors: List[ErrorMetrics]
    active_alerts: int
    total_requests_24h: int


class MonitoringService:
    """Service for model monitoring and health tracking."""

    def __init__(self, engine: Optional[Engine] = None):
        self.engine = engine or create_engine(settings.database_url)

    def record_latency_metrics(
        self,
        model_id: str,
        latencies_ms: List[float],
        window_minutes: int = 5
    ) -> str:
        """
        Record latency metrics for a model.

        Args:
            model_id: The model ID
            latencies_ms: List of latency values in milliseconds
            window_minutes: Time window for aggregation

        Returns:
            ID of the created metrics record
        """
        if not latencies_ms:
            raise ValueError("At least one latency value required")

        sorted_latencies = sorted(latencies_ms)
        n = len(sorted_latencies)

        p50 = sorted_latencies[int(n * 0.5)]
        p95 = sorted_latencies[int(n * 0.95)]
        p99 = sorted_latencies[int(n * 0.99)]

        query = """
            INSERT INTO model_latency_metrics
            (model_id, p50_ms, p95_ms, p99_ms, request_count, window_minutes)
            VALUES (:model_id, :p50, :p95, :p99, :count, :window)
            RETURNING id
        """

        with self.engine.begin() as conn:
            result = conn.execute(text(query), {
                'model_id': model_id,
                'p50': p50,
                'p95': p95,
                'p99': p99,
                'count': n,
                'window': window_minutes
            }).fetchone()

        logger.info(f"Recorded latency metrics for model {model_id}: p50={p50:.2f}ms, p95={p95:.2f}ms, p99={p99:.2f}ms")
        return str(result[0])

    def record_error(
        self,
        model_id: str,
        total_requests: int,
        error_count: int,
        error_types: Optional[Dict[str, int]] = None,
        window_minutes: int = 5
    ) -> str:
        """
        Record error rate metrics for a model.

        Args:
            model_id: The model ID
            total_requests: Total number of requests in the window
            error_count: Number of errors
            error_types: Breakdown by error type
            window_minutes: Time window for aggregation

        Returns:
            ID of the created metrics record
        """
        query = """
            INSERT INTO model_error_rates
            (model_id, total_requests, error_count, error_types, window_minutes)
            VALUES (:model_id, :total, :errors, :types::jsonb, :window)
            RETURNING id
        """

        import json
        with self.engine.begin() as conn:
            result = conn.execute(text(query), {
                'model_id': model_id,
                'total': total_requests,
                'errors': error_count,
                'types': json.dumps(error_types or {}),
                'window': window_minutes
            }).fetchone()

        error_rate = (error_count / total_requests * 100) if total_requests > 0 else 0
        logger.info(f"Recorded error metrics for model {model_id}: {error_count}/{total_requests} ({error_rate:.2f}%)")
        return str(result[0])

    def get_latency_history(
        self,
        model_id: str,
        hours: int = 24
    ) -> List[LatencyMetrics]:
        """
        Get latency history for a model.

        Args:
            model_id: The model ID
            hours: Number of hours of history

        Returns:
            List of LatencyMetrics ordered by time
        """
        query = """
            SELECT id, model_id, recorded_at, p50_ms, p95_ms, p99_ms, request_count, window_minutes
            FROM model_latency_metrics
            WHERE model_id = :model_id
            AND recorded_at > NOW() - INTERVAL ':hours hours'
            ORDER BY recorded_at ASC
        """.replace(':hours', str(hours))

        with self.engine.connect() as conn:
            result = conn.execute(text(query), {'model_id': model_id})
            rows = [dict(row._mapping) for row in result]

        return [
            LatencyMetrics(
                id=str(r['id']),
                model_id=r['model_id'],
                recorded_at=r['recorded_at'],
                p50_ms=float(r['p50_ms']),
                p95_ms=float(r['p95_ms']),
                p99_ms=float(r['p99_ms']),
                request_count=r['request_count'],
                window_minutes=r['window_minutes']
            )
            for r in rows
        ]

    def get_error_history(
        self,
        model_id: str,
        hours: int = 24
    ) -> List[ErrorMetrics]:
        """
        Get error rate history for a model.

        Args:
            model_id: The model ID
            hours: Number of hours of history

        Returns:
            List of ErrorMetrics ordered by time
        """
        query = """
            SELECT id, model_id, recorded_at, total_requests, error_count, error_types, window_minutes
            FROM model_error_rates
            WHERE model_id = :model_id
            AND recorded_at > NOW() - INTERVAL ':hours hours'
            ORDER BY recorded_at ASC
        """.replace(':hours', str(hours))

        with self.engine.connect() as conn:
            result = conn.execute(text(query), {'model_id': model_id})
            rows = [dict(row._mapping) for row in result]

        return [
            ErrorMetrics(
                id=str(r['id']),
                model_id=r['model_id'],
                recorded_at=r['recorded_at'],
                total_requests=r['total_requests'],
                error_count=r['error_count'],
                error_rate=(r['error_count'] / r['total_requests'] * 100) if r['total_requests'] > 0 else 0,
                error_types=r['error_types'] or {},
                window_minutes=r['window_minutes']
            )
            for r in rows
        ]

    def calculate_health_score(self, model_id: str) -> HealthScore:
        """
        Calculate health score for a model.

        Health score formula:
        - Latency score: 100 if p95 < SLA threshold, decreases linearly to 0 at 2x threshold
        - Error score: 100 - (error_rate * 10), min 0
        - Overall = (latency_score + error_score) / 2

        Args:
            model_id: The model ID

        Returns:
            HealthScore with overall and component scores
        """
        # Get SLA config (or use defaults)
        sla = self._get_sla_config(model_id)
        max_latency = sla.max_latency_p95_ms if sla else 500
        max_error_rate = sla.max_error_rate_percent if sla else 1.0

        # Get recent latency (last hour)
        latency_query = """
            SELECT AVG(p95_ms) as avg_p95
            FROM model_latency_metrics
            WHERE model_id = :model_id
            AND recorded_at > NOW() - INTERVAL '1 hour'
        """

        # Get recent error rate (last hour)
        error_query = """
            SELECT
                SUM(error_count) as total_errors,
                SUM(total_requests) as total_requests
            FROM model_error_rates
            WHERE model_id = :model_id
            AND recorded_at > NOW() - INTERVAL '1 hour'
        """

        with self.engine.connect() as conn:
            latency_result = conn.execute(text(latency_query), {'model_id': model_id}).fetchone()
            error_result = conn.execute(text(error_query), {'model_id': model_id}).fetchone()

        # Calculate latency score
        avg_p95 = float(latency_result[0]) if latency_result and latency_result[0] else None
        if avg_p95 is None:
            latency_score = 100
            latency_details = "No recent latency data"
        elif avg_p95 <= max_latency:
            latency_score = 100
            latency_details = f"P95 {avg_p95:.1f}ms within threshold ({max_latency}ms)"
        elif avg_p95 <= max_latency * 2:
            # Linear decrease from 100 to 0 between threshold and 2x threshold
            latency_score = int(100 * (2 - avg_p95 / max_latency))
            latency_details = f"P95 {avg_p95:.1f}ms above threshold ({max_latency}ms)"
        else:
            latency_score = 0
            latency_details = f"P95 {avg_p95:.1f}ms critically above threshold ({max_latency}ms)"

        # Calculate error score
        total_errors = error_result[0] if error_result and error_result[0] else 0
        total_requests = error_result[1] if error_result and error_result[1] else 0

        if total_requests == 0:
            error_score = 100
            error_rate = 0
            error_details = "No recent requests"
        else:
            error_rate = (total_errors / total_requests) * 100
            error_score = max(0, int(100 - (error_rate * 10)))
            if error_rate <= max_error_rate:
                error_details = f"Error rate {error_rate:.2f}% within threshold ({max_error_rate}%)"
            else:
                error_details = f"Error rate {error_rate:.2f}% above threshold ({max_error_rate}%)"

        overall = (latency_score + error_score) // 2

        return HealthScore(
            overall=overall,
            latency_score=latency_score,
            error_score=error_score,
            latency_details=latency_details,
            error_details=error_details
        )

    def get_sla_config(self, model_id: str) -> Optional[SLAConfig]:
        """Get SLA configuration for a model."""
        return self._get_sla_config(model_id)

    def _get_sla_config(self, model_id: str) -> Optional[SLAConfig]:
        """Internal method to get SLA config."""
        query = """
            SELECT id, model_id, max_latency_p95_ms, max_error_rate_percent, alerting_enabled
            FROM model_sla_config
            WHERE model_id = :model_id
        """

        with self.engine.connect() as conn:
            result = conn.execute(text(query), {'model_id': model_id}).fetchone()

        if not result:
            return None

        return SLAConfig(
            id=str(result[0]),
            model_id=result[1],
            max_latency_p95_ms=result[2],
            max_error_rate_percent=float(result[3]),
            alerting_enabled=result[4]
        )

    def create_or_update_sla(
        self,
        model_id: str,
        max_latency_p95_ms: int = 500,
        max_error_rate_percent: float = 1.0,
        alerting_enabled: bool = True
    ) -> str:
        """
        Create or update SLA configuration for a model.

        Args:
            model_id: The model ID
            max_latency_p95_ms: Maximum acceptable P95 latency
            max_error_rate_percent: Maximum acceptable error rate percentage
            alerting_enabled: Whether to send alerts on SLA breach

        Returns:
            ID of the SLA config
        """
        query = """
            INSERT INTO model_sla_config
            (model_id, max_latency_p95_ms, max_error_rate_percent, alerting_enabled)
            VALUES (:model_id, :latency, :error_rate, :alerting)
            ON CONFLICT (model_id) DO UPDATE SET
                max_latency_p95_ms = EXCLUDED.max_latency_p95_ms,
                max_error_rate_percent = EXCLUDED.max_error_rate_percent,
                alerting_enabled = EXCLUDED.alerting_enabled,
                updated_at = NOW()
            RETURNING id
        """

        with self.engine.begin() as conn:
            result = conn.execute(text(query), {
                'model_id': model_id,
                'latency': max_latency_p95_ms,
                'error_rate': max_error_rate_percent,
                'alerting': alerting_enabled
            }).fetchone()

        logger.info(f"Updated SLA config for model {model_id}: latency={max_latency_p95_ms}ms, error_rate={max_error_rate_percent}%")
        return str(result[0])

    def check_sla_compliance(self, model_id: str) -> SLAStatus:
        """
        Check SLA compliance for a model.

        Args:
            model_id: The model ID

        Returns:
            SLAStatus with compliance details
        """
        sla = self._get_sla_config(model_id)

        if not sla:
            # Create default SLA config
            self.create_or_update_sla(model_id)
            sla = self._get_sla_config(model_id)

        # Get recent metrics (last hour average)
        latency_query = """
            SELECT AVG(p95_ms) as avg_p95
            FROM model_latency_metrics
            WHERE model_id = :model_id
            AND recorded_at > NOW() - INTERVAL '1 hour'
        """

        error_query = """
            SELECT
                SUM(error_count) as total_errors,
                SUM(total_requests) as total_requests
            FROM model_error_rates
            WHERE model_id = :model_id
            AND recorded_at > NOW() - INTERVAL '1 hour'
        """

        with self.engine.connect() as conn:
            latency_result = conn.execute(text(latency_query), {'model_id': model_id}).fetchone()
            error_result = conn.execute(text(error_query), {'model_id': model_id}).fetchone()

        # Check latency compliance
        current_p95 = float(latency_result[0]) if latency_result and latency_result[0] else None
        latency_compliant = current_p95 is None or current_p95 <= sla.max_latency_p95_ms

        # Check error rate compliance
        total_errors = error_result[0] if error_result and error_result[0] else 0
        total_requests = error_result[1] if error_result and error_result[1] else 0
        current_error_rate = (total_errors / total_requests * 100) if total_requests > 0 else 0.0
        error_compliant = total_requests == 0 or current_error_rate <= sla.max_error_rate_percent

        is_compliant = latency_compliant and error_compliant

        # Build status message
        messages = []
        if not latency_compliant:
            messages.append(f"P95 latency ({current_p95:.1f}ms) exceeds threshold ({sla.max_latency_p95_ms}ms)")
        if not error_compliant:
            messages.append(f"Error rate ({current_error_rate:.2f}%) exceeds threshold ({sla.max_error_rate_percent}%)")

        message = "SLA compliant" if is_compliant else "; ".join(messages)

        return SLAStatus(
            model_id=model_id,
            is_compliant=is_compliant,
            latency_compliant=latency_compliant,
            error_rate_compliant=error_compliant,
            current_p95_ms=current_p95,
            current_error_rate=current_error_rate,
            sla_config=sla,
            message=message
        )

    def get_monitoring_summary(self, model_id: str) -> MonitoringSummary:
        """
        Get complete monitoring summary for a model.

        Args:
            model_id: The model ID

        Returns:
            MonitoringSummary with all monitoring data
        """
        # Get model name
        model_query = "SELECT name FROM ml_model WHERE id = :model_id"
        with self.engine.connect() as conn:
            model_result = conn.execute(text(model_query), {'model_id': model_id}).fetchone()
            model_name = model_result[0] if model_result else "Unknown"

        # Get health score
        health_score = self.calculate_health_score(model_id)

        # Get SLA status
        sla_status = self.check_sla_compliance(model_id)

        # Get recent metrics
        recent_latency = self.get_latency_history(model_id, hours=24)
        recent_errors = self.get_error_history(model_id, hours=24)

        # Get active alerts count
        alerts_query = """
            SELECT COUNT(*) FROM model_sla_alerts
            WHERE model_id = :model_id
            AND acknowledged = false
            AND resolved_at IS NULL
        """
        with self.engine.connect() as conn:
            alerts_result = conn.execute(text(alerts_query), {'model_id': model_id}).fetchone()
            active_alerts = alerts_result[0] if alerts_result else 0

        # Total requests in 24h
        requests_query = """
            SELECT SUM(request_count) FROM model_latency_metrics
            WHERE model_id = :model_id
            AND recorded_at > NOW() - INTERVAL '24 hours'
        """
        with self.engine.connect() as conn:
            requests_result = conn.execute(text(requests_query), {'model_id': model_id}).fetchone()
            total_requests = requests_result[0] if requests_result and requests_result[0] else 0

        return MonitoringSummary(
            model_id=model_id,
            model_name=model_name,
            health_score=health_score,
            sla_status=sla_status,
            recent_latency=recent_latency,
            recent_errors=recent_errors,
            active_alerts=active_alerts,
            total_requests_24h=total_requests
        )

    def get_active_alerts(self, model_id: Optional[str] = None) -> List[Dict]:
        """
        Get active SLA alerts.

        Args:
            model_id: Optional filter by model ID

        Returns:
            List of active alerts
        """
        query = """
            SELECT a.*, m.name as model_name
            FROM model_sla_alerts a
            JOIN ml_model m ON a.model_id = m.id
            WHERE a.acknowledged = false
            AND a.resolved_at IS NULL
        """
        params = {}

        if model_id:
            query += " AND a.model_id = :model_id"
            params['model_id'] = model_id

        query += " ORDER BY a.triggered_at DESC"

        with self.engine.connect() as conn:
            result = conn.execute(text(query), params)
            return [dict(row._mapping) for row in result]

    def acknowledge_alert(self, alert_id: str, acknowledged_by: str) -> bool:
        """
        Acknowledge an SLA alert.

        Args:
            alert_id: The alert ID
            acknowledged_by: User acknowledging the alert

        Returns:
            True if successful
        """
        query = """
            UPDATE model_sla_alerts
            SET acknowledged = true, acknowledged_by = :user
            WHERE id = :id
        """

        with self.engine.begin() as conn:
            result = conn.execute(text(query), {
                'id': alert_id,
                'user': acknowledged_by
            })

        return result.rowcount > 0

    def resolve_alert(self, alert_id: str) -> bool:
        """
        Mark an alert as resolved.

        Args:
            alert_id: The alert ID

        Returns:
            True if successful
        """
        query = """
            UPDATE model_sla_alerts
            SET resolved_at = NOW()
            WHERE id = :id
        """

        with self.engine.begin() as conn:
            result = conn.execute(text(query), {'id': alert_id})

        return result.rowcount > 0


# Singleton instance
_service_instance: Optional[MonitoringService] = None


def get_monitoring_service() -> MonitoringService:
    """Get singleton monitoring service instance."""
    global _service_instance
    if _service_instance is None:
        _service_instance = MonitoringService()
    return _service_instance
