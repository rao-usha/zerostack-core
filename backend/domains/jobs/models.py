"""Job models."""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime
from enum import Enum


class JobStatus(str, Enum):
    """Job status."""
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


class JobType(str, Enum):
    """Job types."""
    DATA_IMPORT = "data_import"
    DATA_TRANSFORM = "data_transform"
    MODEL_TRAINING = "model_training"
    EVALUATION = "evaluation"
    SYNTHETIC_DATA_GENERATION = "synthetic_data_generation"
    REPORT_GENERATION = "report_generation"


class Job(BaseModel):
    """Job definition."""
    id: UUID
    job_type: JobType
    status: JobStatus = JobStatus.PENDING
    input: Dict[str, Any] = Field(default_factory=dict)
    output: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    progress: float = 0.0  # 0.0 to 1.0
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_by: Optional[UUID] = None
    
    class Config:
        from_attributes = True


class JobCreate(BaseModel):
    """Request to create a job."""
    job_type: JobType
    input: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    priority: int = 0  # Higher priority = executed first


class JobUpdate(BaseModel):
    """Job update."""
    status: Optional[JobStatus] = None
    progress: Optional[float] = None
    output: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

