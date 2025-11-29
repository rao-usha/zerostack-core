"""Aggregator routes."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..db import get_db
from .. import models, schemas
from ..workers.jobs import enqueue_aggregate_job
import uuid


router = APIRouter(prefix="/v1/aggregate", tags=["aggregator"])


@router.post("/sample", status_code=202)
def sample_context(
    payload: schemas.AggregateSampleRequest,
    db: Session = Depends(get_db)
):
    """Enqueue a context generation/mutation job."""
    # Validate context if provided
    if payload.context_id:
        context = db.query(models.ContextDoc).filter(models.ContextDoc.id == payload.context_id).first()
        if not context:
            raise HTTPException(status_code=404, detail="ContextDoc not found")
    
    # Enqueue job
    job_id = f"agg-{uuid.uuid4().hex[:12]}"
    enqueue_aggregate_job(job_id, payload.model_dump())
    
    return {
        "job_id": job_id,
        "status": "queued",
        "message": "Aggregation job enqueued"
    }

