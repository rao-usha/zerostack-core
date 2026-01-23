"""Pydantic models for notebooks API."""
from datetime import datetime
from typing import Optional, List, Any
from uuid import UUID
from enum import Enum

from pydantic import BaseModel, Field


class CellType(str, Enum):
    SQL = "sql"
    PYTHON = "python"
    MARKDOWN = "markdown"


class RunStatus(str, Enum):
    SUCCESS = "success"
    ERROR = "error"
    RUNNING = "running"


# ============================================================================
# CELL MODELS
# ============================================================================

class CellCreate(BaseModel):
    """Create a new cell."""
    cell_type: CellType = CellType.SQL
    content: str = ""
    position: Optional[int] = None  # If not provided, append to end
    connection_id: Optional[UUID] = None
    settings: dict = Field(default_factory=dict)


class CellUpdate(BaseModel):
    """Update a cell."""
    content: Optional[str] = None
    position: Optional[int] = None
    connection_id: Optional[UUID] = None
    settings: Optional[dict] = None


class CellResponse(BaseModel):
    """Cell response."""
    id: UUID
    notebook_id: UUID
    cell_type: str
    content: str
    position: int
    
    # Execution state
    last_run_at: Optional[datetime] = None
    last_run_duration_ms: Optional[int] = None
    last_run_status: Optional[str] = None
    last_run_error: Optional[str] = None
    last_run_row_count: Optional[int] = None
    
    # Results
    cached_results: Optional[List[dict]] = None
    
    # Settings
    connection_id: Optional[UUID] = None
    settings: dict = Field(default_factory=dict)
    
    created_at: datetime
    updated_at: datetime


class CellExecuteRequest(BaseModel):
    """Request to execute a cell."""
    limit: int = Field(default=1000, le=10000, description="Max rows to return")
    timeout_seconds: int = Field(default=60, le=300, description="Query timeout")


class CellExecuteResponse(BaseModel):
    """Response from SQL cell execution."""
    cell_id: UUID
    status: str
    duration_ms: int
    row_count: int
    columns: List[dict]  # [{name, type}, ...]
    rows: List[dict]  # First N rows
    truncated: bool  # True if results were limited
    error: Optional[str] = None


class PythonExecuteRequest(BaseModel):
    """Request to execute a Python cell."""
    timeout_seconds: int = Field(default=60, le=300, description="Execution timeout")


class PythonOutput(BaseModel):
    """A rich output from Python execution."""
    type: str  # 'text', 'dataframe', 'image', 'error'
    data: Any
    name: Optional[str] = None
    # For dataframes
    columns: Optional[List[str]] = None
    shape: Optional[List[int]] = None
    truncated: Optional[bool] = None
    # For images
    format: Optional[str] = None


class PythonExecuteResponse(BaseModel):
    """Response from Python cell execution."""
    cell_id: UUID
    status: str  # 'success' or 'error'
    duration_ms: int
    stdout: str
    stderr: str
    result: Optional[Any] = None  # Last expression value
    outputs: List[dict] = Field(default_factory=list)  # Rich outputs
    variables: List[str] = Field(default_factory=list)  # New variables created
    error: Optional[str] = None
    traceback: Optional[str] = None


class VariableInfo(BaseModel):
    """Information about a variable in the Python session."""
    name: str
    type: str
    preview: str
    shape: Optional[List[int]] = None


class SessionVariablesResponse(BaseModel):
    """List of variables in the Python session."""
    notebook_id: UUID
    variables: List[VariableInfo]


# ============================================================================
# NOTEBOOK MODELS
# ============================================================================

class NotebookCreate(BaseModel):
    """Create a new notebook."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    folder: str = ""
    tags: List[str] = Field(default_factory=list)
    default_connection_id: Optional[UUID] = None


class NotebookUpdate(BaseModel):
    """Update a notebook."""
    name: Optional[str] = None
    description: Optional[str] = None
    folder: Optional[str] = None
    tags: Optional[List[str]] = None
    default_connection_id: Optional[UUID] = None


class NotebookResponse(BaseModel):
    """Notebook response (without cells)."""
    id: UUID
    name: str
    description: Optional[str] = None
    folder: str = ""
    tags: List[str] = Field(default_factory=list)
    default_connection_id: Optional[UUID] = None
    
    created_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    # Summary stats
    cell_count: int = 0


class NotebookDetailResponse(BaseModel):
    """Notebook with cells."""
    id: UUID
    name: str
    description: Optional[str] = None
    folder: str = ""
    tags: List[str] = Field(default_factory=list)
    default_connection_id: Optional[UUID] = None
    
    cells: List[CellResponse] = Field(default_factory=list)
    
    created_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class NotebookListResponse(BaseModel):
    """List of notebooks."""
    notebooks: List[NotebookResponse]
    total: int


# ============================================================================
# DATASET MODELS
# ============================================================================

class DatasetCreate(BaseModel):
    """Save cell results as dataset."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    format: str = Field(default="parquet", pattern="^(parquet|csv|json)$")


class DatasetResponse(BaseModel):
    """Saved dataset response."""
    id: UUID
    name: str
    description: Optional[str] = None
    
    source_notebook_id: Optional[UUID] = None
    source_cell_id: Optional[UUID] = None
    source_query: Optional[str] = None
    
    storage_uri: Optional[str] = None
    storage_format: str = "parquet"
    
    row_count: Optional[int] = None
    column_count: Optional[int] = None
    size_bytes: Optional[int] = None
    columns: List[dict] = Field(default_factory=list)
    
    created_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class DatasetListResponse(BaseModel):
    """List of datasets."""
    datasets: List[DatasetResponse]
    total: int
