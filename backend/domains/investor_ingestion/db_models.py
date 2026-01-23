"""
Investor Ingestion Database Models

SQLAlchemy models for tracking FO/LP data ingestion jobs.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4

from sqlmodel import Column, Field as SQLField, SQLModel
from sqlalchemy import DateTime, Text, BigInteger
from sqlalchemy.dialects.postgresql import JSONB


class IngestionJob(SQLModel, table=True):
    """Tracks an investor data ingestion job."""
    __tablename__ = "investor_ingestion_jobs"

    id: UUID = SQLField(default_factory=uuid4, primary_key=True)

    # File info
    filename: str = SQLField(nullable=False)
    original_filename: str = SQLField(nullable=False)
    file_type: str = SQLField(nullable=False)
    file_size_bytes: int = SQLField(sa_column=Column(BigInteger, nullable=False))
    storage_path: Optional[str] = SQLField(default=None)

    # Target
    target_entity: str = SQLField(nullable=False, index=True)
    parent_id: Optional[int] = SQLField(default=None)

    # Mapping
    field_mappings: List[Dict[str, Any]] = SQLField(
        default=None, sa_column=Column(JSONB)
    )

    # Status
    status: str = SQLField(default="pending", nullable=False, index=True)
    error_message: Optional[str] = SQLField(default=None, sa_column=Column(Text))

    # Row counts
    total_rows: int = SQLField(default=0)
    rows_processed: int = SQLField(default=0)
    rows_inserted: int = SQLField(default=0)
    rows_updated: int = SQLField(default=0)
    rows_failed: int = SQLField(default=0)

    # Errors (stored as JSON array)
    errors: Optional[List[Dict[str, Any]]] = SQLField(
        default=None, sa_column=Column(JSONB)
    )

    # Options
    options: Optional[Dict[str, Any]] = SQLField(
        default=None, sa_column=Column(JSONB)
    )

    # Audit
    created_by: Optional[str] = SQLField(default=None)
    created_at: datetime = SQLField(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False)
    )
    started_at: Optional[datetime] = SQLField(
        default=None, sa_column=Column(DateTime(timezone=True))
    )
    completed_at: Optional[datetime] = SQLField(
        default=None, sa_column=Column(DateTime(timezone=True))
    )


class MappingTemplateDB(SQLModel, table=True):
    """Saved field mapping template."""
    __tablename__ = "investor_mapping_templates"

    id: UUID = SQLField(default_factory=uuid4, primary_key=True)
    name: str = SQLField(nullable=False, index=True)
    target_entity: str = SQLField(nullable=False, index=True)
    field_mappings: List[Dict[str, Any]] = SQLField(
        default=None, sa_column=Column(JSONB)
    )

    # Audit
    created_by: Optional[str] = SQLField(default=None)
    created_at: datetime = SQLField(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False)
    )
    updated_at: datetime = SQLField(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False)
    )
