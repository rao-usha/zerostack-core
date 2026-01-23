"""
Data Ingestion Models

Pydantic schemas for CSV/Excel upload and schema detection.
"""
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class InferredDataType(str, Enum):
    """Inferred column data types"""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    DATE = "date"
    DATETIME = "datetime"
    CURRENCY = "currency"
    PERCENTAGE = "percentage"
    EMAIL = "email"
    PHONE = "phone"
    URL = "url"
    UUID = "uuid"


class DataQualityFlag(str, Enum):
    """Data quality issues detected"""
    MISSING_VALUES = "missing_values"
    MIXED_TYPES = "mixed_types"
    OUTLIERS = "outliers"
    DUPLICATES = "duplicates"
    INCONSISTENT_FORMAT = "inconsistent_format"
    EMPTY_COLUMN = "empty_column"
    HIGH_CARDINALITY = "high_cardinality"
    LOW_CARDINALITY = "low_cardinality"


class AnomalyType(str, Enum):
    """Types of statistical anomalies detected"""
    STATISTICAL_OUTLIER = "statistical_outlier"
    BENFORDS_VIOLATION = "benfords_violation"
    DISTRIBUTION_SHIFT = "distribution_shift"
    TEMPORAL_GAP = "temporal_gap"
    ROUND_NUMBER_BIAS = "round_number_bias"


class RedFlagType(str, Enum):
    """Types of PE-specific red flags"""
    NEGATIVE_REVENUE = "negative_revenue"
    IMPOSSIBLE_MARGIN = "impossible_margin"
    EXTREME_GROWTH = "extreme_growth"
    HIGH_CHURN = "high_churn"
    CUSTOMER_CONCENTRATION = "customer_concentration"
    HEADCOUNT_MISMATCH = "headcount_mismatch"
    PERIOD_END_SPIKE = "period_end_spike"
    FUTURE_DATES = "future_dates"
    DUPLICATE_ROWS = "duplicate_rows"
    NEGATIVE_IMPOSSIBLE = "negative_impossible"


class AnomalyResult(BaseModel):
    """Result from anomaly detection"""
    anomaly_type: AnomalyType
    severity: str  # low, medium, high, critical
    column_name: Optional[str] = None
    title: str
    description: str
    evidence: Dict[str, Any] = Field(default_factory=dict)
    recommendation: str
    affected_rows: Optional[int] = None
    affected_percent: Optional[float] = None


class RedFlagResult(BaseModel):
    """Result from PE red flag scanning"""
    flag_type: RedFlagType
    severity: str  # low, medium, high, critical
    category: str  # financial, customer, operational, data_quality
    title: str
    description: str
    evidence: Dict[str, Any] = Field(default_factory=dict)
    recommendation: str
    affected_columns: List[str] = Field(default_factory=list)


class ColumnAnalysis(BaseModel):
    """Analysis of a single column"""
    name: str
    inferred_type: InferredDataType
    nullable: bool
    null_count: int
    null_percent: float
    unique_count: int
    unique_percent: float
    example_values: List[str] = Field(default_factory=list)
    min_value: Optional[str] = None
    max_value: Optional[str] = None
    mean_value: Optional[float] = None
    quality_flags: List[DataQualityFlag] = Field(default_factory=list)

    # For numeric columns
    std_dev: Optional[float] = None

    # For string columns
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    avg_length: Optional[float] = None


class SheetAnalysis(BaseModel):
    """Analysis of a single sheet/table"""
    sheet_name: str
    row_count: int
    column_count: int
    columns: List[ColumnAnalysis]
    sample_data: List[List[Any]]
    quality_score: float = Field(ge=0, le=100, description="Overall quality score 0-100")
    quality_issues: List[str] = Field(default_factory=list)
    anomalies: List[Dict[str, Any]] = Field(default_factory=list)
    red_flags: List[Dict[str, Any]] = Field(default_factory=list)


class FileAnalysisResponse(BaseModel):
    """Response from file upload and analysis"""
    filename: str
    file_size_bytes: int
    file_type: str
    sheets: List[SheetAnalysis]
    total_rows: int
    total_columns: int
    analysis_duration_ms: int
    overall_quality_score: float
    summary: str

    # PE Due Diligence specific
    detected_data_categories: List[str] = Field(default_factory=list)
    potential_issues: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)


class UploadError(BaseModel):
    """Error response for upload failures"""
    error: str
    details: Optional[str] = None


# --- Deal Models ---

class DealCreate(BaseModel):
    """Create a new PE deal"""
    name: str
    target_company: str
    description: Optional[str] = None
    deal_stage: Optional[str] = None
    deal_owner: Optional[str] = None
    target_close_date: Optional[str] = None  # YYYY-MM-DD


class DealUpdate(BaseModel):
    """Update a PE deal"""
    name: Optional[str] = None
    target_company: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    deal_stage: Optional[str] = None
    deal_owner: Optional[str] = None
    target_close_date: Optional[str] = None


class DealResponse(BaseModel):
    """PE deal response"""
    id: str
    name: str
    target_company: str
    description: Optional[str] = None
    status: str
    deal_stage: Optional[str] = None
    deal_owner: Optional[str] = None
    target_close_date: Optional[str] = None
    file_count: int = 0
    issue_count: int = 0
    avg_quality_score: Optional[float] = None
    created_at: datetime
    updated_at: datetime


class DealSummary(BaseModel):
    """Deal summary with aggregated stats"""
    id: str
    name: str
    target_company: str
    status: str
    file_count: int
    total_rows: int
    issue_count: int
    critical_issues: int
    avg_quality_score: Optional[float]
    detected_categories: List[str]
    created_at: datetime


# --- File Models ---

class IngestedFileResponse(BaseModel):
    """Ingested file response"""
    id: str
    deal_id: Optional[str] = None
    deal_name: Optional[str] = None
    filename: str
    original_filename: str
    file_type: str
    file_size_bytes: int
    upload_source: str
    quality_score: Optional[float] = None
    row_count: Optional[int] = None
    column_count: Optional[int] = None
    sheet_count: int = 1
    detected_categories: List[str] = Field(default_factory=list)
    status: str
    issue_count: int = 0
    uploaded_by: Optional[str] = None
    uploaded_at: datetime
    analyzed_at: Optional[datetime] = None


class IngestedFileDetail(BaseModel):
    """Detailed file info with full analysis"""
    id: str
    deal_id: Optional[str] = None
    deal_name: Optional[str] = None
    filename: str
    original_filename: str
    file_type: str
    file_size_bytes: int
    content_hash: Optional[str] = None
    upload_source: str
    source_system: Optional[str] = None
    quality_score: Optional[float] = None
    row_count: Optional[int] = None
    column_count: Optional[int] = None
    sheet_count: int = 1
    detected_categories: List[str] = Field(default_factory=list)
    schema_analysis: Optional[Dict[str, Any]] = None
    analysis_summary: Optional[str] = None
    status: str
    error_message: Optional[str] = None
    issues: List["IssueResponse"] = Field(default_factory=list)
    uploaded_by: Optional[str] = None
    uploaded_at: datetime
    analyzed_at: Optional[datetime] = None


# --- Issue Models ---

class IssueResponse(BaseModel):
    """Ingestion issue response"""
    id: str
    file_id: str
    deal_id: Optional[str] = None
    issue_type: str
    severity: str
    category: Optional[str] = None
    sheet_name: Optional[str] = None
    column_name: Optional[str] = None
    row_number: Optional[int] = None
    title: str
    description: Optional[str] = None
    recommendation: Optional[str] = None
    status: str
    acknowledged: bool
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    created_at: datetime


class IssueAcknowledge(BaseModel):
    """Acknowledge an issue"""
    acknowledged_by: str
    resolution_notes: Optional[str] = None
    new_status: Optional[str] = None  # acknowledged, resolved, dismissed


class IssueSummary(BaseModel):
    """Summary of issues by type/severity"""
    total: int
    by_severity: Dict[str, int]
    by_type: Dict[str, int]
    unacknowledged: int
    critical_count: int


# --- Upload with persistence ---

class UploadResponse(BaseModel):
    """Response from file upload with persistence"""
    file_id: str
    filename: str
    file_size_bytes: int
    file_type: str
    quality_score: float
    row_count: int
    column_count: int
    sheet_count: int
    detected_categories: List[str]
    issue_count: int
    analysis_summary: str
    status: str


class BatchUploadResponse(BaseModel):
    """Response from batch file upload"""
    files: List[UploadResponse]
    total_files: int
    successful: int
    failed: int
    total_rows: int
    avg_quality_score: float


class ReAnalyzeRequest(BaseModel):
    """Request to re-run analysis on an existing file"""
    run_anomaly_detection: bool = True
    run_red_flag_scan: bool = True


class ReAnalyzeResponse(BaseModel):
    """Response from re-analysis"""
    file_id: str
    new_anomalies: int
    new_red_flags: int
    total_issues: int
    analysis_summary: str


# Update forward references
IngestedFileDetail.model_rebuild()
