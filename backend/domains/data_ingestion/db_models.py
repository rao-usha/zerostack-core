"""
Data Ingestion Database Models

SQLAlchemy models for PE due diligence data ingestion.
"""
from datetime import datetime, date
from enum import Enum
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4

from sqlmodel import Column, Field as SQLField, Relationship, SQLModel
from sqlalchemy import DateTime, Text, BigInteger, Date
from sqlalchemy.dialects.postgresql import JSONB


class DealStatus(str, Enum):
    ACTIVE = "active"
    CLOSED = "closed"
    PASSED = "passed"
    ON_HOLD = "on_hold"


class FileStatus(str, Enum):
    PENDING = "pending"
    ANALYZING = "analyzing"
    COMPLETED = "completed"
    FAILED = "failed"


class UploadSource(str, Enum):
    MANUAL = "manual"
    CODAT = "codat"
    MERGE = "merge"
    API = "api"
    GDRIVE = "gdrive"


class IssueType(str, Enum):
    QUALITY = "quality"
    ANOMALY = "anomaly"
    RED_FLAG = "red_flag"
    MISSING_DATA = "missing_data"
    INCONSISTENCY = "inconsistency"


class IssueSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IssueStatus(str, Enum):
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


class PEDeal(SQLModel, table=True):
    """PE Deal / Target Company"""
    __tablename__ = "pe_deals"

    id: UUID = SQLField(default_factory=uuid4, primary_key=True)
    name: str = SQLField(nullable=False, index=True)
    target_company: str = SQLField(nullable=False)
    description: Optional[str] = SQLField(default=None, sa_column=Column(Text))
    status: str = SQLField(default=DealStatus.ACTIVE, nullable=False)
    deal_stage: Optional[str] = SQLField(default=None)
    deal_owner: Optional[str] = SQLField(default=None)
    target_close_date: Optional[date] = SQLField(default=None, sa_column=Column(Date))
    metadata_json: Optional[Dict[str, Any]] = SQLField(
        default=None, sa_column=Column("metadata", JSONB)
    )
    created_at: datetime = SQLField(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False)
    )
    updated_at: datetime = SQLField(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False)
    )

    # Relationships
    files: List["IngestedFile"] = Relationship(back_populates="deal")
    issues: List["IngestionIssue"] = Relationship(back_populates="deal")


class IngestedFile(SQLModel, table=True):
    """Uploaded file with analysis results"""
    __tablename__ = "ingested_files"

    id: UUID = SQLField(default_factory=uuid4, primary_key=True)
    deal_id: Optional[UUID] = SQLField(default=None, foreign_key="pe_deals.id")

    # File info
    filename: str = SQLField(nullable=False)
    original_filename: str = SQLField(nullable=False)
    file_type: str = SQLField(nullable=False)
    file_size_bytes: int = SQLField(sa_column=Column(BigInteger, nullable=False))
    content_hash: Optional[str] = SQLField(default=None)

    # Storage
    storage_path: Optional[str] = SQLField(default=None)
    storage_bucket: Optional[str] = SQLField(default=None)

    # Source
    upload_source: str = SQLField(default=UploadSource.MANUAL, nullable=False)
    source_system: Optional[str] = SQLField(default=None)
    source_account_id: Optional[str] = SQLField(default=None)

    # Analysis results
    quality_score: Optional[float] = SQLField(default=None)
    row_count: Optional[int] = SQLField(default=None)
    column_count: Optional[int] = SQLField(default=None)
    sheet_count: int = SQLField(default=1)
    detected_categories: Optional[List[str]] = SQLField(
        default=None, sa_column=Column(JSONB)
    )
    schema_analysis: Optional[Dict[str, Any]] = SQLField(
        default=None, sa_column=Column(JSONB)
    )
    analysis_summary: Optional[str] = SQLField(default=None, sa_column=Column(Text))

    # Status
    status: str = SQLField(default=FileStatus.PENDING, nullable=False)
    error_message: Optional[str] = SQLField(default=None, sa_column=Column(Text))

    # Audit
    uploaded_by: Optional[str] = SQLField(default=None)
    uploaded_at: datetime = SQLField(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False)
    )
    analyzed_at: Optional[datetime] = SQLField(
        default=None, sa_column=Column(DateTime(timezone=True))
    )

    # Relationships
    deal: Optional[PEDeal] = Relationship(back_populates="files")
    issues: List["IngestionIssue"] = Relationship(back_populates="file")


class IngestionIssue(SQLModel, table=True):
    """Quality issue or red flag detected in ingested data"""
    __tablename__ = "ingestion_issues"

    id: UUID = SQLField(default_factory=uuid4, primary_key=True)
    file_id: UUID = SQLField(foreign_key="ingested_files.id", nullable=False)
    deal_id: Optional[UUID] = SQLField(default=None, foreign_key="pe_deals.id")

    # Issue details
    issue_type: str = SQLField(nullable=False)
    severity: str = SQLField(nullable=False)
    category: Optional[str] = SQLField(default=None)
    sheet_name: Optional[str] = SQLField(default=None)
    column_name: Optional[str] = SQLField(default=None)
    row_number: Optional[int] = SQLField(default=None)

    # Description
    title: str = SQLField(nullable=False)
    description: Optional[str] = SQLField(default=None, sa_column=Column(Text))
    details: Optional[Dict[str, Any]] = SQLField(default=None, sa_column=Column(JSONB))
    recommendation: Optional[str] = SQLField(default=None, sa_column=Column(Text))

    # Resolution
    status: str = SQLField(default=IssueStatus.OPEN, nullable=False)
    acknowledged: bool = SQLField(default=False, nullable=False)
    acknowledged_by: Optional[str] = SQLField(default=None)
    acknowledged_at: Optional[datetime] = SQLField(
        default=None, sa_column=Column(DateTime(timezone=True))
    )
    resolution_notes: Optional[str] = SQLField(default=None, sa_column=Column(Text))

    # Timestamps
    created_at: datetime = SQLField(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False)
    )

    # Relationships
    file: IngestedFile = Relationship(back_populates="issues")
    deal: Optional[PEDeal] = Relationship(back_populates="issues")
