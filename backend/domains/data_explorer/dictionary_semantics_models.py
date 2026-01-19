"""Models for dictionary semantics, grains, and relationships."""
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, validator
from sqlmodel import SQLModel, Field as SQLField, Column
from sqlalchemy.dialects.postgresql import JSONB, ARRAY, UUID as PG_UUID
from sqlalchemy import String, Text


# ==================== Enums ====================

class EntryType(str, Enum):
    """Type of dictionary entry."""
    DATABASE = "database"
    SCHEMA = "schema"
    TABLE = "table"
    COLUMN = "column"
    CONCEPT = "concept"


class RelationshipKind(str, Enum):
    """Kind of relationship."""
    CANDIDATE = "candidate"
    SEMANTIC = "semantic"


class RelationshipStatus(str, Enum):
    """Status of relationship."""
    SUGGESTED = "suggested"
    APPROVED = "approved"
    REJECTED = "rejected"
    DEPRECATED = "deprecated"


class CandidateRelationshipType(str, Enum):
    """Types for candidate relationships."""
    FOREIGN_KEY_LIKE = "foreign_key_like"
    JOIN_KEY = "join_key"
    BRIDGE = "bridge"
    SCD2_LINK = "scd2_link"


class SemanticRelationshipType(str, Enum):
    """Types for semantic relationships."""
    DERIVED_FROM = "derived_from"
    ROLLS_UP_TO = "rolls_up_to"
    DEPENDS_ON = "depends_on"
    IS_ALIAS_OF = "is_alias_of"
    MAPS_TO_EXTERNAL = "maps_to_external"
    SCD2 = "scd2"


class Cardinality(str, Enum):
    """Relationship cardinality."""
    ONE_TO_ONE = "one_to_one"
    ONE_TO_MANY = "one_to_many"
    MANY_TO_ONE = "many_to_one"
    MANY_TO_MANY = "many_to_many"


# ==================== Pydantic Models for JSON Blocks ====================

class Consumer(BaseModel):
    """Consumer of a data asset."""
    role: str
    team: Optional[str] = None
    system: Optional[str] = None


class DecisionContext(BaseModel):
    """Decision context for a dictionary entry."""
    primary_decisions: List[str] = Field(default_factory=list)
    secondary_decisions: List[str] = Field(default_factory=list)
    consumers: List[Consumer] = Field(default_factory=list)
    decision_frequency: Optional[str] = None  # daily, weekly, monthly, ad_hoc
    downside_if_wrong: Optional[str] = None
    notes: Optional[str] = None
    
    class Config:
        extra = "allow"  # Forward compatibility


class TemporalBehavior(BaseModel):
    """Temporal behavior of data."""
    freshness: Optional[str] = None
    backfill_expected: bool = False
    late_arriving_data: Optional[bool] = None
    
    class Config:
        extra = "allow"


class AggregationRules(BaseModel):
    """Aggregation rules for data."""
    allowed: List[str] = Field(default_factory=list)
    forbidden: List[str] = Field(default_factory=list)
    
    class Config:
        extra = "allow"


class PIIInfo(BaseModel):
    """PII information."""
    contains_pii: bool = False
    pii_types: List[str] = Field(default_factory=list)
    
    class Config:
        extra = "allow"


class SemanticGuarantees(BaseModel):
    """Semantic guarantees for a dictionary entry."""
    invariants: List[str] = Field(default_factory=list)
    temporal_behavior: Optional[TemporalBehavior] = None
    aggregation_rules: Optional[AggregationRules] = None
    known_failure_modes: List[str] = Field(default_factory=list)
    pii: Optional[PIIInfo] = None
    notes: Optional[str] = None
    
    class Config:
        extra = "allow"


class ValidationState(BaseModel):
    """Validation state for a dictionary entry."""
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    confidence_sources: List[str] = Field(default_factory=list)  # ai_inferred, sme_reviewed, system_generated
    last_validated_at: Optional[datetime] = None
    validated_by: List[str] = Field(default_factory=list)
    upstream_sources: List[str] = Field(default_factory=list)
    downstream_usage: List[str] = Field(default_factory=list)
    notes: Optional[str] = None
    
    class Config:
        extra = "allow"
    
    @validator('confidence_score')
    def validate_confidence(cls, v):
        if v is not None and (v < 0.0 or v > 1.0):
            raise ValueError('confidence_score must be between 0.0 and 1.0')
        return v


class GrainCompatibility(BaseModel):
    """Grain compatibility information for relationships."""
    join_type: Optional[str] = None
    safe_aggregations: List[str] = Field(default_factory=list)
    unsafe_patterns: List[str] = Field(default_factory=list)
    
    class Config:
        extra = "allow"


class EnforcementInfo(BaseModel):
    """Enforcement information for semantic relationships."""
    method: Optional[str] = None
    frequency: Optional[str] = None
    
    class Config:
        extra = "allow"


class SemanticDefinition(BaseModel):
    """Semantic definition for relationships."""
    inputs: List[str] = Field(default_factory=list)  # Entry IDs or names
    formula: Optional[str] = None
    tolerance: Optional[float] = None
    enforcement: Optional[EnforcementInfo] = None
    
    class Config:
        extra = "allow"


# ==================== SQLModel Tables ====================

class DictionaryEntry(SQLModel, table=True):
    """Unified dictionary entry for all asset types."""
    __tablename__ = "dictionary_entries"
    
    id: Optional[UUID] = SQLField(
        default_factory=uuid4,
        sa_column=Column(PG_UUID(as_uuid=True), primary_key=True)
    )
    
    # Entry identification
    entry_type: str = SQLField(max_length=50, index=True)
    database_name: Optional[str] = SQLField(default=None, max_length=255, index=True)
    schema_name: Optional[str] = SQLField(default=None, max_length=255, index=True)
    table_name: Optional[str] = SQLField(default=None, max_length=255, index=True)
    column_name: Optional[str] = SQLField(default=None, max_length=255, index=True)
    concept_name: Optional[str] = SQLField(default=None, max_length=255, index=True)
    
    # Basic metadata
    title: str = SQLField(max_length=500)
    description: Optional[str] = None
    tags: Optional[List[str]] = SQLField(default=None, sa_column=Column(ARRAY(String)))
    
    # Timestamps
    created_at: datetime = SQLField(default_factory=datetime.utcnow)
    updated_at: datetime = SQLField(default_factory=datetime.utcnow)


class DictionaryEntryVersion(SQLModel, table=True):
    """Version history for dictionary entries."""
    __tablename__ = "dictionary_entry_versions"
    
    id: Optional[UUID] = SQLField(
        default_factory=uuid4,
        sa_column=Column(PG_UUID(as_uuid=True), primary_key=True)
    )
    entry_id: UUID = SQLField(sa_column=Column(PG_UUID(as_uuid=True), index=True))
    version: int = SQLField(index=True)
    snapshot: Dict[str, Any] = SQLField(sa_column=Column(JSONB))
    created_at: datetime = SQLField(default_factory=datetime.utcnow)


class DictionaryEntrySemantics(SQLModel, table=True):
    """Semantics block for dictionary entries."""
    __tablename__ = "dictionary_entry_semantics"
    
    entry_id: UUID = SQLField(
        sa_column=Column(PG_UUID(as_uuid=True), primary_key=True)
    )
    decision_context: Dict[str, Any] = SQLField(
        default_factory=dict,
        sa_column=Column(JSONB)
    )
    semantic_guarantees: Dict[str, Any] = SQLField(
        default_factory=dict,
        sa_column=Column(JSONB)
    )
    validation_state: Dict[str, Any] = SQLField(
        default_factory=dict,
        sa_column=Column(JSONB)
    )
    updated_at: datetime = SQLField(default_factory=datetime.utcnow)


class DictionaryGrain(SQLModel, table=True):
    """Grain definition for dictionary entries."""
    __tablename__ = "dictionary_grains"
    
    id: Optional[UUID] = SQLField(
        default_factory=uuid4,
        sa_column=Column(PG_UUID(as_uuid=True), primary_key=True)
    )
    entry_id: UUID = SQLField(
        sa_column=Column(PG_UUID(as_uuid=True), index=True, unique=True)
    )
    entity: str
    primary_key: Optional[List[str]] = SQLField(default=None, sa_column=Column(ARRAY(String)))
    time_grain: Optional[str] = SQLField(default=None, max_length=100)
    natural_key: Optional[List[str]] = SQLField(default=None, sa_column=Column(ARRAY(String)))
    notes: Optional[str] = None
    created_at: datetime = SQLField(default_factory=datetime.utcnow)
    updated_at: datetime = SQLField(default_factory=datetime.utcnow)


class DictionaryRelationship(SQLModel, table=True):
    """Relationships between dictionary entries."""
    __tablename__ = "dictionary_relationships"
    
    id: Optional[UUID] = SQLField(
        default_factory=uuid4,
        sa_column=Column(PG_UUID(as_uuid=True), primary_key=True)
    )
    
    # Relationship metadata
    relationship_kind: str = SQLField(max_length=50, index=True)  # candidate, semantic
    status: str = SQLField(default="suggested", max_length=50, index=True)
    
    # Connected entries
    left_entry_id: UUID = SQLField(sa_column=Column(PG_UUID(as_uuid=True), index=True))
    right_entry_id: UUID = SQLField(sa_column=Column(PG_UUID(as_uuid=True), index=True))
    left_ref: Optional[Dict[str, Any]] = SQLField(default=None, sa_column=Column(JSONB))
    right_ref: Optional[Dict[str, Any]] = SQLField(default=None, sa_column=Column(JSONB))
    
    # Relationship details
    relationship_type: str = SQLField(max_length=100, index=True)
    cardinality: Optional[str] = SQLField(default=None, max_length=50)
    
    # Candidate relationship stats
    match_rate_sample: Optional[float] = None
    left_null_rate: Optional[float] = None
    right_unique: Optional[bool] = None
    suggested_join_sql: Optional[str] = None
    
    # Semantic blocks
    grain_compatibility: Dict[str, Any] = SQLField(
        default_factory=dict,
        sa_column=Column(JSONB)
    )
    semantic_definition: Dict[str, Any] = SQLField(
        default_factory=dict,
        sa_column=Column(JSONB)
    )
    
    # Metadata
    confidence_score: Optional[float] = None
    created_by: Optional[str] = SQLField(default=None, max_length=255)
    created_at: datetime = SQLField(default_factory=datetime.utcnow)
    updated_at: datetime = SQLField(default_factory=datetime.utcnow)


class DictionaryInferenceJob(SQLModel, table=True):
    """Job for inferring relationships."""
    __tablename__ = "dictionary_inference_jobs"
    
    id: Optional[UUID] = SQLField(
        default_factory=uuid4,
        sa_column=Column(PG_UUID(as_uuid=True), primary_key=True)
    )
    
    # Job configuration
    connection_id: str = SQLField(max_length=100)
    schema_name: Optional[str] = SQLField(default=None, max_length=255)
    include_tables: Optional[List[str]] = SQLField(default=None, sa_column=Column(ARRAY(String)))
    exclude_tables: Optional[List[str]] = SQLField(default=None, sa_column=Column(ARRAY(String)))
    max_samples: int = SQLField(default=1000)
    
    # Job status
    status: str = SQLField(default="pending", max_length=50, index=True)
    progress: int = SQLField(default=0)
    current_stage: Optional[str] = SQLField(default=None, max_length=255)
    
    # Results
    relationships_found: int = SQLField(default=0)
    tables_scanned: int = SQLField(default=0)
    error_message: Optional[str] = None
    result_summary: Optional[Dict[str, Any]] = SQLField(default=None, sa_column=Column(JSONB))
    
    # Timestamps
    created_at: datetime = SQLField(default_factory=datetime.utcnow, index=True)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

