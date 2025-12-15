"""Data Explorer models and schemas."""
from typing import Optional, List, Any, Dict
from pydantic import BaseModel, Field, validator


class SchemaInfo(BaseModel):
    """Database schema information."""
    name: str
    table_count: Optional[int] = None


class TableInfo(BaseModel):
    """Table or view information."""
    schema: str
    name: str
    type: str  # 'table' or 'view'
    row_estimate: Optional[int] = None


class ColumnInfo(BaseModel):
    """Column metadata."""
    name: str
    data_type: str
    is_nullable: bool
    default: Optional[str] = None
    ordinal_position: int


class TableRowsResponse(BaseModel):
    """Response for table rows query."""
    schema: str
    table: str
    columns: List[str]
    rows: List[List[Any]]
    page: int
    page_size: int
    total_rows: Optional[int] = None


class QueryRequest(BaseModel):
    """SQL query request."""
    sql: str = Field(..., min_length=1, max_length=10000)
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=100, ge=1, le=1000)
    
    @validator('sql')
    def validate_sql(cls, v):
        """Basic validation that SQL is not empty."""
        if not v or not v.strip():
            raise ValueError("SQL query cannot be empty")
        return v.strip()


class QueryResponse(BaseModel):
    """SQL query response."""
    columns: List[str]
    rows: List[List[Any]]
    total_rows_estimate: Optional[int] = None
    execution_time_ms: float
    error: Optional[Dict[str, str]] = None


class TableSummaryResponse(BaseModel):
    """Table summary statistics."""
    schema: str
    table: str
    column_stats: Dict[str, Any]


class ErrorResponse(BaseModel):
    """Structured error response."""
    message: str
    code: Optional[str] = None


# AI Analysis Models

class TableSelection(BaseModel):
    """Table selection for analysis."""
    schema: str
    table: str


class AnalysisRequest(BaseModel):
    """Request to analyze tables with AI."""
    tables: List[Dict[str, str]] = Field(..., min_items=1, max_items=10)
    analysis_types: List[str] = Field(
        default=["profiling", "quality"],
        description="Types of analysis: profiling, quality, anomaly, relationships, trends, patterns, column_documentation"
    )
    provider: str = Field(
        default="openai",
        description="LLM provider: openai, anthropic, google, xai"
    )
    model: str = Field(
        default="gpt-4o",
        description="Model name"
    )
    db_id: str = Field(default="default")
    context: Optional[str] = Field(
        default=None,
        description="Additional context about the business domain"
    )
    
    @validator('analysis_types')
    def validate_analysis_types(cls, v):
        """Validate analysis types."""
        valid_types = {"profiling", "quality", "anomaly", "relationships", "trends", "patterns", "column_documentation"}
        invalid = set(v) - valid_types
        if invalid:
            raise ValueError(f"Invalid analysis types: {invalid}. Valid types: {valid_types}")
        return v


class AnalysisResult(BaseModel):
    """Result of AI analysis."""
    analysis_id: str
    tables: List[Dict[str, str]]  # Changed to accept plain dicts
    analysis_types: List[str]
    provider: str
    model: str
    insights: Dict[str, Any]  # Main analysis results organized by type
    summary: str  # Executive summary
    recommendations: List[str]  # Actionable recommendations
    metadata: Dict[str, Any]  # Execution metadata (time, tokens, etc.)
    created_at: str


class AnalysisResponse(BaseModel):
    """Response from analysis endpoint."""
    analysis_id: str
    status: str  # "running", "completed", "failed"
    message: Optional[str] = None
    result: Optional[AnalysisResult] = None
    error: Optional[str] = None


class SavedAnalysis(BaseModel):
    """Saved analysis record."""
    id: str
    name: str
    description: Optional[str] = None
    analysis_result: AnalysisResult
    saved_at: str
    tags: List[str] = Field(default_factory=list)