"""MCP models."""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime
from enum import Enum


class MCPToolStatus(str, Enum):
    """MCP tool status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"


class MCPTool(BaseModel):
    """MCP tool definition."""
    id: UUID
    name: str
    description: Optional[str] = None
    tool_type: str  # e.g., "function", "command", "query"
    schema: Dict[str, Any] = Field(default_factory=dict)  # JSON schema for tool
    implementation: Optional[str] = None  # Path or reference to implementation
    status: MCPToolStatus = MCPToolStatus.INACTIVE
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        from_attributes = True


class MCPToolCreate(BaseModel):
    """Request to create an MCP tool."""
    name: str
    description: Optional[str] = None
    tool_type: str
    schema: Dict[str, Any] = Field(default_factory=dict)
    implementation: Optional[str] = None


class MCPToolExecution(BaseModel):
    """MCP tool execution."""
    id: UUID
    tool_id: UUID
    input: Dict[str, Any] = Field(default_factory=dict)
    output: Optional[Dict[str, Any]] = None
    status: str  # "pending", "running", "completed", "error"
    error: Optional[str] = None
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class MCPToolExecutionRequest(BaseModel):
    """Request to execute an MCP tool."""
    tool_id: UUID
    input: Dict[str, Any] = Field(default_factory=dict)

