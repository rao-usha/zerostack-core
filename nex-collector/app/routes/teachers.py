"""Teacher routes."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..db import get_db
from .. import models, schemas
from ..workers.jobs import enqueue_teacher_run_job


router = APIRouter(prefix="/v1/teachers", tags=["teachers"])


@router.post("/runs", status_code=202)
def enqueue_teacher_run(
    payload: schemas.TeacherRunCreate,
    db: Session = Depends(get_db)
):
    """Enqueue a teacher run to label an example."""
    # Validate example exists
    example = db.query(models.SyntheticExample).filter(
        models.SyntheticExample.id == payload.example_id
    ).first()
    if not example:
        raise HTTPException(status_code=404, detail="Example not found")
    
    # Check if run exists
    existing = db.query(models.TeacherRun).filter(models.TeacherRun.id == payload.id).first()
    if existing:
        return {"run_id": payload.id, "status": "exists"}
    
    # Create run
    run = models.TeacherRun(
        id=payload.id,
        example_id=payload.example_id,
        provider=payload.provider,
        model=payload.model,
        params_json=payload.params_json
    )
    db.add(run)
    db.commit()
    
    # Enqueue job
    enqueue_teacher_run_job(payload.id)
    
    return {"run_id": run.id, "status": "queued"}


@router.get("/runs/{run_id}", response_model=schemas.TeacherRunResponse)
def get_run(
    run_id: str,
    db: Session = Depends(get_db)
):
    """Get a TeacherRun by ID."""
    run = db.query(models.TeacherRun).filter(models.TeacherRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return run
