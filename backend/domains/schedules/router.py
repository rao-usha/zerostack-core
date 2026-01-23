"""Schedules API router for managing recurring ML runs."""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from sqlalchemy import create_engine, text

from core.config import settings
from services.scheduler import get_scheduler

router = APIRouter(prefix="/schedules", tags=["schedules"])
engine = create_engine(settings.database_url)


# ========================================
# Pydantic Models
# ========================================

class ScheduleCreate(BaseModel):
    """Request to create a schedule."""
    name: str
    recipe_id: str
    cron_expression: str
    dataset_id: Optional[str] = None
    parameters: dict = {}
    timezone: str = "UTC"
    use_reuse_engine: bool = True
    notify_on_failure: bool = True
    notify_on_success: bool = False
    notification_channels: List[str] = []


class ScheduleUpdate(BaseModel):
    """Request to update a schedule."""
    name: Optional[str] = None
    cron_expression: Optional[str] = None
    parameters: Optional[dict] = None
    timezone: Optional[str] = None
    use_reuse_engine: Optional[bool] = None
    notify_on_failure: Optional[bool] = None
    notify_on_success: Optional[bool] = None
    notification_channels: Optional[List[str]] = None


class ScheduleResponse(BaseModel):
    """Response for a schedule."""
    id: str
    name: str
    recipe_id: str
    dataset_id: Optional[str]
    cron_expression: str
    timezone: str
    parameters: dict
    is_active: bool
    use_reuse_engine: bool
    notify_on_failure: bool
    notify_on_success: bool
    notification_channels: List[str]
    last_run_id: Optional[str]
    last_run_at: Optional[datetime]
    next_run_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ========================================
# Schedule CRUD Endpoints
# ========================================

@router.post("", response_model=ScheduleResponse)
async def create_schedule(request: ScheduleCreate):
    """
    Create a new schedule for recurring ML runs.
    
    Cron expression format: minute hour day month day_of_week
    Examples:
    - "0 9 * * 1" = Every Monday at 9:00 AM
    - "0 0 1 * *" = First day of every month at midnight
    - "*/15 * * * *" = Every 15 minutes
    """
    scheduler = get_scheduler()
    
    # Validate cron expression
    parts = request.cron_expression.split()
    if len(parts) != 5:
        raise HTTPException(
            status_code=400,
            detail="Invalid cron expression. Format: 'minute hour day month day_of_week'"
        )
    
    schedule_id = await scheduler.create_schedule(
        name=request.name,
        recipe_id=request.recipe_id,
        cron_expression=request.cron_expression,
        dataset_id=request.dataset_id,
        parameters=request.parameters,
        timezone=request.timezone,
        use_reuse_engine=request.use_reuse_engine,
        notify_on_failure=request.notify_on_failure,
        notify_on_success=request.notify_on_success,
        notification_channels=request.notification_channels
    )
    
    return await get_schedule(schedule_id)


@router.get("", response_model=List[ScheduleResponse])
async def list_schedules(
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    recipe_id: Optional[str] = Query(None, description="Filter by recipe ID"),
    limit: int = Query(100, le=500)
):
    """List all schedules with optional filters."""
    query = "SELECT * FROM run_schedules WHERE 1=1"
    params = {}
    
    if is_active is not None:
        query += " AND is_active = :is_active"
        params['is_active'] = is_active
    
    if recipe_id:
        query += " AND recipe_id = :recipe_id"
        params['recipe_id'] = recipe_id
    
    query += " ORDER BY created_at DESC LIMIT :limit"
    params['limit'] = limit
    
    with engine.connect() as conn:
        result = conn.execute(text(query), params)
        schedules = [dict(row._mapping) for row in result]
    
    return [_schedule_to_response(s) for s in schedules]


@router.get("/{schedule_id}", response_model=ScheduleResponse)
async def get_schedule(schedule_id: str):
    """Get a specific schedule."""
    query = "SELECT * FROM run_schedules WHERE id = :id"
    
    with engine.connect() as conn:
        result = conn.execute(text(query), {'id': schedule_id}).fetchone()
    
    if not result:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    return _schedule_to_response(dict(result._mapping))


@router.put("/{schedule_id}", response_model=ScheduleResponse)
async def update_schedule(schedule_id: str, request: ScheduleUpdate):
    """Update a schedule configuration."""
    import json
    
    updates = []
    params = {'schedule_id': schedule_id}
    
    if request.name is not None:
        updates.append("name = :name")
        params['name'] = request.name
    
    if request.cron_expression is not None:
        # Validate cron expression
        parts = request.cron_expression.split()
        if len(parts) != 5:
            raise HTTPException(status_code=400, detail="Invalid cron expression")
        updates.append("cron_expression = :cron")
        params['cron'] = request.cron_expression
    
    if request.parameters is not None:
        updates.append("parameters = :parameters")
        params['parameters'] = json.dumps(request.parameters)
    
    if request.timezone is not None:
        updates.append("timezone = :timezone")
        params['timezone'] = request.timezone
    
    if request.use_reuse_engine is not None:
        updates.append("use_reuse_engine = :use_reuse")
        params['use_reuse'] = request.use_reuse_engine
    
    if request.notify_on_failure is not None:
        updates.append("notify_on_failure = :notify_fail")
        params['notify_fail'] = request.notify_on_failure
    
    if request.notify_on_success is not None:
        updates.append("notify_on_success = :notify_success")
        params['notify_success'] = request.notify_on_success
    
    if request.notification_channels is not None:
        updates.append("notification_channels = :channels")
        params['channels'] = json.dumps(request.notification_channels)
    
    if not updates:
        raise HTTPException(status_code=400, detail="No updates provided")
    
    updates.append("updated_at = NOW()")
    query = f"UPDATE run_schedules SET {', '.join(updates)} WHERE id = :schedule_id"
    
    with engine.begin() as conn:
        result = conn.execute(text(query), params)
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Schedule not found")
    
    return await get_schedule(schedule_id)


@router.delete("/{schedule_id}", status_code=204)
async def delete_schedule(schedule_id: str):
    """Delete a schedule."""
    scheduler = get_scheduler()
    await scheduler.pause_schedule(schedule_id)  # Remove from active scheduler
    
    query = "DELETE FROM run_schedules WHERE id = :id"
    
    with engine.begin() as conn:
        result = conn.execute(text(query), {'id': schedule_id})
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Schedule not found")


# ========================================
# Schedule Control Endpoints
# ========================================

@router.post("/{schedule_id}/pause", response_model=ScheduleResponse)
async def pause_schedule(schedule_id: str):
    """Pause a schedule (stop it from running)."""
    scheduler = get_scheduler()
    await scheduler.pause_schedule(schedule_id)
    
    return await get_schedule(schedule_id)


@router.post("/{schedule_id}/resume", response_model=ScheduleResponse)
async def resume_schedule(schedule_id: str):
    """Resume a paused schedule."""
    scheduler = get_scheduler()
    await scheduler.resume_schedule(schedule_id)
    
    return await get_schedule(schedule_id)


@router.post("/{schedule_id}/trigger")
async def trigger_schedule(schedule_id: str):
    """
    Manually trigger a schedule now.
    
    This runs the schedule immediately, regardless of its cron expression.
    """
    scheduler = get_scheduler()
    run_id = await scheduler.trigger_now(schedule_id)
    
    if run_id:
        return {
            "message": "Schedule triggered successfully",
            "schedule_id": schedule_id,
            "run_id": run_id
        }
    else:
        return {
            "message": "Schedule triggered (may have reused existing run)",
            "schedule_id": schedule_id
        }


# ========================================
# Schedule History Endpoints
# ========================================

@router.get("/{schedule_id}/history")
async def get_schedule_history(
    schedule_id: str,
    limit: int = Query(20, le=100)
):
    """
    Get run history for a schedule.
    
    Shows recent runs triggered by this schedule.
    """
    # First verify schedule exists
    schedule = await get_schedule(schedule_id)
    
    # Get runs associated with this schedule (by recipe_id and run_type)
    query = """
        SELECT id, status, started_at, finished_at, metrics_json, 
               actual_cost_usd, runtime_seconds
        FROM ml_run 
        WHERE recipe_id = :recipe_id 
          AND run_type = 'scheduled'
        ORDER BY created_at DESC
        LIMIT :limit
    """
    
    with engine.connect() as conn:
        result = conn.execute(text(query), {
            'recipe_id': schedule.recipe_id,
            'limit': limit
        })
        runs = [dict(row._mapping) for row in result]
    
    return {
        'schedule_id': schedule_id,
        'schedule_name': schedule.name,
        'total_runs': len(runs),
        'runs': [
            {
                'run_id': r['id'],
                'status': r['status'],
                'started_at': r['started_at'].isoformat() if r['started_at'] else None,
                'finished_at': r['finished_at'].isoformat() if r['finished_at'] else None,
                'metrics': r.get('metrics_json') or {},
                'cost_usd': float(r['actual_cost_usd']) if r.get('actual_cost_usd') else None,
                'runtime_seconds': r.get('runtime_seconds')
            }
            for r in runs
        ]
    }


# ========================================
# Helper Functions
# ========================================

def _schedule_to_response(s: dict) -> ScheduleResponse:
    """Convert database row to response model."""
    import json
    
    # Parse JSON fields
    parameters = s.get('parameters')
    if isinstance(parameters, str):
        parameters = json.loads(parameters)
    elif parameters is None:
        parameters = {}
    
    channels = s.get('notification_channels')
    if isinstance(channels, str):
        channels = json.loads(channels)
    elif channels is None:
        channels = []
    
    return ScheduleResponse(
        id=str(s['id']),
        name=s['name'],
        recipe_id=s['recipe_id'],
        dataset_id=s.get('dataset_id'),
        cron_expression=s['cron_expression'],
        timezone=s.get('timezone', 'UTC'),
        parameters=parameters,
        is_active=s['is_active'],
        use_reuse_engine=s.get('use_reuse_engine', True),
        notify_on_failure=s.get('notify_on_failure', True),
        notify_on_success=s.get('notify_on_success', False),
        notification_channels=channels,
        last_run_id=s.get('last_run_id'),
        last_run_at=s.get('last_run_at'),
        next_run_at=s.get('next_run_at'),
        created_at=s['created_at'],
        updated_at=s.get('updated_at') or s['created_at']
    )
