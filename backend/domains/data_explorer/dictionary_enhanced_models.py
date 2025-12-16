"""Enhanced Data Dictionary models for semantic metadata, relationships, and data quality."""
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from uuid import UUID, uuid4
from sqlmodel import SQLModel, Field as SQLField, Column, Relationship
from sqlalchemy.dialects.postgresql import JSONB, ARRAY, JSON, UUID as PG_UUID
from sqlalchemy import String, Text, Integer, Float, Boolean


class TrustTier(str, Enum):
    """Trust/certification level for data assets."""
    CERTIFIED = "certified"
    TRUSTED = "trusted"
    EXPERIMENTAL = "experimental"
    DEPRECATED = "deprecated"


class EntityRole(str, Enum):
    """Semantic role of a column."""
    PRIMARY_IDENTIFIER = "primary_identifier"
    FOREIGN_KEY = "foreign_key"
    MEASURE = "measure"
    DIMENSION = "dimension"
    STATUS_FLAG = "status_flag"
    TIMESTAMP = "timestamp"
    FREE_TEXT = "free_text"
    OTHER = "other"


class Cardinality(str, Enum):
    """Relationship cardinality."""
    ONE_TO_ONE = "one_to_one"
    ONE_TO_MANY = "one_to_many"
    MANY_TO_ONE = "many_to_one"
    MANY_TO_MANY = "many_to_many"
    UNKNOWN = "unknown"


class RelationshipConfidence(str, Enum):
    """Confidence level in relationship."""
    DECLARED = "declared"  # From foreign keys
    INFERRED = "inferred"  # From data patterns
    ASSUMED = "assumed"    # Manual/guessed


class DictionaryAsset(SQLModel, table=True):
    """Table-level metadata in the data dictionary."""
    __tablename__ = "dictionary_assets"
    
    # Primary key
    id: Optional[UUID] = SQLField(
        default_factory=uuid4,
        sa_column=Column(PG_UUID(as_uuid=True), primary_key=True)
    )
    
    # Asset identity
    connection_id: str = SQLField(max_length=100, index=True)
    schema_name: str = SQLField(max_length=255, index=True)
    table_name: str = SQLField(max_length=255, index=True)
    asset_type: str = SQLField(max_length=50, default="table")  # 'table' | 'view'
    
    # Business semantics
    business_name: Optional[str] = SQLField(default=None, max_length=255)
    business_definition: Optional[str] = None
    business_domain: Optional[str] = SQLField(default=None, max_length=100)  # Sales, Finance, etc.
    grain: Optional[str] = None  # "one row per..."
    row_meaning: Optional[str] = None  # Alternative to grain
    
    # Ownership
    owner: Optional[str] = SQLField(default=None, max_length=255)
    steward: Optional[str] = SQLField(default=None, max_length=255)
    tags: Optional[List[str]] = SQLField(default=None, sa_column=Column(JSONB))
    
    # Trust & quality
    trust_tier: str = SQLField(default="experimental", max_length=50)
    trust_score: int = SQLField(default=50)  # 0-100
    approved_for_reporting: bool = SQLField(default=False)
    approved_for_ml: bool = SQLField(default=False)
    known_issues: Optional[str] = None
    issue_tags: Optional[List[str]] = SQLField(default=None, sa_column=Column(JSONB))
    
    # Usage metrics (computed/aggregated)
    query_count_30d: int = SQLField(default=0)
    last_queried_at: Optional[datetime] = None
    
    # Technical metadata
    row_count_estimate: Optional[int] = None
    size_bytes: Optional[int] = None
    
    # Timestamps
    created_at: datetime = SQLField(default_factory=datetime.utcnow)
    updated_at: datetime = SQLField(default_factory=datetime.utcnow)


class DictionaryField(SQLModel, table=True):
    """Column-level metadata (complements existing data_dictionary_entries)."""
    __tablename__ = "dictionary_fields"
    
    # Primary key
    id: Optional[UUID] = SQLField(
        default_factory=uuid4,
        sa_column=Column(PG_UUID(as_uuid=True), primary_key=True)
    )
    
    # Foreign key to asset
    asset_id: UUID = SQLField(
        sa_column=Column(PG_UUID(as_uuid=True), index=True)
    )
    
    # Column identity
    column_name: str = SQLField(max_length=255, index=True)
    ordinal_position: Optional[int] = None
    
    # Technical details
    data_type: Optional[str] = SQLField(default=None, max_length=100)
    is_nullable: bool = SQLField(default=True)
    default_value: Optional[str] = None
    
    # Business semantics
    business_name: Optional[str] = SQLField(default=None, max_length=255)
    business_definition: Optional[str] = None
    entity_role: str = SQLField(default="other", max_length=50)
    tags: Optional[List[str]] = SQLField(default=None, sa_column=Column(JSONB))
    
    # Trust & quality
    trust_tier: str = SQLField(default="experimental", max_length=50)
    trust_score: int = SQLField(default=50)
    approved_for_reporting: bool = SQLField(default=False)
    approved_for_ml: bool = SQLField(default=False)
    known_issues: Optional[str] = None
    issue_tags: Optional[List[str]] = SQLField(default=None, sa_column=Column(JSONB))
    
    # Usage metrics
    query_count_30d: int = SQLField(default=0)
    last_queried_at: Optional[datetime] = None
    top_filters: Optional[List[Dict[str, Any]]] = SQLField(default=None, sa_column=Column(JSONB))
    top_group_bys: Optional[List[str]] = SQLField(default=None, sa_column=Column(JSONB))
    
    # Timestamps
    created_at: datetime = SQLField(default_factory=datetime.utcnow)
    updated_at: datetime = SQLField(default_factory=datetime.utcnow)


class DictionaryRelationship(SQLModel, table=True):
    """Explicit representation of table joins/relationships."""
    __tablename__ = "dictionary_relationships"
    
    # Primary key
    id: Optional[UUID] = SQLField(
        default_factory=uuid4,
        sa_column=Column(PG_UUID(as_uuid=True), primary_key=True)
    )
    
    # Connection context
    connection_id: str = SQLField(max_length=100, index=True)
    
    # Source (FK side typically)
    source_schema: str = SQLField(max_length=255, index=True)
    source_table: str = SQLField(max_length=255, index=True)
    source_column: str = SQLField(max_length=255)
    
    # Target (PK side typically)
    target_schema: str = SQLField(max_length=255, index=True)
    target_table: str = SQLField(max_length=255, index=True)
    target_column: str = SQLField(max_length=255)
    
    # Relationship metadata
    cardinality: str = SQLField(default="unknown", max_length=50)
    confidence: str = SQLField(default="assumed", max_length=50)
    notes: Optional[str] = None
    
    # Usage
    join_count_30d: int = SQLField(default=0)
    
    # Timestamps
    created_at: datetime = SQLField(default_factory=datetime.utcnow)
    updated_at: datetime = SQLField(default_factory=datetime.utcnow)


class DictionaryProfile(SQLModel, table=True):
    """Column-level profiling snapshots (append-only for history)."""
    __tablename__ = "dictionary_profiles"
    
    # Primary key
    id: Optional[UUID] = SQLField(
        default_factory=uuid4,
        sa_column=Column(PG_UUID(as_uuid=True), primary_key=True)
    )
    
    # Column identity
    connection_id: str = SQLField(max_length=100, index=True)
    schema_name: str = SQLField(max_length=255, index=True)
    table_name: str = SQLField(max_length=255, index=True)
    column_name: str = SQLField(max_length=255, index=True)
    
    # Table-level context
    row_count_estimate: Optional[int] = None
    
    # Completeness
    null_count: Optional[int] = None
    null_fraction: Optional[float] = None
    
    # Cardinality
    distinct_count: Optional[int] = None
    distinct_count_estimate: Optional[int] = None
    uniqueness_fraction: Optional[float] = None
    
    # Numeric stats (nullable, only for numeric columns)
    numeric_min: Optional[float] = None
    numeric_max: Optional[float] = None
    numeric_avg: Optional[float] = None
    numeric_stddev: Optional[float] = None
    numeric_median: Optional[float] = None
    
    # Categorical stats (nullable, only for low-cardinality columns)
    top_values: Optional[List[Dict[str, Any]]] = SQLField(
        default=None,
        sa_column=Column(JSONB)
    )  # [{"value": "foo", "count": 100, "fraction": 0.5}, ...]
    
    # String stats (nullable, only for text columns)
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    avg_length: Optional[float] = None
    
    # Temporal stats (nullable, only for date/timestamp columns)
    earliest_value: Optional[datetime] = None
    latest_value: Optional[datetime] = None
    
    # Profiling metadata
    sample_size: Optional[int] = None  # How many rows were sampled
    sample_method: Optional[str] = SQLField(default=None, max_length=50)  # 'full', 'sample', 'tablesample'
    profile_version: int = SQLField(default=1)
    computed_at: datetime = SQLField(default_factory=datetime.utcnow, index=True)


class DictionaryUsageLog(SQLModel, table=True):
    """Raw usage event log (optional, for detailed tracking)."""
    __tablename__ = "dictionary_usage_logs"
    
    id: Optional[UUID] = SQLField(
        default_factory=uuid4,
        sa_column=Column(PG_UUID(as_uuid=True), primary_key=True)
    )
    
    # Event details
    connection_id: str = SQLField(max_length=100, index=True)
    event_type: str = SQLField(max_length=50)  # 'query', 'chat', 'export', etc.
    
    # Referenced objects
    schemas_used: Optional[List[str]] = SQLField(default=None, sa_column=Column(JSONB))
    tables_used: Optional[List[str]] = SQLField(default=None, sa_column=Column(JSONB))
    columns_used: Optional[List[str]] = SQLField(default=None, sa_column=Column(JSONB))
    
    # Query context
    query_text: Optional[str] = None  # Store for analysis
    query_hash: Optional[str] = SQLField(default=None, max_length=64, index=True)
    
    # User context
    user_id: Optional[str] = SQLField(default=None, max_length=100)
    session_id: Optional[str] = SQLField(default=None, max_length=100)
    
    # Timestamps
    event_at: datetime = SQLField(default_factory=datetime.utcnow, index=True)


