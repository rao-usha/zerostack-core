"""Drift Detection API router."""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from sqlalchemy import create_engine, text

from core.config import settings
from services.drift_detector import (
    get_drift_detector, 
    ComparisonType, 
    Severity,
    DriftCheckResult
)

router = APIRouter(prefix="/drift", tags=["drift-detection"])
engine = create_engine(settings.database_url)


# ========================================
# Pydantic Models
# ========================================

class DriftCheckCreate(BaseModel):
    """Request to create a drift check."""
    name: str
    metric: str
    threshold: float
    comparison: str = "percentage_both"  # absolute, percentage_increase, percentage_decrease, percentage_both
    recipe_id: Optional[str] = None
    asset_id: Optional[str] = None
    description: Optional[str] = None
    check_frequency: str = "on_run"  # on_run, hourly, daily


class DriftCheckUpdate(BaseModel):
    """Request to update a drift check."""
    name: Optional[str] = None
    threshold: Optional[float] = None
    comparison: Optional[str] = None
    is_active: Optional[bool] = None
    baseline_value: Optional[float] = None
    description: Optional[str] = None


class DriftCheckResponse(BaseModel):
    """Response for a drift check."""
    id: str
    name: str
    description: Optional[str]
    metric: str
    threshold: float
    comparison: str
    recipe_id: Optional[str]
    asset_id: Optional[str]
    baseline_value: Optional[float]
    latest_value: Optional[float]
    is_breached: bool
    is_active: bool
    check_frequency: str
    last_checked_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class DriftAlertResponse(BaseModel):
    """Response for a drift alert."""
    id: str
    drift_check_id: str
    run_id: Optional[str]
    severity: str
    baseline_value: Optional[float]
    current_value: Optional[float]
    change_percent: Optional[float]
    message: Optional[str]
    acknowledged: bool
    acknowledged_at: Optional[datetime]
    acknowledged_by: Optional[str]
    triggered_at: datetime

    class Config:
        from_attributes = True


class CheckMetricsRequest(BaseModel):
    """Request to check metrics for drift."""
    run_id: str
    metrics: dict  # metric_name -> value


class AcknowledgeAlertRequest(BaseModel):
    """Request to acknowledge an alert."""
    acknowledged_by: Optional[str] = None


# ========================================
# Drift Check Endpoints
# ========================================

@router.post("/checks", response_model=DriftCheckResponse)
async def create_drift_check(request: DriftCheckCreate):
    """
    Create a new drift check.
    
    Configure monitoring for a specific metric to alert when it drifts
    beyond the specified threshold.
    """
    detector = get_drift_detector()
    
    try:
        comparison_type = ComparisonType(request.comparison)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid comparison type. Must be one of: {[c.value for c in ComparisonType]}"
        )
    
    check_id = detector.create_check(
        name=request.name,
        metric=request.metric,
        threshold=request.threshold,
        comparison=comparison_type,
        recipe_id=request.recipe_id,
        asset_id=request.asset_id,
        description=request.description,
        check_frequency=request.check_frequency
    )
    
    # Fetch and return the created check
    return await get_drift_check(check_id)


@router.get("/checks", response_model=List[DriftCheckResponse])
async def list_drift_checks(
    recipe_id: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    is_breached: Optional[bool] = Query(None),
    limit: int = Query(100, le=500)
):
    """List all drift checks with optional filters."""
    query = "SELECT * FROM drift_checks WHERE 1=1"
    params = {}
    
    if recipe_id:
        query += " AND recipe_id = :recipe_id"
        params['recipe_id'] = recipe_id
    
    if is_active is not None:
        query += " AND is_active = :is_active"
        params['is_active'] = is_active
    
    if is_breached is not None:
        query += " AND is_breached = :is_breached"
        params['is_breached'] = is_breached
    
    query += " ORDER BY created_at DESC LIMIT :limit"
    params['limit'] = limit
    
    with engine.connect() as conn:
        result = conn.execute(text(query), params)
        checks = [dict(row._mapping) for row in result]
    
    return [
        DriftCheckResponse(
            id=str(c['id']),
            name=c['name'],
            description=c.get('description'),
            metric=c['metric'],
            threshold=float(c['threshold']),
            comparison=c['comparison'],
            recipe_id=c.get('recipe_id'),
            asset_id=str(c['asset_id']) if c.get('asset_id') else None,
            baseline_value=float(c['baseline_value']) if c.get('baseline_value') else None,
            latest_value=float(c['latest_value']) if c.get('latest_value') else None,
            is_breached=c['is_breached'],
            is_active=c['is_active'],
            check_frequency=c.get('check_frequency', 'on_run'),
            last_checked_at=c.get('last_checked_at'),
            created_at=c['created_at']
        )
        for c in checks
    ]


@router.get("/checks/{check_id}", response_model=DriftCheckResponse)
async def get_drift_check(check_id: str):
    """Get a specific drift check."""
    query = "SELECT * FROM drift_checks WHERE id = :check_id"
    
    with engine.connect() as conn:
        result = conn.execute(text(query), {'check_id': check_id}).fetchone()
    
    if not result:
        raise HTTPException(status_code=404, detail="Drift check not found")
    
    c = dict(result._mapping)
    return DriftCheckResponse(
        id=str(c['id']),
        name=c['name'],
        description=c.get('description'),
        metric=c['metric'],
        threshold=float(c['threshold']),
        comparison=c['comparison'],
        recipe_id=c.get('recipe_id'),
        asset_id=str(c['asset_id']) if c.get('asset_id') else None,
        baseline_value=float(c['baseline_value']) if c.get('baseline_value') else None,
        latest_value=float(c['latest_value']) if c.get('latest_value') else None,
        is_breached=c['is_breached'],
        is_active=c['is_active'],
        check_frequency=c.get('check_frequency', 'on_run'),
        last_checked_at=c.get('last_checked_at'),
        created_at=c['created_at']
    )


@router.put("/checks/{check_id}", response_model=DriftCheckResponse)
async def update_drift_check(check_id: str, request: DriftCheckUpdate):
    """Update a drift check configuration."""
    updates = []
    params = {'check_id': check_id}
    
    if request.name is not None:
        updates.append("name = :name")
        params['name'] = request.name
    
    if request.threshold is not None:
        updates.append("threshold = :threshold")
        params['threshold'] = request.threshold
    
    if request.comparison is not None:
        updates.append("comparison = :comparison")
        params['comparison'] = request.comparison
    
    if request.is_active is not None:
        updates.append("is_active = :is_active")
        params['is_active'] = request.is_active
    
    if request.baseline_value is not None:
        updates.append("baseline_value = :baseline_value")
        params['baseline_value'] = request.baseline_value
    
    if request.description is not None:
        updates.append("description = :description")
        params['description'] = request.description
    
    if not updates:
        raise HTTPException(status_code=400, detail="No updates provided")
    
    updates.append("updated_at = NOW()")
    query = f"UPDATE drift_checks SET {', '.join(updates)} WHERE id = :check_id"
    
    with engine.begin() as conn:
        result = conn.execute(text(query), params)
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Drift check not found")
    
    return await get_drift_check(check_id)


@router.delete("/checks/{check_id}", status_code=204)
async def delete_drift_check(check_id: str):
    """Delete a drift check and its alerts."""
    query = "DELETE FROM drift_checks WHERE id = :check_id"
    
    with engine.begin() as conn:
        result = conn.execute(text(query), {'check_id': check_id})
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Drift check not found")


# ========================================
# Drift Check Execution
# ========================================

@router.post("/checks/{check_id}/evaluate")
async def evaluate_drift_check(check_id: str, current_value: float = Query(...)):
    """
    Manually evaluate a drift check with a given value.
    
    Useful for testing or ad-hoc drift detection.
    """
    detector = get_drift_detector()
    result = detector.check_drift(check_id, current_value)
    
    return result.to_dict()


@router.post("/evaluate-run")
async def evaluate_run_metrics(request: CheckMetricsRequest):
    """
    Evaluate all configured drift checks against a run's metrics.
    
    This is called automatically when a run completes, but can also
    be called manually.
    """
    detector = get_drift_detector()
    results = detector.check_run_metrics(request.run_id, request.metrics)
    
    return {
        'run_id': request.run_id,
        'checks_evaluated': len(results),
        'breaches': [r.to_dict() for r in results if r.is_breached],
        'all_results': [r.to_dict() for r in results]
    }


# ========================================
# Alert Endpoints
# ========================================

@router.get("/alerts", response_model=List[DriftAlertResponse])
async def list_drift_alerts(
    check_id: Optional[str] = Query(None),
    unacknowledged_only: bool = Query(False),
    severity: Optional[str] = Query(None),
    limit: int = Query(100, le=500)
):
    """List drift alerts with optional filters."""
    query = "SELECT * FROM drift_alerts WHERE 1=1"
    params = {}
    
    if check_id:
        query += " AND drift_check_id = :check_id"
        params['check_id'] = check_id
    
    if unacknowledged_only:
        query += " AND acknowledged = false"
    
    if severity:
        query += " AND severity = :severity"
        params['severity'] = severity
    
    query += " ORDER BY triggered_at DESC LIMIT :limit"
    params['limit'] = limit
    
    with engine.connect() as conn:
        result = conn.execute(text(query), params)
        alerts = [dict(row._mapping) for row in result]
    
    return [
        DriftAlertResponse(
            id=str(a['id']),
            drift_check_id=str(a['drift_check_id']),
            run_id=a.get('run_id'),
            severity=a['severity'],
            baseline_value=float(a['baseline_value']) if a.get('baseline_value') else None,
            current_value=float(a['current_value']) if a.get('current_value') else None,
            change_percent=float(a['change_percent']) if a.get('change_percent') else None,
            message=a.get('message'),
            acknowledged=a['acknowledged'],
            acknowledged_at=a.get('acknowledged_at'),
            acknowledged_by=a.get('acknowledged_by'),
            triggered_at=a['triggered_at']
        )
        for a in alerts
    ]


@router.get("/alerts/{alert_id}", response_model=DriftAlertResponse)
async def get_drift_alert(alert_id: str):
    """Get a specific drift alert."""
    query = "SELECT * FROM drift_alerts WHERE id = :alert_id"
    
    with engine.connect() as conn:
        result = conn.execute(text(query), {'alert_id': alert_id}).fetchone()
    
    if not result:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    a = dict(result._mapping)
    return DriftAlertResponse(
        id=str(a['id']),
        drift_check_id=str(a['drift_check_id']),
        run_id=a.get('run_id'),
        severity=a['severity'],
        baseline_value=float(a['baseline_value']) if a.get('baseline_value') else None,
        current_value=float(a['current_value']) if a.get('current_value') else None,
        change_percent=float(a['change_percent']) if a.get('change_percent') else None,
        message=a.get('message'),
        acknowledged=a['acknowledged'],
        acknowledged_at=a.get('acknowledged_at'),
        acknowledged_by=a.get('acknowledged_by'),
        triggered_at=a['triggered_at']
    )


@router.post("/alerts/{alert_id}/acknowledge", response_model=DriftAlertResponse)
async def acknowledge_drift_alert(alert_id: str, request: AcknowledgeAlertRequest = AcknowledgeAlertRequest()):
    """Acknowledge a drift alert."""
    detector = get_drift_detector()
    detector.acknowledge_alert(alert_id, request.acknowledged_by)
    
    return await get_drift_alert(alert_id)


@router.post("/alerts/acknowledge-all")
async def acknowledge_all_alerts(
    check_id: Optional[str] = Query(None),
    acknowledged_by: Optional[str] = Query(None)
):
    """Acknowledge all unacknowledged alerts."""
    query = """
        UPDATE drift_alerts 
        SET acknowledged = true, 
            acknowledged_at = NOW(),
            acknowledged_by = :acknowledged_by
        WHERE acknowledged = false
    """
    params = {'acknowledged_by': acknowledged_by}
    
    if check_id:
        query += " AND drift_check_id = :check_id"
        params['check_id'] = check_id
    
    with engine.begin() as conn:
        result = conn.execute(text(query), params)
    
    return {
        'acknowledged_count': result.rowcount,
        'message': f"Acknowledged {result.rowcount} alert(s)"
    }


# ========================================
# Summary Endpoints
# ========================================

@router.get("/summary")
async def get_drift_summary():
    """Get a summary of drift detection status."""
    queries = {
        'total_checks': "SELECT COUNT(*) FROM drift_checks",
        'active_checks': "SELECT COUNT(*) FROM drift_checks WHERE is_active = true",
        'breached_checks': "SELECT COUNT(*) FROM drift_checks WHERE is_breached = true AND is_active = true",
        'total_alerts': "SELECT COUNT(*) FROM drift_alerts",
        'unacknowledged_alerts': "SELECT COUNT(*) FROM drift_alerts WHERE acknowledged = false",
        'critical_alerts': "SELECT COUNT(*) FROM drift_alerts WHERE severity = 'critical' AND acknowledged = false",
    }
    
    results = {}
    with engine.connect() as conn:
        for key, query in queries.items():
            result = conn.execute(text(query)).fetchone()
            results[key] = result[0]
    
    return results
