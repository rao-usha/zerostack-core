"""
Highlighted Datasets SQLModel database models.

Maps to tables created in migration 020_add_gpu_runner.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4
from sqlmodel import SQLModel, Field as SQLField, Column, Relationship
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from sqlalchemy import String


class HighlightedDataset(SQLModel, table=True):
    """
    A curated dataset entry visible in the UI catalog.
    
    May be already available in object storage or not yet present.
    The resolver handles checking availability and triggering ingestion.
    """
    __tablename__ = "highlighted_datasets"
    
    id: str = SQLField(max_length=100, primary_key=True)  # e.g., "m5_forecasting"
    display_name: str = SQLField(max_length=255)
    description: Optional[str] = None
    tags: List[str] = SQLField(default=[], sa_column=Column(ARRAY(String)))
    
    # Source configuration
    source_type: str = SQLField(max_length=50)  # manual_upload, http_download, kaggle
    default_location_uri: Optional[str] = SQLField(default=None, max_length=500)
    
    # Availability tracking
    availability_state: str = SQLField(default="NOT_PRESENT", max_length=30)
    # States: AVAILABLE, NOT_PRESENT, REQUIRES_CREDENTIALS, INGESTING, ERROR
    
    # Resolver configuration (JSON)
    resolver_config: Dict[str, Any] = SQLField(default={}, sa_column=Column(JSONB))
    # Example: {
    #   "dataset_id": "m5",
    #   "target_bucket_prefix": "datasets/m5",
    #   "ingest_method": "manual_upload",
    #   "required_files": ["calendar.csv", "sales.csv", "prices.csv"]
    # }
    
    license_notes: Optional[str] = None
    
    created_at: datetime = SQLField(default_factory=datetime.utcnow)
    updated_at: datetime = SQLField(default_factory=datetime.utcnow)
    
    # Relationships
    versions: List["HighlightedDatasetVersion"] = Relationship(back_populates="dataset")


class HighlightedDatasetVersion(SQLModel, table=True):
    """
    A versioned dataset reference with manifest in object storage.

    Each version points to a specific set of files at a known location.
    """
    __tablename__ = "highlighted_dataset_versions"
    model_config = {"protected_namespaces": ()}  # Allow schema_json field name

    id: Optional[UUID] = SQLField(default_factory=uuid4, primary_key=True)
    highlighted_dataset_id: str = SQLField(foreign_key="highlighted_datasets.id", max_length=100)
    
    version_label: str = SQLField(max_length=64)  # e.g., "v1", "2024-01"
    manifest_uri: str = SQLField(max_length=500)  # s3://bucket/datasets/m5/v1/manifest.json
    storage_uri: str = SQLField(max_length=500)   # s3://bucket/datasets/m5/v1/
    
    # File statistics
    file_count: Optional[int] = None
    total_bytes: Optional[int] = None
    
    # Optional schema definition
    schema_json: Optional[Dict[str, Any]] = SQLField(default=None, sa_column=Column(JSONB))
    
    created_at: datetime = SQLField(default_factory=datetime.utcnow)
    created_by: Optional[str] = SQLField(default=None, max_length=100)
    
    # Relationships
    dataset: Optional[HighlightedDataset] = Relationship(back_populates="versions")
