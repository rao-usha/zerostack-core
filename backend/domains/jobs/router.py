"""Job API router."""
from fastapi import APIRouter, HTTPException
from typing import List, Optional
from uuid import UUID
from domains.jobs.models import Job, JobCreate, JobStatus, JobType
from domains.jobs.service import QueueInterface

router = APIRouter(prefix="/jobs", tags=["jobs"])

queue = QueueInterface()


@router.post("", response_model=Job, status_code=201)
async def create_job(job: JobCreate):
    """Create and enqueue a job."""
    raise HTTPException(status_code=501, detail="Not implemented")


@router.get("", response_model=List[Job])
async def list_jobs(
    job_type: Optional[JobType] = None,
    status: Optional[JobStatus] = None,
    limit: int = 100
):
    """List jobs."""
    raise HTTPException(status_code=501, detail="Not implemented")


@router.get("/{job_id}", response_model=Job)
async def get_job(job_id: UUID):
    """Get job status."""
    raise HTTPException(status_code=501, detail="Not implemented")


@router.post("/{job_id}/cancel")
async def cancel_job(job_id: UUID):
    """Cancel a job."""
    raise HTTPException(status_code=501, detail="Not implemented")


@router.post("/{job_id}/retry")
async def retry_job(job_id: UUID):
    """Retry a failed job."""
    raise HTTPException(status_code=501, detail="Not implemented")

