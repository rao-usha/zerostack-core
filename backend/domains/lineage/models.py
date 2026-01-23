"""
Data Lineage Models

Tracks relationships between data entities (files, tables, datasets, models).
"""
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field
from sqlmodel import Column, DateTime, Field as SQLField, SQLModel, Text
from sqlalchemy.dialects.postgresql import JSONB


# --- Enums ---

class EntityType(str, Enum):
    """Types of data entities that can be tracked in lineage"""
    FILE = "file"
    FILE_TABLE = "file_table"
    DATABASE_TABLE = "database_table"
    DATASET = "dataset"
    NOTEBOOK = "notebook"
    QUERY = "query"
    MODEL = "model"
    REPORT = "report"
    NOTEBOOK_OUTPUT = "notebook_output"


class EdgeType(str, Enum):
    """Types of lineage relationships"""
    DERIVED_FROM = "derived_from"  # General derivation
    PUBLISHED = "published"  # File table published to dataset
    TRANSFORMED = "transformed"  # Data transformation applied
    JOINED = "joined"  # Multiple sources joined
    AGGREGATED = "aggregated"  # Data aggregated
    FILTERED = "filtered"  # Data filtered
    TRAINED_ON = "trained_on"  # ML model trained on dataset
    QUERIED_FROM = "queried_from"  # Query result from table


class ColumnTransformation(str, Enum):
    """Types of column-level transformations"""
    DIRECT = "direct"  # Direct copy
    CAST = "cast"  # Type conversion
    CALCULATED = "calculated"  # Computed from expression
    AGGREGATED = "aggregated"  # Aggregation (SUM, AVG, etc.)
    RENAMED = "renamed"  # Column renamed


# --- SQLModel Tables (Database) ---

class DataLineageEdge(SQLModel, table=True):
    """
    Represents a lineage relationship between two data entities.
    """
    __tablename__ = "data_lineage_edges"
    
    id: UUID = SQLField(default_factory=uuid4, primary_key=True)
    
    # Source entity
    source_type: EntityType = SQLField(nullable=False, index=True)
    source_id: UUID = SQLField(nullable=False, index=True)
    source_name: Optional[str] = SQLField(default=None, max_length=500)
    source_schema: Optional[str] = SQLField(default=None, max_length=200)
    
    # Target entity
    target_type: EntityType = SQLField(nullable=False, index=True)
    target_id: UUID = SQLField(nullable=False, index=True)
    target_name: Optional[str] = SQLField(default=None, max_length=500)
    target_schema: Optional[str] = SQLField(default=None, max_length=200)
    
    # Relationship details
    edge_type: EdgeType = SQLField(nullable=False, index=True)
    transform_sql: Optional[str] = SQLField(default=None, sa_column=Column(Text))
    transform_config: Optional[Dict[str, Any]] = SQLField(default=None, sa_column=Column(JSONB))
    
    # Metadata
    created_at: datetime = SQLField(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False)
    )
    created_by: Optional[UUID] = SQLField(default=None)
    
    # Data flow metrics
    source_row_count: Optional[int] = SQLField(default=None)
    target_row_count: Optional[int] = SQLField(default=None)
    source_column_count: Optional[int] = SQLField(default=None)
    target_column_count: Optional[int] = SQLField(default=None)


class DataLineageMetadata(SQLModel, table=True):
    """
    Summary statistics and metadata for each entity in the lineage graph.
    """
    __tablename__ = "data_lineage_metadata"
    
    entity_type: EntityType = SQLField(nullable=False, primary_key=True)
    entity_id: UUID = SQLField(nullable=False, primary_key=True)
    entity_name: Optional[str] = SQLField(default=None, max_length=500)
    
    # Lineage statistics
    upstream_count: int = SQLField(default=0, nullable=False)
    downstream_count: int = SQLField(default=0, nullable=False)
    total_upstream_count: int = SQLField(default=0, nullable=False)
    total_downstream_count: int = SQLField(default=0, nullable=False)
    lineage_depth: int = SQLField(default=0, nullable=False)
    
    # Freshness tracking
    last_refreshed_at: Optional[datetime] = SQLField(
        default=None, sa_column=Column(DateTime(timezone=True))
    )
    upstream_last_modified_at: Optional[datetime] = SQLField(
        default=None, sa_column=Column(DateTime(timezone=True))
    )
    is_stale: bool = SQLField(default=False, nullable=False)
    
    # Usage tracking
    access_count: int = SQLField(default=0, nullable=False)
    last_accessed_at: Optional[datetime] = SQLField(
        default=None, sa_column=Column(DateTime(timezone=True))
    )
    
    # Timestamps
    created_at: datetime = SQLField(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False)
    )
    updated_at: datetime = SQLField(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False)
    )


class DataLineageColumn(SQLModel, table=True):
    """
    Column-level lineage tracking (detailed mapping between columns).
    """
    __tablename__ = "data_lineage_columns"
    
    id: UUID = SQLField(default_factory=uuid4, primary_key=True)
    edge_id: UUID = SQLField(foreign_key="data_lineage_edges.id", nullable=False, index=True)
    
    # Source column
    source_column: str = SQLField(nullable=False, max_length=200)
    source_data_type: Optional[str] = SQLField(default=None, max_length=100)
    
    # Target column
    target_column: str = SQLField(nullable=False, max_length=200)
    target_data_type: Optional[str] = SQLField(default=None, max_length=100)
    
    # Transformation
    transformation: Optional[ColumnTransformation] = SQLField(default=None)
    transformation_expression: Optional[str] = SQLField(default=None, sa_column=Column(Text))
    
    created_at: datetime = SQLField(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False)
    )


# --- Pydantic Schemas (API Request/Response) ---

class LineageNode(BaseModel):
    """Represents a node in the lineage graph"""
    entity_type: EntityType
    entity_id: UUID
    entity_name: str
    schema_name: Optional[str] = None
    row_count: Optional[int] = None
    column_count: Optional[int] = None
    created_at: Optional[datetime] = None
    last_modified_at: Optional[datetime] = None
    
    # Computed fields
    is_source: bool = False  # True if this is an original data source
    is_sink: bool = False  # True if nothing derives from this
    depth: int = 0  # Distance from original source


class LineageEdgeResponse(BaseModel):
    """Represents an edge in the lineage graph"""
    id: UUID
    source_type: EntityType
    source_id: UUID
    source_name: Optional[str]
    target_type: EntityType
    target_id: UUID
    target_name: Optional[str]
    edge_type: EdgeType
    transform_sql: Optional[str]
    transform_config: Optional[Dict[str, Any]]
    created_at: datetime
    created_by: Optional[UUID]
    source_row_count: Optional[int]
    target_row_count: Optional[int]
    
    class Config:
        from_attributes = True


class ColumnLineage(BaseModel):
    """Column-level lineage mapping"""
    source_column: str
    source_data_type: Optional[str]
    target_column: str
    target_data_type: Optional[str]
    transformation: Optional[ColumnTransformation]
    transformation_expression: Optional[str]


class LineageGraphResponse(BaseModel):
    """Complete lineage graph for an entity"""
    center_node: LineageNode
    upstream_nodes: List[LineageNode] = []
    downstream_nodes: List[LineageNode] = []
    edges: List[LineageEdgeResponse] = []
    column_mappings: List[ColumnLineage] = []
    
    # Summary stats
    total_upstream_count: int = 0
    total_downstream_count: int = 0
    max_depth: int = 0


class LineageSummary(BaseModel):
    """Quick summary of lineage for an entity"""
    entity_type: EntityType
    entity_id: UUID
    entity_name: str
    
    # Direct relationships
    upstream_count: int = 0
    downstream_count: int = 0
    
    # Total (all ancestors/descendants)
    total_upstream_count: int = 0
    total_downstream_count: int = 0
    
    # Quick lists
    immediate_sources: List[str] = []  # Names of direct sources
    immediate_targets: List[str] = []  # Names of direct targets
    
    # Freshness
    is_stale: bool = False
    last_refreshed_at: Optional[datetime] = None


class CreateLineageRequest(BaseModel):
    """Request to create a lineage relationship"""
    source_type: EntityType
    source_id: UUID
    source_name: str
    target_type: EntityType
    target_id: UUID
    target_name: str
    edge_type: EdgeType
    transform_sql: Optional[str] = None
    transform_config: Optional[Dict[str, Any]] = None
    source_row_count: Optional[int] = None
    target_row_count: Optional[int] = None
    source_column_count: Optional[int] = None
    target_column_count: Optional[int] = None
    column_mappings: Optional[List[ColumnLineage]] = None


class LineageQueryRequest(BaseModel):
    """Request to query lineage"""
    entity_type: EntityType
    entity_id: UUID
    direction: str = Field(default="both", pattern="^(upstream|downstream|both)$")
    max_depth: int = Field(default=3, ge=1, le=10)
    include_columns: bool = False


class LineageImpactAnalysis(BaseModel):
    """Impact analysis result"""
    entity_type: EntityType
    entity_id: UUID
    entity_name: str
    
    affected_downstream_count: int = 0
    affected_entities: List[LineageNode] = []
    
    risk_level: str = "low"  # low, medium, high
    recommendations: List[str] = []


class LineageSearchRequest(BaseModel):
    """Search for entities in lineage"""
    search_term: str
    entity_types: Optional[List[EntityType]] = None
    limit: int = Field(default=50, ge=1, le=500)


class LineageSearchResult(BaseModel):
    """Search result for lineage entities"""
    entities: List[LineageNode] = []
    total_count: int = 0
