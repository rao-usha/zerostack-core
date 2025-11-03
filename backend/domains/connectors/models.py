"""Connector models."""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, Literal
from uuid import UUID
from datetime import datetime
from enum import Enum


class ConnectorType(str, Enum):
    """Supported connector types."""
    POSTGRES = "postgres"
    SNOWFLAKE = "snowflake"
    S3 = "s3"
    HTTP = "http"
    FILE = "file"


class ConnectorStatus(str, Enum):
    """Connector status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"


class ConnectorConfig(BaseModel):
    """Connector configuration."""
    type: ConnectorType
    name: str
    config: Dict[str, Any] = Field(default_factory=dict)
    credentials: Optional[Dict[str, Any]] = None  # TODO: Encrypt in production


class Connector(BaseModel):
    """Connector instance."""
    id: UUID
    type: ConnectorType
    name: str
    status: ConnectorStatus = ConnectorStatus.INACTIVE
    config: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[UUID] = None
    
    class Config:
        from_attributes = True


class ConnectorCreate(BaseModel):
    """Request to create a connector."""
    type: ConnectorType
    name: str
    config: Dict[str, Any] = Field(default_factory=dict)


class ConnectorUpdate(BaseModel):
    """Request to update a connector."""
    name: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    status: Optional[ConnectorStatus] = None


class ConnectorTest(BaseModel):
    """Response from connector test."""
    success: bool
    message: str
    details: Optional[Dict[str, Any]] = None

