"""Job service - queue interface."""
from typing import List, Optional
from uuid import UUID
from .models import Job, JobCreate, JobUpdate, JobStatus, JobType


class QueueInterface:
    """Abstract queue interface for async job processing."""
    
    def enqueue(self, job: JobCreate, created_by: Optional[UUID] = None) -> Job:
        """
        Enqueue a job.
        
        TODO: Implement job queuing with:
        - Priority handling
        - Queue backend integration (Redis, RabbitMQ, etc.)
        - Job persistence
        """
        raise NotImplementedError("TODO: Implement job queuing")
    
    def get_job(self, job_id: UUID) -> Optional[Job]:
        """Get job status."""
        raise NotImplementedError("TODO: Implement job retrieval")
    
    def update_job(self, job_id: UUID, update: JobUpdate) -> Job:
        """Update job status/progress."""
        raise NotImplementedError("TODO: Implement job update")
    
    def list_jobs(
        self,
        job_type: Optional[JobType] = None,
        status: Optional[JobStatus] = None,
        limit: int = 100
    ) -> List[Job]:
        """List jobs."""
        raise NotImplementedError("TODO: Implement job listing")
    
    def cancel_job(self, job_id: UUID) -> bool:
        """Cancel a job."""
        raise NotImplementedError("TODO: Implement job cancellation")
    
    def retry_job(self, job_id: UUID) -> Job:
        """Retry a failed job."""
        raise NotImplementedError("TODO: Implement job retry")


class JobWorker:
    """Job worker interface."""
    
    def process_job(self, job: Job) -> None:
        """
        Process a job.
        
        TODO: Implement job processing logic.
        This should be implemented per job type.
        """
        raise NotImplementedError("TODO: Implement job processing")

