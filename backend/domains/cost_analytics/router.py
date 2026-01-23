"""Cost Analytics API router.

Provides endpoints for analyzing ML run costs, viewing spending trends,
and managing cost budgets.
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text

from core.config import settings
from .service import get_cost_analytics_service, CostSummary, ProviderCost, ModelCost, CostTrend, BudgetStatus

router = APIRouter(prefix="/cost-analytics", tags=["cost-analytics"])
engine = create_engine(settings.database_url)


# ========================================
# Pydantic Models
# ========================================

class CostSummaryResponse(BaseModel):
    """Response for cost summary."""
    total_cost_usd: float
    total_runs: int
    average_cost_per_run: float
    total_runtime_hours: float
    period_start: datetime
    period_end: datetime

    class Config:
        from_attributes = True


class ProviderCostResponse(BaseModel):
    """Response for costs by provider."""
    provider: str
    total_cost_usd: float
    run_count: int
    total_runtime_hours: float
    average_cost_per_run: float


class ModelCostResponse(BaseModel):
    """Response for costs by model."""
    model_name: str
    model_id: str
    total_cost_usd: float
    run_count: int
    total_runtime_hours: float


class CostTrendResponse(BaseModel):
    """Response for cost trends."""
    period_start: datetime
    period_end: datetime
    total_cost_usd: float
    run_count: int
    average_cost_per_run: float


class RunCostResponse(BaseModel):
    """Response for individual run costs."""
    run_id: str
    model_id: Optional[str]
    model_name: Optional[str]
    recipe_id: str
    status: str
    gpu_type: Optional[str]
    runtime_seconds: Optional[int]
    estimated_cost_usd: Optional[float]
    actual_cost_usd: Optional[float]
    started_at: Optional[datetime]
    finished_at: Optional[datetime]


class BudgetCreate(BaseModel):
    """Request to create a budget."""
    name: str
    budget_amount_usd: float = Field(gt=0)
    period: str = Field(pattern="^(daily|weekly|monthly)$")
    alert_threshold_percent: int = Field(default=80, ge=1, le=100)
    scope_type: str = Field(default="global", pattern="^(global|provider|model)$")
    scope_id: Optional[str] = None


class BudgetResponse(BaseModel):
    """Response for a budget."""
    id: str
    name: str
    budget_amount_usd: float
    period: str
    alert_threshold_percent: int
    scope_type: str
    scope_id: Optional[str]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class BudgetStatusResponse(BaseModel):
    """Response for budget status."""
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


# ========================================
# Summary Endpoints
# ========================================

@router.get("/summary", response_model=CostSummaryResponse)
async def get_cost_summary(
    start: Optional[datetime] = Query(None, description="Start of period"),
    end: Optional[datetime] = Query(None, description="End of period")
):
    """
    Get cost summary for a time period.

    Defaults to last 30 days if no dates provided.
    """
    service = get_cost_analytics_service()

    if not end:
        end = datetime.utcnow()
    if not start:
        start = end - timedelta(days=30)

    summary = service.get_cost_summary(start, end)

    return CostSummaryResponse(
        total_cost_usd=summary.total_cost_usd,
        total_runs=summary.total_runs,
        average_cost_per_run=summary.average_cost_per_run,
        total_runtime_hours=summary.total_runtime_hours,
        period_start=start,
        period_end=end
    )


@router.get("/by-provider", response_model=List[ProviderCostResponse])
async def get_costs_by_provider(
    start: Optional[datetime] = Query(None),
    end: Optional[datetime] = Query(None)
):
    """Get costs broken down by compute provider."""
    service = get_cost_analytics_service()

    if not end:
        end = datetime.utcnow()
    if not start:
        start = end - timedelta(days=30)

    costs = service.get_costs_by_provider(start, end)

    return [
        ProviderCostResponse(
            provider=c.provider,
            total_cost_usd=c.total_cost_usd,
            run_count=c.run_count,
            total_runtime_hours=c.total_runtime_hours,
            average_cost_per_run=c.average_cost_per_run
        )
        for c in costs
    ]


@router.get("/by-model", response_model=List[ModelCostResponse])
async def get_costs_by_model(
    start: Optional[datetime] = Query(None),
    end: Optional[datetime] = Query(None)
):
    """Get costs broken down by ML model."""
    service = get_cost_analytics_service()

    if not end:
        end = datetime.utcnow()
    if not start:
        start = end - timedelta(days=30)

    costs = service.get_costs_by_model(start, end)

    return [
        ModelCostResponse(
            model_name=c.model_name,
            model_id=c.model_id,
            total_cost_usd=c.total_cost_usd,
            run_count=c.run_count,
            total_runtime_hours=c.total_runtime_hours
        )
        for c in costs
    ]


@router.get("/trends", response_model=List[CostTrendResponse])
async def get_cost_trends(
    periods: int = Query(7, ge=1, le=90, description="Number of periods"),
    granularity: str = Query("daily", pattern="^(daily|weekly|monthly)$")
):
    """
    Get cost trends over time.

    Returns spending for each period going back from today.
    """
    service = get_cost_analytics_service()
    trends = service.get_cost_trends(periods, granularity)

    return [
        CostTrendResponse(
            period_start=t.period_start,
            period_end=t.period_end,
            total_cost_usd=t.total_cost_usd,
            run_count=t.run_count,
            average_cost_per_run=t.average_cost_per_run
        )
        for t in trends
    ]


@router.get("/runs", response_model=List[RunCostResponse])
async def get_run_costs(
    limit: int = Query(50, ge=1, le=500),
    model_id: Optional[str] = Query(None),
    provider: Optional[str] = Query(None),
    min_cost: Optional[float] = Query(None, ge=0)
):
    """
    Get individual run costs.

    Returns recent runs with their cost information.
    """
    query = """
        SELECT
            r.id as run_id,
            r.model_id,
            m.name as model_name,
            r.recipe_id,
            r.status,
            r.gpu_type,
            r.runtime_seconds,
            r.estimated_cost_usd,
            r.actual_cost_usd,
            r.started_at,
            r.finished_at
        FROM ml_run r
        LEFT JOIN ml_model m ON r.model_id = m.id
        WHERE 1=1
    """
    params = {}

    if model_id:
        query += " AND r.model_id = :model_id"
        params['model_id'] = model_id

    if provider:
        query += " AND r.compute_target = :provider"
        params['provider'] = provider

    if min_cost is not None:
        query += " AND COALESCE(r.actual_cost_usd, r.estimated_cost_usd, 0) >= :min_cost"
        params['min_cost'] = min_cost

    query += " ORDER BY r.started_at DESC NULLS LAST LIMIT :limit"
    params['limit'] = limit

    with engine.connect() as conn:
        result = conn.execute(text(query), params)
        runs = [dict(row._mapping) for row in result]

    return [
        RunCostResponse(
            run_id=r['run_id'],
            model_id=r['model_id'],
            model_name=r['model_name'],
            recipe_id=r['recipe_id'],
            status=r['status'],
            gpu_type=r['gpu_type'],
            runtime_seconds=r['runtime_seconds'],
            estimated_cost_usd=float(r['estimated_cost_usd']) if r['estimated_cost_usd'] else None,
            actual_cost_usd=float(r['actual_cost_usd']) if r['actual_cost_usd'] else None,
            started_at=r['started_at'],
            finished_at=r['finished_at']
        )
        for r in runs
    ]


# ========================================
# Budget Endpoints
# ========================================

@router.post("/budgets", response_model=BudgetResponse)
async def create_budget(request: BudgetCreate):
    """Create a new cost budget."""
    service = get_cost_analytics_service()

    budget_id = service.create_budget(
        name=request.name,
        budget_amount_usd=request.budget_amount_usd,
        period=request.period,
        alert_threshold_percent=request.alert_threshold_percent,
        scope_type=request.scope_type,
        scope_id=request.scope_id
    )

    return await get_budget(budget_id)


@router.get("/budgets", response_model=List[BudgetResponse])
async def list_budgets(
    is_active: Optional[bool] = Query(None)
):
    """List all budgets."""
    query = "SELECT * FROM cost_budgets WHERE 1=1"
    params = {}

    if is_active is not None:
        query += " AND is_active = :is_active"
        params['is_active'] = is_active

    query += " ORDER BY created_at DESC"

    with engine.connect() as conn:
        result = conn.execute(text(query), params)
        budgets = [dict(row._mapping) for row in result]

    return [
        BudgetResponse(
            id=str(b['id']),
            name=b['name'],
            budget_amount_usd=float(b['budget_amount_usd']),
            period=b['period'],
            alert_threshold_percent=b['alert_threshold_percent'],
            scope_type=b['scope_type'],
            scope_id=b['scope_id'],
            is_active=b['is_active'],
            created_at=b['created_at']
        )
        for b in budgets
    ]


@router.get("/budgets/{budget_id}", response_model=BudgetResponse)
async def get_budget(budget_id: str):
    """Get a specific budget."""
    query = "SELECT * FROM cost_budgets WHERE id = :budget_id"

    with engine.connect() as conn:
        result = conn.execute(text(query), {'budget_id': budget_id}).fetchone()

    if not result:
        raise HTTPException(status_code=404, detail="Budget not found")

    b = dict(result._mapping)
    return BudgetResponse(
        id=str(b['id']),
        name=b['name'],
        budget_amount_usd=float(b['budget_amount_usd']),
        period=b['period'],
        alert_threshold_percent=b['alert_threshold_percent'],
        scope_type=b['scope_type'],
        scope_id=b['scope_id'],
        is_active=b['is_active'],
        created_at=b['created_at']
    )


@router.get("/budgets/{budget_id}/status", response_model=BudgetStatusResponse)
async def get_budget_status(budget_id: str):
    """Get current status of a budget including spend and alerts."""
    service = get_cost_analytics_service()
    status = service.check_budget_status(budget_id)

    if not status:
        raise HTTPException(status_code=404, detail="Budget not found")

    return BudgetStatusResponse(
        budget_id=status.budget_id,
        budget_name=status.budget_name,
        budget_amount_usd=status.budget_amount_usd,
        current_spend_usd=status.current_spend_usd,
        percent_used=status.percent_used,
        remaining_usd=status.remaining_usd,
        is_exceeded=status.is_exceeded,
        alert_triggered=status.alert_triggered,
        period_start=status.period_start,
        period_end=status.period_end
    )


@router.delete("/budgets/{budget_id}", status_code=204)
async def delete_budget(budget_id: str):
    """Delete a budget."""
    query = "DELETE FROM cost_budgets WHERE id = :budget_id"

    with engine.begin() as conn:
        result = conn.execute(text(query), {'budget_id': budget_id})
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Budget not found")


@router.put("/budgets/{budget_id}/toggle")
async def toggle_budget(budget_id: str):
    """Toggle budget active/inactive status."""
    query = """
        UPDATE cost_budgets
        SET is_active = NOT is_active, updated_at = NOW()
        WHERE id = :budget_id
        RETURNING is_active
    """

    with engine.begin() as conn:
        result = conn.execute(text(query), {'budget_id': budget_id}).fetchone()
        if not result:
            raise HTTPException(status_code=404, detail="Budget not found")

    return {"is_active": result[0]}


# ========================================
# GPU Pricing Endpoints
# ========================================

@router.get("/gpu-pricing")
async def get_gpu_pricing(
    provider: Optional[str] = Query(None)
):
    """Get available GPU pricing options."""
    query = "SELECT * FROM gpu_pricing WHERE 1=1"
    params = {}

    if provider:
        query += " AND provider = :provider"
        params['provider'] = provider

    query += " ORDER BY price_per_hour_usd ASC"

    with engine.connect() as conn:
        result = conn.execute(text(query), params)
        pricing = [dict(row._mapping) for row in result]

    return [
        {
            'id': p['id'],
            'provider': p['provider'],
            'gpu_type': p['gpu_type'],
            'price_per_hour_usd': float(p['price_per_hour_usd']),
            'memory_gb': p['memory_gb'],
            'spot_available': p.get('spot_available', False),
            'spot_price_per_hour_usd': float(p['spot_price_per_hour_usd']) if p.get('spot_price_per_hour_usd') else None
        }
        for p in pricing
    ]
