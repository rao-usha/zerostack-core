"""Abstract compute adapter interface."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum
from datetime import datetime


class JobState(str, Enum):
    """Possible states for a compute job."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    UNKNOWN = "unknown"


@dataclass
class JobStatus:
    """Status of a compute job."""
    state: JobState
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    exit_code: Optional[int] = None
    reason: Optional[str] = None
    progress: Optional[float] = None  # 0.0 to 1.0


@dataclass
class JobSubmission:
    """Job submission request."""
    run_id: str
    image: str
    command: list[str]
    env: dict[str, str]
    input_uri: str
    output_uri: str
    gpu_count: int = 1
    cpu_limit: Optional[str] = None  # e.g., "2000m"
    memory_limit: Optional[str] = None  # e.g., "4Gi"
    timeout_seconds: int = 3600
    working_dir: Optional[str] = None
    labels: dict[str, str] = field(default_factory=dict)


class ComputeAdapter(ABC):
    """
    Abstract base class for compute backends.
    
    Implementations:
    - LocalComputeAdapter: Run containers locally (dev)
    - SSHComputeAdapter: Run containers on remote GPU VM via SSH
    - K8sGatewayAdapter: Submit jobs to Kubernetes cluster
    """
    
    @property
    @abstractmethod
    def adapter_type(self) -> str:
        """Return the adapter type identifier."""
        pass
    
    @abstractmethod
    async def submit(self, job: JobSubmission) -> str:
        """
        Submit a job for execution.
        
        Args:
            job: Job submission details
            
        Returns:
            Remote job ID for tracking
            
        Raises:
            ComputeError: If submission fails
        """
        pass
    
    @abstractmethod
    async def get_status(self, remote_job_id: str) -> JobStatus:
        """
        Get the current status of a job.
        
        Args:
            remote_job_id: ID returned from submit()
            
        Returns:
            Current job status
        """
        pass
    
    @abstractmethod
    async def get_logs(self, remote_job_id: str, tail: Optional[int] = None) -> str:
        """
        Fetch job logs.
        
        Args:
            remote_job_id: ID returned from submit()
            tail: Optional number of lines from end
            
        Returns:
            Log content as string
        """
        pass
    
    @abstractmethod
    async def cancel(self, remote_job_id: str) -> bool:
        """
        Cancel a running job.
        
        Args:
            remote_job_id: ID returned from submit()
            
        Returns:
            True if cancelled successfully
        """
        pass
    
    async def is_healthy(self) -> bool:
        """
        Check if the compute backend is healthy/reachable.
        
        Returns:
            True if healthy
        """
        return True


class ComputeError(Exception):
    """Exception raised by compute operations."""
    
    def __init__(self, message: str, job_id: Optional[str] = None, cause: Optional[Exception] = None):
        super().__init__(message)
        self.job_id = job_id
        self.cause = cause
