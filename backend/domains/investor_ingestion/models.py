"""Pydantic models for Investor Ingestion API."""
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field


class IngestionStatus(str, Enum):
    """Status of an ingestion job."""
    PENDING = "pending"
    VALIDATING = "validating"
    MAPPING = "mapping"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class TargetEntityType(str, Enum):
    """Target entity type for ingestion."""
    FAMILY_OFFICE = "family_office"
    FO_CONTACT = "fo_contact"
    FO_INTERACTION = "fo_interaction"
    CO_INVESTMENT = "co_investment"
    PORTFOLIO_COMPANY = "portfolio_company"
    INVESTOR_THEME = "investor_theme"
    IMPACT_ANALYSIS = "impact_analysis"
    LP_FUND = "lp_fund"
    LP_CONTACT = "lp_contact"
    LP_DOCUMENT = "lp_document"
    LP_ALLOCATION = "lp_allocation"
    LP_EXPOSURE = "lp_exposure"


# ========================================
# Field Mapping Models
# ========================================

class FieldMapping(BaseModel):
    """Mapping from source field to target field."""
    source_field: str = Field(..., description="Field name in the source file")
    target_field: str = Field(..., description="Target field name in the database")
    transform: Optional[str] = Field(None, description="Optional transformation (e.g., 'uppercase', 'date_parse')")
    default_value: Optional[Any] = Field(None, description="Default value if source is missing/null")


class MappingTemplate(BaseModel):
    """Saved field mapping template."""
    id: Optional[str] = None
    name: str = Field(..., description="Template name")
    target_entity: TargetEntityType
    field_mappings: List[FieldMapping]
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class MappingSuggestion(BaseModel):
    """Suggested field mapping with confidence score."""
    source_field: str
    suggested_target: str
    confidence: float = Field(..., ge=0, le=1, description="Confidence score 0-1")
    reasoning: Optional[str] = None


# ========================================
# Upload & Preview Models
# ========================================

class ColumnPreview(BaseModel):
    """Preview of a column from the uploaded file."""
    name: str
    inferred_type: str
    sample_values: List[Any]
    null_count: int
    unique_count: int


class UploadPreviewResponse(BaseModel):
    """Response from preview endpoint."""
    filename: str
    file_size_bytes: int
    total_rows: int
    total_columns: int
    columns: List[ColumnPreview]
    sample_data: List[Dict[str, Any]]
    suggested_entity: Optional[TargetEntityType] = None
    mapping_suggestions: List[MappingSuggestion] = []


class IngestionRequest(BaseModel):
    """Request to start ingestion."""
    filename: str = Field(..., description="Name of the uploaded file")
    target_entity: TargetEntityType
    field_mappings: List[FieldMapping]
    parent_id: Optional[int] = Field(None, description="Parent entity ID (e.g., family_office_id for contacts)")
    options: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional options")


# ========================================
# Job Status Models
# ========================================

class IngestionJobSummary(BaseModel):
    """Summary view of an ingestion job."""
    id: str
    filename: str
    target_entity: str
    status: IngestionStatus
    total_rows: int
    rows_processed: int
    rows_inserted: int
    rows_updated: int
    rows_failed: int
    created_at: datetime
    completed_at: Optional[datetime] = None


class IngestionError(BaseModel):
    """Error encountered during ingestion."""
    row_number: int
    field: Optional[str] = None
    error_type: str
    message: str
    raw_value: Optional[Any] = None


class IngestionJobDetail(BaseModel):
    """Full detail of an ingestion job."""
    id: str
    filename: str
    original_filename: str
    file_size_bytes: int
    target_entity: str
    status: IngestionStatus
    total_rows: int
    rows_processed: int
    rows_inserted: int
    rows_updated: int
    rows_failed: int
    field_mappings: List[FieldMapping]
    errors: List[IngestionError] = []
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None


class IngestionJobListResponse(BaseModel):
    """Paginated response for list of ingestion jobs."""
    jobs: List[IngestionJobSummary]
    total: int
    page: int
    page_size: int


# ========================================
# Template Models
# ========================================

class TemplateListResponse(BaseModel):
    """Response for list of mapping templates."""
    templates: List[MappingTemplate]
    total: int


class CreateTemplateRequest(BaseModel):
    """Request to create a mapping template."""
    name: str = Field(..., description="Template name")
    target_entity: TargetEntityType
    field_mappings: List[FieldMapping]
