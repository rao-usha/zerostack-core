"""Dataset models."""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime
from enum import Enum


class DatasetStatus(str, Enum):
    """Dataset status."""
    ACTIVE = "active"
    PROCESSING = "processing"
    ERROR = "error"
    ARCHIVED = "archived"


class Dataset(BaseModel):
    """Dataset definition."""
    id: UUID
    name: str
    description: Optional[str] = None
    status: DatasetStatus = DatasetStatus.ACTIVE
    source_connector_id: Optional[UUID] = None
    schema: Dict[str, Any] = Field(default_factory=dict)  # Column definitions
    metadata: Dict[str, Any] = Field(default_factory=dict)
    row_count: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[UUID] = None
    org_id: Optional[UUID] = None
    
    class Config:
        from_attributes = True


class DatasetCreate(BaseModel):
    """Request to create a dataset."""
    name: str
    description: Optional[str] = None
    source_connector_id: Optional[UUID] = None
    schema: Optional[Dict[str, Any]] = None


class Transform(BaseModel):
    """Data transform definition."""
    id: UUID
    dataset_id: UUID
    name: str
    transform_type: str  # "filter", "map", "aggregate", "join", etc.
    config: Dict[str, Any] = Field(default_factory=dict)
    order: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        from_attributes = True


class SyntheticDataRequest(BaseModel):
    """Request to generate synthetic data."""
    source_dataset_id: UUID
    num_rows: int = 1000
    preserve_distribution: bool = True
    privacy_level: str = "high"  # "low", "medium", "high"
    config: Dict[str, Any] = Field(default_factory=dict)


class SyntheticDataResult(BaseModel):
    """Synthetic data generation result."""
    synthetic_dataset_id: UUID
    source_dataset_id: UUID
    num_rows: int
    quality_score: Optional[float] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

