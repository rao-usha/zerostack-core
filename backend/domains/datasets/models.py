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


class DatasetSourceType(str, Enum):
    """How the dataset was created."""
    UPLOAD = "upload"
    NOTEBOOK = "notebook"
    CONNECTION = "connection"
    SYNTHETIC = "synthetic"


class ColumnSchema(BaseModel):
    """Column schema definition."""
    name: str
    dtype: str
    nullable: bool = True
    stats: Optional[Dict[str, Any]] = None


class DatasetSchema(BaseModel):
    """Dataset schema."""
    columns: List[ColumnSchema] = Field(default_factory=list)


class Dataset(BaseModel):
    """Dataset definition."""
    id: UUID
    name: str
    description: Optional[str] = None
    status: DatasetStatus = DatasetStatus.ACTIVE
    source_type: DatasetSourceType = DatasetSourceType.UPLOAD
    source_id: Optional[UUID] = None
    data_schema: Dict[str, Any] = Field(default_factory=dict, alias="schema")
    row_count: Optional[int] = None
    column_count: Optional[int] = None
    size_bytes: Optional[int] = None
    storage_uri: Optional[str] = None
    storage_format: str = "parquet"
    current_version_number: int = 0
    tags: List[str] = Field(default_factory=list)
    org_id: str = "default"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None

    class Config:
        from_attributes = True
        populate_by_name = True


class DatasetCreate(BaseModel):
    """Request to create a dataset (metadata only)."""
    name: str
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    org_id: Optional[str] = "default"


class DatasetUpdate(BaseModel):
    """Request to update a dataset."""
    name: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    status: Optional[DatasetStatus] = None


class DatasetVersion(BaseModel):
    """Dataset version."""
    id: UUID
    dataset_id: UUID
    version_number: int
    sha256: str
    storage_uri: str
    storage_format: str
    original_filename: Optional[str] = None
    row_count: Optional[int] = None
    column_count: Optional[int] = None
    size_bytes: Optional[int] = None
    data_schema: Dict[str, Any] = Field(default_factory=dict, alias="schema")
    quality_profile: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None
    notes: Optional[str] = None

    class Config:
        from_attributes = True
        populate_by_name = True


class DatasetUploadResponse(BaseModel):
    """Response after uploading a dataset."""
    dataset: Dataset
    version: DatasetVersion
    message: str = "Upload successful"


class DatasetListResponse(BaseModel):
    """Paginated list of datasets."""
    items: List[Dataset]
    total: int
    page: int
    page_size: int


class DatasetVersionListResponse(BaseModel):
    """List of dataset versions."""
    items: List[DatasetVersion]
    total: int


class DatasetPreviewResponse(BaseModel):
    """Preview of dataset data."""
    columns: List[str]
    rows: List[Dict[str, Any]]
    total_rows: int
    preview_rows: int


class DatasetDownloadResponse(BaseModel):
    """Download URL response."""
    download_url: str
    expires_in: int
    format: str


class QualityProfile(BaseModel):
    """Data quality profile."""
    completeness: float  # % non-null values
    uniqueness: Dict[str, float]  # unique ratio per column
    row_count: int
    column_count: int
    null_counts: Dict[str, int]
    duplicate_rows: int


# Legacy models for backward compatibility
class Transform(BaseModel):
    """Data transform definition."""
    id: UUID
    dataset_id: UUID
    name: str
    transform_type: str
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
    privacy_level: str = "high"
    config: Dict[str, Any] = Field(default_factory=dict)


class SyntheticDataResult(BaseModel):
    """Synthetic data generation result."""
    synthetic_dataset_id: UUID
    source_dataset_id: UUID
    num_rows: int
    quality_score: Optional[float] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
