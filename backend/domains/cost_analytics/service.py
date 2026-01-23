"""Cost Analytics Service.

Provides aggregated cost analysis, budget tracking, and spending trends.
"""
import logging
from typing import List, Optional
from decimal import Decimal
from datetime import datetime, timedelta
from dataclasses import dataclass
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class CostSummary:
    """Summary of costs for a time period."""
    total_cost_usd: float
    total_runs: int
    average_cost_per_run: float
    total_runtime_hours: float


@dataclass
class ProviderCost:
    """Cost breakdown by provider."""
    provider: str
    total_cost_usd: float
    run_count: int
    total_runtime_hours: float
    average_cost_per_run: float


@dataclass
class ModelCost:
    """Cost breakdown by model."""
    model_id: str
    model_name: str
    total_cost_usd: float
    run_count: int
    total_runtime_hours: float


@dataclass
class CostTrend:
    """Cost data for a time period."""
    period_start: datetime
    period_end: datetime
    total_cost_usd: float
    run_count: int
    average_cost_per_run: float


@dataclass
class BudgetStatus:
    """Status of a cost budget."""
    budget_id: str
    budget_name: str
    budget_amount_usd: float
    current_spend_usd: float
    percent_used: float
    remaining_usd: float
    is_exceeded: bool
    alert_triggered: bool
    period_start: datetime
    period_end: datetime


class CostAnalyticsService:
    """Service for cost analytics and budget management."""

    def __init__(self, engine: Optional[Engine] = None):
        self.engine = engine or create_engine(settings.database_url)

    def get_cost_summary(self, start: datetime, end: datetime) -> CostSummary:
        """
        Get cost summary for a time period.

        Args:
            start: Start of period
            end: End of period

        Returns:
            CostSummary with aggregated data
        """
        query = """
            SELECT
                COALESCE(SUM(COALESCE(actual_cost_usd, estimated_cost_usd, 0)), 0) as total_cost,
                COUNT(*) as total_runs,
                COALESCE(SUM(runtime_seconds), 0) as total_runtime_seconds
            FROM ml_run
            WHERE started_at >= :start AND started_at < :end
        """

        with self.engine.connect() as conn:
            result = conn.execute(text(query), {'start': start, 'end': end}).fetchone()

        total_cost = float(result[0] or 0)
        total_runs = result[1] or 0
        total_runtime_seconds = result[2] or 0

        return CostSummary(
            total_cost_usd=round(total_cost, 4),
            total_runs=total_runs,
            average_cost_per_run=round(total_cost / total_runs, 4) if total_runs > 0 else 0,
            total_runtime_hours=round(total_runtime_seconds / 3600, 2)
        )

    def get_costs_by_provider(self, start: datetime, end: datetime) -> List[ProviderCost]:
        """
        Get costs broken down by compute provider.

        Args:
            start: Start of period
            end: End of period

        Returns:
            List of ProviderCost objects
        """
        query = """
            SELECT
                COALESCE(compute_target, 'local') as provider,
                COALESCE(SUM(COALESCE(actual_cost_usd, estimated_cost_usd, 0)), 0) as total_cost,
                COUNT(*) as run_count,
                COALESCE(SUM(runtime_seconds), 0) as total_runtime_seconds
            FROM ml_run
            WHERE started_at >= :start AND started_at < :end
            GROUP BY COALESCE(compute_target, 'local')
            ORDER BY total_cost DESC
        """

        with self.engine.connect() as conn:
            result = conn.execute(text(query), {'start': start, 'end': end})
            rows = [dict(row._mapping) for row in result]

        return [
            ProviderCost(
                provider=r['provider'],
                total_cost_usd=round(float(r['total_cost']), 4),
                run_count=r['run_count'],
                total_runtime_hours=round(r['total_runtime_seconds'] / 3600, 2),
                average_cost_per_run=round(float(r['total_cost']) / r['run_count'], 4) if r['run_count'] > 0 else 0
            )
            for r in rows
        ]

    def get_costs_by_model(self, start: datetime, end: datetime) -> List[ModelCost]:
        """
        Get costs broken down by ML model.

        Args:
            start: Start of period
            end: End of period

        Returns:
            List of ModelCost objects
        """
        query = """
            SELECT
                r.model_id,
                COALESCE(m.name, 'No Model') as model_name,
                COALESCE(SUM(COALESCE(r.actual_cost_usd, r.estimated_cost_usd, 0)), 0) as total_cost,
                COUNT(*) as run_count,
                COALESCE(SUM(r.runtime_seconds), 0) as total_runtime_seconds
            FROM ml_run r
            LEFT JOIN ml_model m ON r.model_id = m.id
            WHERE r.started_at >= :start AND r.started_at < :end
            GROUP BY r.model_id, m.name
            ORDER BY total_cost DESC
        """

        with self.engine.connect() as conn:
            result = conn.execute(text(query), {'start': start, 'end': end})
            rows = [dict(row._mapping) for row in result]

        return [
            ModelCost(
                model_id=r['model_id'] or 'none',
                model_name=r['model_name'],
                total_cost_usd=round(float(r['total_cost']), 4),
                run_count=r['run_count'],
                total_runtime_hours=round(r['total_runtime_seconds'] / 3600, 2)
            )
            for r in rows
        ]

    def get_cost_trends(self, periods: int, granularity: str = "daily") -> List[CostTrend]:
        """
        Get cost trends over time.

        Args:
            periods: Number of periods to return
            granularity: 'daily', 'weekly', or 'monthly'

        Returns:
            List of CostTrend objects (most recent first)
        """
        # Calculate interval
        if granularity == "daily":
            interval = timedelta(days=1)
        elif granularity == "weekly":
            interval = timedelta(weeks=1)
        else:  # monthly
            interval = timedelta(days=30)

        trends = []
        now = datetime.utcnow()

        for i in range(periods):
            period_end = now - (i * interval)
            period_start = period_end - interval

            summary = self.get_cost_summary(period_start, period_end)

            trends.append(CostTrend(
                period_start=period_start,
                period_end=period_end,
                total_cost_usd=summary.total_cost_usd,
                run_count=summary.total_runs,
                average_cost_per_run=summary.average_cost_per_run
            ))

        return trends

    def create_budget(
        self,
        name: str,
        budget_amount_usd: float,
        period: str,
        alert_threshold_percent: int = 80,
        scope_type: str = "global",
        scope_id: Optional[str] = None
    ) -> str:
        """
        Create a new cost budget.

        Args:
            name: Budget name
            budget_amount_usd: Budget amount in USD
            period: 'daily', 'weekly', or 'monthly'
            alert_threshold_percent: Alert when this % is reached
            scope_type: 'global', 'provider', or 'model'
            scope_id: ID for scoped budgets

        Returns:
            Created budget ID
        """
        query = """
            INSERT INTO cost_budgets (name, budget_amount_usd, period, alert_threshold_percent,
                                      scope_type, scope_id)
            VALUES (:name, :amount, :period, :alert_threshold, :scope_type, :scope_id)
            RETURNING id
        """

        with self.engine.begin() as conn:
            result = conn.execute(text(query), {
                'name': name,
                'amount': budget_amount_usd,
                'period': period,
                'alert_threshold': alert_threshold_percent,
                'scope_type': scope_type,
                'scope_id': scope_id
            })
            budget_id = str(result.fetchone()[0])

        logger.info(f"Created budget {budget_id}: {name} (${budget_amount_usd}/{period})")
        return budget_id

    def check_budget_status(self, budget_id: str) -> Optional[BudgetStatus]:
        """
        Check current status of a budget.

        Args:
            budget_id: Budget ID to check

        Returns:
            BudgetStatus or None if not found
        """
        # Get budget config
        budget_query = "SELECT * FROM cost_budgets WHERE id = :budget_id"

        with self.engine.connect() as conn:
            budget_result = conn.execute(text(budget_query), {'budget_id': budget_id}).fetchone()

        if not budget_result:
            return None

        budget = dict(budget_result._mapping)

        # Calculate period boundaries
        now = datetime.utcnow()
        period = budget['period']

        if period == 'daily':
            period_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            period_end = period_start + timedelta(days=1)
        elif period == 'weekly':
            # Start of week (Monday)
            period_start = now - timedelta(days=now.weekday())
            period_start = period_start.replace(hour=0, minute=0, second=0, microsecond=0)
            period_end = period_start + timedelta(weeks=1)
        else:  # monthly
            period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            # First day of next month
            if now.month == 12:
                period_end = period_start.replace(year=now.year + 1, month=1)
            else:
                period_end = period_start.replace(month=now.month + 1)

        # Calculate current spend within scope
        spend_query = """
            SELECT COALESCE(SUM(COALESCE(actual_cost_usd, estimated_cost_usd, 0)), 0) as total_spend
            FROM ml_run
            WHERE started_at >= :start AND started_at < :end
        """
        params = {'start': period_start, 'end': period_end}

        # Apply scope filter
        scope_type = budget['scope_type']
        scope_id = budget['scope_id']

        if scope_type == 'provider' and scope_id:
            spend_query += " AND compute_target = :scope_id"
            params['scope_id'] = scope_id
        elif scope_type == 'model' and scope_id:
            spend_query += " AND model_id = :scope_id"
            params['scope_id'] = scope_id

        with self.engine.connect() as conn:
            spend_result = conn.execute(text(spend_query), params).fetchone()

        current_spend = float(spend_result[0] or 0)
        budget_amount = float(budget['budget_amount_usd'])
        alert_threshold = budget['alert_threshold_percent']

        percent_used = (current_spend / budget_amount * 100) if budget_amount > 0 else 0
        remaining = max(0, budget_amount - current_spend)

        is_exceeded = current_spend >= budget_amount
        alert_triggered = percent_used >= alert_threshold

        # Record alert if threshold crossed
        if alert_triggered and budget['is_active']:
            self._record_budget_alert(budget_id, current_spend, budget_amount, percent_used)

        return BudgetStatus(
            budget_id=str(budget['id']),
            budget_name=budget['name'],
            budget_amount_usd=budget_amount,
            current_spend_usd=round(current_spend, 4),
            percent_used=round(percent_used, 2),
            remaining_usd=round(remaining, 4),
            is_exceeded=is_exceeded,
            alert_triggered=alert_triggered,
            period_start=period_start,
            period_end=period_end
        )

    def check_all_budgets(self) -> List[BudgetStatus]:
        """Check status of all active budgets."""
        query = "SELECT id FROM cost_budgets WHERE is_active = true"

        with self.engine.connect() as conn:
            result = conn.execute(text(query))
            budget_ids = [row[0] for row in result]

        statuses = []
        for budget_id in budget_ids:
            status = self.check_budget_status(str(budget_id))
            if status:
                statuses.append(status)

        return statuses

    def _record_budget_alert(
        self,
        budget_id: str,
        current_spend: float,
        budget_amount: float,
        percent_used: float
    ):
        """Record a budget alert (prevent duplicates within same period)."""
        # Check for existing alert in this period
        check_query = """
            SELECT id FROM cost_budget_alerts
            WHERE budget_id = :budget_id
            AND triggered_at > NOW() - INTERVAL '1 hour'
        """

        with self.engine.connect() as conn:
            existing = conn.execute(text(check_query), {'budget_id': budget_id}).fetchone()

        if existing:
            return  # Already alerted recently

        # Create alert
        insert_query = """
            INSERT INTO cost_budget_alerts (budget_id, current_spend_usd, budget_amount_usd, percent_used)
            VALUES (:budget_id, :current_spend, :budget_amount, :percent_used)
        """

        with self.engine.begin() as conn:
            conn.execute(text(insert_query), {
                'budget_id': budget_id,
                'current_spend': current_spend,
                'budget_amount': budget_amount,
                'percent_used': int(percent_used)
            })

        logger.warning(f"Budget alert: {budget_id} at {percent_used:.1f}% (${current_spend:.2f}/${budget_amount:.2f})")


# Singleton instance
_service_instance: Optional[CostAnalyticsService] = None


def get_cost_analytics_service() -> CostAnalyticsService:
    """Get singleton cost analytics service instance."""
    global _service_instance
    if _service_instance is None:
        _service_instance = CostAnalyticsService()
    return _service_instance
