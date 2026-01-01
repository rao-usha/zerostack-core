"""
Models for Data Dictionary Relationship Intelligence.

Stores discovered and curated relationships between data assets.
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum


# ============================================================================
# Enums
# ============================================================================

class AssetType(str, Enum):
    """Type of data asset in a relationship."""
    table = "table"
    column = "column"


class RelationshipType(str, Enum):
    """Type of relationship between assets."""
    foreign_key_like = "foreign_key_like"  # High confidence PK/FK match
    semantic_equivalent = "semantic_equivalent"  # Same concept, different naming
    derived_from = "derived_from"  # Column appears to be derived/transformed
    joins_well_with = "joins_well_with"  # Statistically strong join candidate
    references = "references"  # Weak or partial reference


class RelationshipStatus(str, Enum):
    """Curation status of a relationship."""
    suggested = "suggested"  # Auto-discovered, awaiting review
    accepted = "accepted"  # Human-approved
    rejected = "rejected"  # Human-rejected


class DiscoveryJobStatus(str, Enum):
    """Status of a relationship discovery job."""
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"


# ============================================================================
# Evidence Schema (stored in JSONB)
# ============================================================================

class NameSimilarityEvidence(BaseModel):
    """Evidence from name-based matching."""
    normalized_from: str
    normalized_to: str
    similarity_score: float  # 0.0-1.0
    match_type: str  # exact | prefix_suffix | stem | fuzzy
    
    model_config = ConfigDict(extra='allow')


class TypeCompatibilityEvidence(BaseModel):
    """Evidence from data type compatibility."""
    from_type: str
    to_type: str
    compatible: bool
    compatibility_reason: Optional[str] = None
    
    model_config = ConfigDict(extra='allow')


class CardinalityEvidence(BaseModel):
    """Evidence from cardinality analysis."""
    from_total_rows: int
    from_distinct_count: int
    from_null_count: int
    from_uniqueness: float  # 0.0-1.0
    
    to_total_rows: int
    to_distinct_count: int
    to_null_count: int
    to_uniqueness: float
    
    inferred_cardinality: str  # one_to_one | one_to_many | many_to_one | many_to_many
    sample_size: int
    
    model_config = ConfigDict(extra='allow')


class ValueOverlapEvidence(BaseModel):
    """Evidence from value overlap analysis."""
    sample_size: int
    from_sample_size: int
    to_sample_size: int
    
    overlap_count: int
    overlap_percentage: float  # 0.0-100.0
    
    from_null_count: int
    to_null_count: int
    
    examples: List[str] = Field(default_factory=list, max_length=5)
    
    model_config = ConfigDict(extra='allow')


class RelationshipEvidence(BaseModel):
    """Complete evidence bundle for a relationship."""
    signals_fired: List[str] = Field(default_factory=list)  # Which detection signals fired
    
    name_similarity: Optional[NameSimilarityEvidence] = None
    type_compatibility: Optional[TypeCompatibilityEvidence] = None
    cardinality: Optional[CardinalityEvidence] = None
    value_overlap: Optional[ValueOverlapEvidence] = None
    
    additional_notes: Optional[str] = None
    
    model_config = ConfigDict(extra='allow')


# ============================================================================
# Base Models
# ============================================================================

class DictionaryRelationshipBase(BaseModel):
    """Base model for dictionary relationships."""
    # Source asset
    from_asset_type: AssetType
    from_database: str
    from_schema: str
    from_table: str
    from_column: Optional[str] = None
    
    # Target asset
    to_asset_type: AssetType
    to_database: str
    to_schema: str
    to_table: str
    to_column: Optional[str] = None
    
    # Relationship metadata
    relationship_type: RelationshipType
    confidence: float = Field(ge=0.0, le=1.0)
    
    # Evidence
    evidence: Dict[str, Any] = Field(default_factory=dict)
    explanation: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())


class DictionaryRelationshipCreate(DictionaryRelationshipBase):
    """Schema for creating a relationship."""
    id: Optional[str] = None
    generated_by: str = "system"
    status: RelationshipStatus = RelationshipStatus.suggested


class DictionaryRelationshipUpdate(BaseModel):
    """Schema for updating a relationship."""
    relationship_type: Optional[RelationshipType] = None
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    evidence: Optional[Dict[str, Any]] = None
    explanation: Optional[str] = None
    status: Optional[RelationshipStatus] = None
    
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())


class DictionaryRelationship(DictionaryRelationshipBase):
    """Full relationship model with all fields."""
    id: str
    
    generated_by: str
    status: RelationshipStatus
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())


# ============================================================================
# Discovery Job Models
# ============================================================================

class DiscoveryConfig(BaseModel):
    """Configuration for relationship discovery."""
    sample_size: int = Field(default=10000, ge=100, le=100000)
    min_confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    
    # Which relationship types to discover
    discover_foreign_key_like: bool = True
    discover_semantic_equivalent: bool = True
    discover_derived_from: bool = False  # More expensive
    discover_joins_well_with: bool = True
    discover_references: bool = True
    
    # Name matching thresholds
    name_similarity_threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    
    # Value overlap thresholds
    min_overlap_percentage: float = Field(default=50.0, ge=0.0, le=100.0)
    
    # Performance limits
    max_tables_to_scan: Optional[int] = Field(default=100, ge=1)
    timeout_seconds: int = Field(default=300, ge=30, le=3600)
    
    model_config = ConfigDict(extra='allow')


class DiscoveryJobCreate(BaseModel):
    """Schema for creating a discovery job."""
    connection_id: str
    scope_database: Optional[str] = None
    scope_schema: Optional[str] = None
    scope_tables: Optional[List[str]] = None
    
    config: DiscoveryConfig = Field(default_factory=DiscoveryConfig)
    started_by: Optional[str] = None


class DiscoveryJobSummary(BaseModel):
    """Summary statistics for a discovery job."""
    tables_scanned: int = 0
    columns_analyzed: int = 0
    relationships_found: int = 0
    relationships_by_type: Dict[str, int] = Field(default_factory=dict)
    avg_confidence: float = 0.0
    duration_seconds: float = 0.0
    
    model_config = ConfigDict(extra='allow')


class DiscoveryJob(BaseModel):
    """Full discovery job model."""
    id: str
    connection_id: str
    scope_database: Optional[str] = None
    scope_schema: Optional[str] = None
    scope_tables: Optional[List[str]] = None
    
    status: DiscoveryJobStatus
    progress: int = Field(ge=0, le=100)
    
    config: Dict[str, Any] = Field(default_factory=dict)
    results_summary: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    
    started_by: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())


# ============================================================================
# Request/Response Models
# ============================================================================

class RelationshipAcceptRequest(BaseModel):
    """Request to accept a relationship."""
    reviewed_by: Optional[str] = None


class RelationshipRejectRequest(BaseModel):
    """Request to reject a relationship."""
    reviewed_by: Optional[str] = None
    reason: Optional[str] = None


class RelationshipListResponse(BaseModel):
    """Response for listing relationships."""
    relationships: List[DictionaryRelationship]
    total: int
    
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())


class AssetRelationshipsResponse(BaseModel):
    """Relationships for a specific asset."""
    asset_identifier: str
    incoming_relationships: List[DictionaryRelationship] = Field(default_factory=list)
    outgoing_relationships: List[DictionaryRelationship] = Field(default_factory=list)
    total_incoming: int = 0
    total_outgoing: int = 0
    
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())


