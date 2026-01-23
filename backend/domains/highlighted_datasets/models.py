"""Pydantic models for Highlighted Datasets API."""
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field
from enum import Enum


class AvailabilityState(str, Enum):
    """Possible availability states for a highlighted dataset."""
    AVAILABLE = "AVAILABLE"
    NOT_PRESENT = "NOT_PRESENT"
    REQUIRES_CREDENTIALS = "REQUIRES_CREDENTIALS"
    INGESTING = "INGESTING"
    ERROR = "ERROR"


class SourceType(str, Enum):
    """Supported dataset source types."""
    MANUAL_UPLOAD = "manual_upload"
    HTTP_DOWNLOAD = "http_download"
    KAGGLE = "kaggle"
    LOCAL_FILE = "local_file"


# ========================================
# Response Models
# ========================================

class HighlightedDatasetResponse(BaseModel):
    """Highlighted dataset response."""
    id: str
    display_name: str
    description: Optional[str] = None
    tags: List[str] = []
    source_type: str
    availability_state: str
    license_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    # Include latest version info if available
    latest_version: Optional["DatasetVersionResponse"] = None
    
    class Config:
        from_attributes = True


class DatasetVersionResponse(BaseModel):
    """Dataset version response."""
    id: UUID
    highlighted_dataset_id: str
    version_label: str
    manifest_uri: str
    storage_uri: str
    file_count: Optional[int] = None
    total_bytes: Optional[int] = None
    created_at: datetime
    created_by: Optional[str] = None
    
    class Config:
        from_attributes = True


class HighlightedDatasetListResponse(BaseModel):
    """Response for listing highlighted datasets."""
    datasets: List[HighlightedDatasetResponse]
    total: int


class DatasetVersionListResponse(BaseModel):
    """Response for listing dataset versions."""
    versions: List[DatasetVersionResponse]
    total: int


# ========================================
# Request Models
# ========================================

class HighlightedDatasetCreate(BaseModel):
    """Create a new highlighted dataset entry."""
    id: str = Field(..., min_length=1, max_length=100, pattern=r'^[a-z0-9_]+$')
    display_name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    tags: List[str] = []
    source_type: SourceType
    default_location_uri: Optional[str] = None
    resolver_config: Dict[str, Any] = {}
    license_notes: Optional[str] = None


class HighlightedDatasetUpdate(BaseModel):
    """Update a highlighted dataset entry."""
    display_name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    resolver_config: Optional[Dict[str, Any]] = None
    license_notes: Optional[str] = None


class ResolveRequest(BaseModel):
    """Request to resolve/ingest a dataset."""
    force_refresh: bool = False
    credentials: Optional[Dict[str, str]] = None  # For REQUIRES_CREDENTIALS state


class ResolveResponse(BaseModel):
    """Response from resolve operation."""
    dataset_id: str
    availability_state: str
    version: Optional[DatasetVersionResponse] = None
    message: str
    ingest_job_id: Optional[str] = None  # If ingestion was triggered


class FileUploadResponse(BaseModel):
    """Response after file upload."""
    filename: str
    size_bytes: int
    storage_path: str
    uploaded: bool


class UploadCompleteRequest(BaseModel):
    """Request to finalize upload and create version."""
    version_label: str = Field(default="v1", max_length=64)
    description: Optional[str] = None


class UploadCompleteResponse(BaseModel):
    """Response after finalizing upload."""
    dataset_id: str
    version: DatasetVersionResponse
    message: str


# Forward ref update
HighlightedDatasetResponse.model_rebuild()
