"""Context engine models."""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime
from enum import Enum


class ContextType(str, Enum):
    """Context types."""
    DATASET = "dataset"
    MODEL = "model"
    PIPELINE = "pipeline"
    EXPERIMENT = "experiment"


class Version(BaseModel):
    """Version information."""
    id: UUID
    context_id: UUID
    version: str  # Semantic version or commit hash
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[UUID] = None
    
    class Config:
        from_attributes = True


class LineageNode(BaseModel):
    """Lineage node."""
    id: UUID
    type: ContextType
    name: str
    version: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class LineageEdge(BaseModel):
    """Lineage edge (relationship)."""
    source_id: UUID
    target_id: UUID
    relationship: str  # e.g., "derived_from", "trained_on", "uses"
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Lineage(BaseModel):
    """Data lineage graph."""
    nodes: List[LineageNode] = Field(default_factory=list)
    edges: List[LineageEdge] = Field(default_factory=list)


class Snapshot(BaseModel):
    """Context snapshot."""
    id: UUID
    context_id: UUID
    version_id: Optional[UUID] = None
    snapshot_type: str  # "full", "incremental", "point_in_time"
    data: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        from_attributes = True


class ContextStore(BaseModel):
    """Context store entry."""
    id: UUID
    context_id: UUID
    context_type: ContextType
    key: str
    value: Any
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

