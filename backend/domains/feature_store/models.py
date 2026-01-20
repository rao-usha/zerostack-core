"""Pydantic models for feature store API."""
from pydantic import BaseModel, Field
from typing import Optional, List, Any
from uuid import UUID
from datetime import datetime
from enum import Enum


# ============================================================================
# Enums
# ============================================================================

class FeatureDataType(str, Enum):
    """Supported feature data types."""
    INT64 = "int64"
    FLOAT64 = "float64"
    STRING = "string"
    BOOL = "bool"
    DATETIME = "datetime"


class TransformationType(str, Enum):
    """Feature transformation types."""
    SQL = "sql"
    PYTHON = "python"


class ComputationMode(str, Enum):
    """How features are computed."""
    ON_DEMAND = "on_demand"
    SCHEDULED = "scheduled"


class FeatureStatus(str, Enum):
    """Feature lifecycle status."""
    DRAFT = "draft"
    ACTIVE = "active"
    DEPRECATED = "deprecated"


# ============================================================================
# Entity Models
# ============================================================================

class EntityBase(BaseModel):
    """Base entity model."""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    join_keys: List[str] = Field(..., min_items=1)  # ["user_id"] or ["user_id", "product_id"]


class EntityCreate(EntityBase):
    """Create entity request."""
    pass


class EntityUpdate(BaseModel):
    """Update entity request."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    join_keys: Optional[List[str]] = None


class Entity(EntityBase):
    """Entity response."""
    id: UUID
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str] = None

    class Config:
        from_attributes = True


# ============================================================================
# Feature Definition Models
# ============================================================================

class FeatureDefinitionBase(BaseModel):
    """Base feature definition model."""
    name: str = Field(..., min_length=1, max_length=255)
    entity_id: Optional[UUID] = None
    dtype: FeatureDataType
    transformation_type: TransformationType
    transformation_code: str = Field(..., min_length=1)
    source_table: Optional[str] = None
    description: Optional[str] = None
    owner: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    computation_mode: ComputationMode = ComputationMode.ON_DEMAND
    refresh_schedule: Optional[str] = None  # cron expression
    ttl_seconds: Optional[int] = None


class FeatureDefinitionCreate(FeatureDefinitionBase):
    """Create feature definition request."""
    pass


class FeatureDefinitionUpdate(BaseModel):
    """Update feature definition request (creates new version)."""
    transformation_code: Optional[str] = None
    description: Optional[str] = None
    owner: Optional[str] = None
    tags: Optional[List[str]] = None
    computation_mode: Optional[ComputationMode] = None
    refresh_schedule: Optional[str] = None
    ttl_seconds: Optional[int] = None
    status: Optional[FeatureStatus] = None


class FeatureDefinition(FeatureDefinitionBase):
    """Feature definition response."""
    id: UUID
    version: int
    status: FeatureStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class FeatureDefinitionWithEntity(FeatureDefinition):
    """Feature definition with entity details."""
    entity: Optional[Entity] = None


# ============================================================================
# Feature Set Models
# ============================================================================

class FeatureSetBase(BaseModel):
    """Base feature set model."""
    name: str = Field(..., min_length=1, max_length=255)
    entity_id: Optional[UUID] = None
    description: Optional[str] = None
    owner: Optional[str] = None
    tags: List[str] = Field(default_factory=list)


class FeatureSetCreate(FeatureSetBase):
    """Create feature set request."""
    feature_ids: List[UUID] = Field(default_factory=list)  # Initial features to add


class FeatureSetUpdate(BaseModel):
    """Update feature set request."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    owner: Optional[str] = None
    tags: Optional[List[str]] = None


class FeatureSet(FeatureSetBase):
    """Feature set response."""
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class FeatureSetWithFeatures(FeatureSet):
    """Feature set with included features."""
    features: List[FeatureDefinition] = Field(default_factory=list)
    feature_count: int = 0


# ============================================================================
# List Response Models
# ============================================================================

class EntityListResponse(BaseModel):
    """Paginated entity list."""
    items: List[Entity]
    total: int
    page: int
    page_size: int


class FeatureDefinitionListResponse(BaseModel):
    """Paginated feature definition list."""
    items: List[FeatureDefinition]
    total: int
    page: int
    page_size: int


class FeatureSetListResponse(BaseModel):
    """Paginated feature set list."""
    items: List[FeatureSet]
    total: int
    page: int
    page_size: int


# ============================================================================
# Action Models
# ============================================================================

class AddFeaturesToSetRequest(BaseModel):
    """Request to add features to a set."""
    feature_ids: List[UUID]


class RemoveFeaturesFromSetRequest(BaseModel):
    """Request to remove features from a set."""
    feature_ids: List[UUID]
