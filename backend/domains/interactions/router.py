"""Interaction Logs API router."""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel
from sqlalchemy import create_engine, select

from core.config import settings
from db.models import interaction_logs

router = APIRouter(prefix="/interactions", tags=["interactions"])

# Initialize engine
engine = create_engine(settings.database_url)


# ========================================
# Pydantic Models
# ========================================

class InteractionLogResponse(BaseModel):
    """Response for a single interaction log entry."""
    id: str
    chat_session_id: Optional[str]
    actor: str
    event_type: str
    message: Optional[str]
    refs: dict
    metadata: dict
    created_at: datetime

    class Config:
        from_attributes = True


class InteractionLogListResponse(BaseModel):
    """Response for listing interaction logs."""
    interactions: List[InteractionLogResponse]
    total: int


# ========================================
# Endpoints
# ========================================

@router.get("", response_model=InteractionLogListResponse)
async def list_interactions(
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    actor: Optional[str] = Query(None, description="Filter by actor (user, assistant, system)"),
    run_id: Optional[str] = Query(None, description="Filter by run_id in refs"),
    asset_id: Optional[str] = Query(None, description="Filter by asset_id in refs"),
    dataset_id: Optional[str] = Query(None, description="Filter by dataset_id in refs"),
    limit: int = Query(100, le=500),
    offset: int = Query(0, ge=0)
):
    """
    List interaction logs with optional filters.
    
    Returns the audit trail of chat messages and ML operations.
    """
    query = select(interaction_logs)
    
    if event_type:
        query = query.where(interaction_logs.c.event_type == event_type)
    if actor:
        query = query.where(interaction_logs.c.actor == actor)
    if run_id:
        query = query.where(interaction_logs.c.refs['run_id'].astext == run_id)
    if asset_id:
        query = query.where(interaction_logs.c.refs['asset_id'].astext == asset_id)
    if dataset_id:
        query = query.where(interaction_logs.c.refs['dataset_id'].astext == dataset_id)
    
    query = query.order_by(interaction_logs.c.created_at.desc()).offset(offset).limit(limit)
    
    with engine.connect() as conn:
        results = conn.execute(query).fetchall()
        
        # Get total count (simplified)
        count_query = select(interaction_logs.c.id)
        if event_type:
            count_query = count_query.where(interaction_logs.c.event_type == event_type)
        if actor:
            count_query = count_query.where(interaction_logs.c.actor == actor)
        total = len(conn.execute(count_query).fetchall())
    
    interactions = [
        InteractionLogResponse(
            id=str(r.id),
            chat_session_id=r.chat_session_id,
            actor=r.actor,
            event_type=r.event_type,
            message=r.message,
            refs=r.refs or {},
            metadata=r.metadata or {},
            created_at=r.created_at
        )
        for r in results
    ]
    
    return InteractionLogListResponse(interactions=interactions, total=total)


@router.get("/session/{chat_session_id}", response_model=InteractionLogListResponse)
async def get_session_history(
    chat_session_id: str,
    limit: int = Query(100, le=500)
):
    """
    Get all interactions for a specific chat session.
    
    Returns the full history linking chat messages to runs and assets.
    """
    query = (
        select(interaction_logs)
        .where(interaction_logs.c.chat_session_id == chat_session_id)
        .order_by(interaction_logs.c.created_at.asc())
        .limit(limit)
    )
    
    with engine.connect() as conn:
        results = conn.execute(query).fetchall()
    
    interactions = [
        InteractionLogResponse(
            id=str(r.id),
            chat_session_id=r.chat_session_id,
            actor=r.actor,
            event_type=r.event_type,
            message=r.message,
            refs=r.refs or {},
            metadata=r.metadata or {},
            created_at=r.created_at
        )
        for r in results
    ]
    
    return InteractionLogListResponse(interactions=interactions, total=len(interactions))


@router.get("/run/{run_id}", response_model=InteractionLogListResponse)
async def get_run_history(run_id: str):
    """
    Get all interactions related to a specific ML run.
    
    Returns events from submission through completion/banking.
    """
    query = (
        select(interaction_logs)
        .where(interaction_logs.c.refs['run_id'].astext == run_id)
        .order_by(interaction_logs.c.created_at.asc())
    )
    
    with engine.connect() as conn:
        results = conn.execute(query).fetchall()
    
    interactions = [
        InteractionLogResponse(
            id=str(r.id),
            chat_session_id=r.chat_session_id,
            actor=r.actor,
            event_type=r.event_type,
            message=r.message,
            refs=r.refs or {},
            metadata=r.metadata or {},
            created_at=r.created_at
        )
        for r in results
    ]
    
    return InteractionLogListResponse(interactions=interactions, total=len(interactions))


@router.get("/event-types")
async def list_event_types():
    """List all possible event types for filtering."""
    return {
        "event_types": [
            {"type": "CHAT_MESSAGE", "description": "User or assistant chat message"},
            {"type": "DATASET_RESOLVE", "description": "Dataset availability check"},
            {"type": "INGEST_START", "description": "Dataset ingestion started"},
            {"type": "INGEST_COMPLETE", "description": "Dataset ingestion completed"},
            {"type": "RUN_SUBMITTED", "description": "ML run submitted"},
            {"type": "RUN_STARTED", "description": "ML run started executing"},
            {"type": "RUN_COMPLETED", "description": "ML run completed successfully"},
            {"type": "RUN_FAILED", "description": "ML run failed"},
            {"type": "RUN_CANCELLED", "description": "ML run was cancelled"},
            {"type": "ASSET_CREATED", "description": "Derived asset created"},
            {"type": "ASSET_PROMOTED", "description": "Asset promoted to permanent"},
            {"type": "ASSET_DELETED", "description": "Asset deleted"},
            {"type": "VIEW_STATUS", "description": "User viewed run status"},
            {"type": "VIEW_LOGS", "description": "User viewed run logs"},
        ]
    }
