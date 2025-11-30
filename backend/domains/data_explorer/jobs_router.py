"""
Data Analysis Jobs API router.

Provides async job management for data analysis tasks.
"""
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks, Depends
from typing import List, Optional
from sqlmodel import Session
from uuid import UUID
from pydantic import BaseModel, Field

from .job_models import AnalysisJob
from .job_service import AnalysisJobService
from .models import AnalysisResult
from .db_models import AIAnalysisResult
from db_session import get_session


router = APIRouter(prefix="/data-analysis", tags=["data-analysis"])


class JobCreate(BaseModel):
    """Create analysis job request."""
    name: str = Field(..., min_length=1, max_length=255)
    tables: List[dict] = Field(..., min_items=1, max_items=10)
    analysis_types: List[str]
    provider: str = "openai"
    model: str = "gpt-4-turbo-preview"
    db_id: str = "default"
    context: Optional[str] = None
    tags: List[str] = Field(default_factory=list)


class JobResponse(BaseModel):
    """Job status response."""
    id: str
    name: str
    description: Optional[str]
    status: str
    progress: int
    current_stage: Optional[str]
    tables: List[dict]
    analysis_types: List[str]
    provider: str
    model: str
    db_id: str
    created_at: str
    started_at: Optional[str]
    completed_at: Optional[str]
    cancelled_at: Optional[str]
    result_id: Optional[str]
    error_message: Optional[str]
    tags: List[str]


class JobWithResult(BaseModel):
    """Job with full analysis result."""
    job: JobResponse
    result: Optional[AnalysisResult] = None


@router.post("/jobs", response_model=JobResponse, status_code=202)
async def create_analysis_job(
    data: JobCreate,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session)
):
    """
    Create a new analysis job and start it in the background.
    
    Returns immediately with job ID and status 'pending'.
    The actual analysis runs asynchronously.
    
    Returns:
        202 Accepted with job details
    """
    try:
        # Create job
        job = AnalysisJobService.create_job(
            session=session,
            name=data.name,
            tables=data.tables,
            analysis_types=data.analysis_types,
            provider=data.provider,
            model=data.model,
            db_id=data.db_id,
            context=data.context,
            tags=data.tags
        )
        
        # Start background task
        background_tasks.add_task(
            AnalysisJobService.run_analysis_job,
            job.id,
            session
        )
        
        return JobResponse(
            id=str(job.id),
            name=job.name,
            description=job.description,
            status=job.status,
            progress=job.progress,
            current_stage=job.current_stage,
            tables=job.tables,
            analysis_types=job.analysis_types,
            provider=job.provider,
            model=job.model,
            db_id=job.db_id,
            created_at=job.created_at.isoformat(),
            started_at=None,
            completed_at=None,
            cancelled_at=None,
            result_id=None,
            error_message=None,
            tags=job.tags
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs", response_model=List[JobResponse])
async def list_jobs(
    db_id: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    session: Session = Depends(get_session)
):
    """
    List analysis jobs with optional filters.
    
    Args:
        db_id: Filter by database ID
        status: Filter by status (pending, running, completed, failed, cancelled)
        limit: Maximum number of results
        
    Returns:
        List of jobs
    """
    try:
        jobs = AnalysisJobService.list_jobs(
            session=session,
            db_id=db_id,
            status=status,
            limit=limit
        )
        
        return [
            JobResponse(
                id=str(job.id),
                name=job.name,
                description=job.description,
                status=job.status,
                progress=job.progress,
                current_stage=job.current_stage,
                tables=job.tables,
                analysis_types=job.analysis_types,
                provider=job.provider,
                model=job.model,
                db_id=job.db_id,
                created_at=job.created_at.isoformat(),
                started_at=job.started_at.isoformat() if job.started_at else None,
                completed_at=job.completed_at.isoformat() if job.completed_at else None,
                cancelled_at=job.cancelled_at.isoformat() if job.cancelled_at else None,
                result_id=str(job.result_id) if job.result_id else None,
                error_message=job.error_message,
                tags=job.tags or []
            )
            for job in jobs
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs/{job_id}", response_model=JobWithResult)
async def get_job(
    job_id: UUID,
    session: Session = Depends(get_session)
):
    """
    Get job details with full result if completed.
    
    Args:
        job_id: Job UUID
        
    Returns:
        Job with analysis result (if completed)
    """
    try:
        job = AnalysisJobService.get_job(session, job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        job_resp = JobResponse(
            id=str(job.id),
            name=job.name,
            description=job.description,
            status=job.status,
            progress=job.progress,
            current_stage=job.current_stage,
            tables=job.tables,
            analysis_types=job.analysis_types,
            provider=job.provider,
            model=job.model,
            db_id=job.db_id,
            created_at=job.created_at.isoformat(),
            started_at=job.started_at.isoformat() if job.started_at else None,
            completed_at=job.completed_at.isoformat() if job.completed_at else None,
            cancelled_at=job.cancelled_at.isoformat() if job.cancelled_at else None,
            result_id=str(job.result_id) if job.result_id else None,
            error_message=job.error_message,
            tags=job.tags or []
        )
        
        # Get result if completed
        result = None
        if job.result_id:
            analysis_result = session.get(AIAnalysisResult, job.result_id)
            if analysis_result:
                result = AnalysisResult(
                    analysis_id=str(analysis_result.id),
                    tables=analysis_result.tables,
                    analysis_types=analysis_result.analysis_types,
                    provider=analysis_result.provider,
                    model=analysis_result.model,
                    insights=analysis_result.insights,
                    summary=analysis_result.summary,
                    recommendations=analysis_result.recommendations or [],
                    metadata=analysis_result.execution_metadata or {},
                    created_at=analysis_result.created_at.isoformat()
                )
        
        return JobWithResult(job=job_resp, result=result)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/jobs/{job_id}/cancel")
async def cancel_job(
    job_id: UUID,
    session: Session = Depends(get_session)
):
    """
    Cancel a pending or running job.
    
    Args:
        job_id: Job UUID
        
    Returns:
        Success message
    """
    try:
        success = AnalysisJobService.cancel_job(session, job_id)
        if not success:
            raise HTTPException(
                status_code=400,
                detail="Job cannot be cancelled (not found or already completed)"
            )
        
        return {"success": True, "message": "Job cancelled successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/jobs/{job_id}")
async def delete_job(
    job_id: UUID,
    session: Session = Depends(get_session)
):
    """
    Delete a completed, failed, or cancelled job.
    
    Args:
        job_id: Job UUID
        
    Returns:
        Success message
    """
    try:
        success = AnalysisJobService.delete_job(session, job_id)
        if not success:
            raise HTTPException(
                status_code=400,
                detail="Job cannot be deleted (not found or still running)"
            )
        
        return {"success": True, "message": "Job deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs/{job_id}/status")
async def get_job_status(
    job_id: UUID,
    session: Session = Depends(get_session)
):
    """
    Get quick job status (lightweight endpoint for polling).
    
    Args:
        job_id: Job UUID
        
    Returns:
        Status, progress, and current stage
    """
    try:
        job = AnalysisJobService.get_job(session, job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        return {
            "id": str(job.id),
            "status": job.status,
            "progress": job.progress,
            "current_stage": job.current_stage,
            "result_id": str(job.result_id) if job.result_id else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

