"""Pydantic models for data connections API."""
from datetime import datetime
from typing import Optional, List, Any
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field


# ============================================================================
# ENUMS
# ============================================================================

class ConnectionType(str, Enum):
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    SQLSERVER = "sqlserver"
    SNOWFLAKE = "snowflake"
    BIGQUERY = "bigquery"
    S3 = "s3"
    FILE = "file"


class ConnectionStatus(str, Enum):
    PENDING = "pending"
    CONNECTED = "connected"
    FAILED = "failed"
    SCANNING = "scanning"


class ScanStatus(str, Enum):
    NEVER = "never"
    SCANNING = "scanning"
    COMPLETED = "completed"
    FAILED = "failed"


class CompatibilityStatus(str, Enum):
    READY = "ready"
    PARTIAL = "partial"
    INCOMPATIBLE = "incompatible"


# ============================================================================
# COLUMN SCAN MODELS
# ============================================================================

class ColumnScan(BaseModel):
    """Detailed scan results for a single column."""
    name: str
    data_type: str
    nullable: bool = True
    nulls_count: int = 0
    nulls_pct: float = 0.0
    cardinality: int = 0  # Unique values
    
    # Statistics (for numeric/date columns)
    min_value: Optional[Any] = None
    max_value: Optional[Any] = None
    mean_value: Optional[float] = None
    
    # Sample values
    sample_values: List[Any] = Field(default_factory=list)
    
    # Type hints for ML
    is_date: bool = False
    is_numeric: bool = False
    is_categorical: bool = False
    is_text: bool = False
    is_boolean: bool = False


class QualityIssue(BaseModel):
    """Detected data quality issue."""
    severity: str  # warning, error
    issue_type: str  # high_nulls, low_cardinality, outliers, etc.
    column: Optional[str] = None
    message: str
    recommendation: Optional[str] = None


# ============================================================================
# TABLE SCAN MODELS
# ============================================================================

class TableScanSummary(BaseModel):
    """Summary of a table scan."""
    id: UUID
    connection_id: UUID
    schema_name: Optional[str] = None
    table_name: str
    full_name: str
    row_count: Optional[int] = None
    column_count: Optional[int] = None
    date_column: Optional[str] = None
    date_span_days: Optional[int] = None
    completeness_score: Optional[float] = None
    quality_issues: List[QualityIssue] = Field(default_factory=list)
    scanned_at: Optional[datetime] = None


class TableScanDetail(BaseModel):
    """Full table scan details."""
    id: UUID
    connection_id: UUID
    schema_name: Optional[str] = None
    table_name: str
    full_name: str
    
    # Stats
    row_count: Optional[int] = None
    column_count: Optional[int] = None
    size_bytes: Optional[int] = None
    
    # Columns
    columns: List[ColumnScan] = Field(default_factory=list)
    
    # Time series
    date_column: Optional[str] = None
    date_min: Optional[datetime] = None
    date_max: Optional[datetime] = None
    date_span_days: Optional[int] = None
    
    # Quality
    completeness_score: Optional[float] = None
    quality_issues: List[QualityIssue] = Field(default_factory=list)
    
    # Sample
    sample_rows: List[dict] = Field(default_factory=list)
    
    scanned_at: Optional[datetime] = None


# ============================================================================
# CONNECTION MODELS
# ============================================================================

class DataConnectionCreate(BaseModel):
    """Create a new data connection."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    connection_type: ConnectionType
    
    # Connection details
    host: Optional[str] = None
    port: Optional[int] = None
    database: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None  # Will be encrypted
    extra_config: dict = Field(default_factory=dict)


class DataConnectionUpdate(BaseModel):
    """Update a data connection."""
    name: Optional[str] = None
    description: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None
    database: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    extra_config: Optional[dict] = None


class DataConnectionResponse(BaseModel):
    """Data connection response."""
    id: UUID
    name: str
    description: Optional[str] = None
    connection_type: str
    
    host: Optional[str] = None
    port: Optional[int] = None
    database: Optional[str] = None
    username: Optional[str] = None
    # password is never returned
    
    status: str
    last_connected_at: Optional[datetime] = None
    last_error: Optional[str] = None
    
    last_scan_at: Optional[datetime] = None
    scan_status: str
    tables_count: int = 0
    total_rows: int = 0
    
    created_at: datetime
    updated_at: datetime


class DataConnectionListResponse(BaseModel):
    """List of data connections."""
    connections: List[DataConnectionResponse]
    total: int


# ============================================================================
# SCAN REQUEST/RESPONSE
# ============================================================================

class ScanRequest(BaseModel):
    """Request to scan a connection or table."""
    full_scan: bool = False  # If true, scan all columns deeply
    sample_size: int = 1000  # Number of rows to sample
    include_sample_data: bool = True


class ConnectionScanResponse(BaseModel):
    """Response from scanning a connection."""
    connection_id: UUID
    tables_found: int
    tables_scanned: int
    total_rows: int
    scan_duration_seconds: float
    tables: List[TableScanSummary]


class TableScanResponse(BaseModel):
    """Response from scanning a specific table."""
    table: TableScanDetail
    scan_duration_seconds: float


# ============================================================================
# RECIPE COMPATIBILITY
# ============================================================================

class RequirementCheck(BaseModel):
    """Single requirement check result."""
    requirement: str  # e.g., "date_column", "target_numeric", "group_columns"
    status: str  # met, partial, missing
    column: Optional[str] = None  # Matched column if any
    notes: Optional[str] = None


class RecipeCompatibilityResponse(BaseModel):
    """Recipe compatibility assessment."""
    table_scan_id: UUID
    recipe_id: str
    recipe_name: str
    
    compatibility_score: float  # 0-100
    status: str  # ready, partial, incompatible
    
    requirements_met: List[RequirementCheck]
    requirements_missing: List[RequirementCheck]
    requirements_partial: List[RequirementCheck]
    
    recommendations: List[str]
    
    # Quick summary
    can_run: bool
    estimated_quality: str  # excellent, good, fair, poor


class TableCompatibilityResponse(BaseModel):
    """All recipe compatibility for a table."""
    table_scan_id: UUID
    table_name: str
    recipes: List[RecipeCompatibilityResponse]
