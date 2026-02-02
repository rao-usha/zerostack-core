"""Pydantic models for Query Workbench."""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID


# ========================================
# Query Parameter Models
# ========================================

class QueryParameter(BaseModel):
    """Definition of a query parameter."""
    name: str = Field(..., description="Parameter name (e.g., 'start_date')")
    type: str = Field(default="string", description="Parameter type: string, number, date, boolean")
    default: Optional[str] = Field(None, description="Default value")
    description: Optional[str] = Field(None, description="Help text for the parameter")


# ========================================
# Saved Query Models
# ========================================

class SavedQueryCreate(BaseModel):
    """Request to create a saved query."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    sql: str = Field(..., min_length=1, max_length=100000)
    db_id: str = Field(default="default")
    folder: Optional[str] = Field(None, max_length=255)
    tags: Optional[List[str]] = None
    parameters: Optional[List[QueryParameter]] = None
    is_public: bool = False


class SavedQueryUpdate(BaseModel):
    """Request to update a saved query."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    sql: Optional[str] = Field(None, min_length=1, max_length=100000)
    folder: Optional[str] = Field(None, max_length=255)
    tags: Optional[List[str]] = None
    parameters: Optional[List[QueryParameter]] = None
    is_public: Optional[bool] = None
    schedule_cron: Optional[str] = None
    schedule_enabled: Optional[bool] = None
    cache_ttl_seconds: Optional[int] = None


class SavedQueryResponse(BaseModel):
    """Response for a saved query."""
    id: str
    name: str
    description: Optional[str]
    sql: str
    db_id: str
    folder: Optional[str]
    tags: Optional[List[str]]
    parameters: Optional[List[QueryParameter]]
    is_public: bool
    created_by: Optional[str]
    schedule_cron: Optional[str]
    schedule_enabled: bool
    cache_ttl_seconds: Optional[int]
    run_count: int
    last_run_at: Optional[datetime]
    avg_execution_time_ms: Optional[float]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SavedQueryListItem(BaseModel):
    """Abbreviated response for listing saved queries."""
    id: str
    name: str
    description: Optional[str]
    db_id: str
    folder: Optional[str]
    tags: Optional[List[str]]
    is_public: bool
    created_by: Optional[str]
    run_count: int
    last_run_at: Optional[datetime]
    avg_execution_time_ms: Optional[float]
    created_at: datetime

    class Config:
        from_attributes = True


class SavedQueryListResponse(BaseModel):
    """Paginated list of saved queries."""
    queries: List[SavedQueryListItem]
    total: int
    page: int
    page_size: int


# ========================================
# Query Execution Models
# ========================================

class ExecuteQueryRequest(BaseModel):
    """Request to execute a saved query."""
    parameters: Optional[Dict[str, Any]] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=100, ge=1, le=1000)


class QueryExecutionResponse(BaseModel):
    """Response for a query execution."""
    id: str
    saved_query_id: Optional[str]
    sql_snapshot: str
    db_id: str
    parameters_used: Optional[Dict[str, Any]]
    status: str
    started_at: datetime
    finished_at: Optional[datetime]
    execution_time_ms: Optional[float]
    row_count: Optional[int]
    column_count: Optional[int]
    result_preview: Optional[Dict[str, Any]]
    error_message: Optional[str]
    error_code: Optional[str]
    executed_by: Optional[str]
    source: str

    class Config:
        from_attributes = True


class QueryExecutionListResponse(BaseModel):
    """List of query executions."""
    executions: List[QueryExecutionResponse]
    total: int


class QueryResultResponse(BaseModel):
    """Full query result with data."""
    execution_id: str
    columns: List[str]
    rows: List[List[Any]]
    total_rows: int
    execution_time_ms: float
    page: int
    page_size: int


# ========================================
# Folder Models
# ========================================

class FolderInfo(BaseModel):
    """Information about a query folder."""
    name: str
    query_count: int
