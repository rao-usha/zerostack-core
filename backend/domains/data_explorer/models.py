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

