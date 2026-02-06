"""Persona models."""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime
from enum import Enum


class PersonaStatus(str, Enum):
    """Persona status."""
    ACTIVE = "active"
    DRAFT = "draft"
    ARCHIVED = "archived"


class RoleType(str, Enum):
    """Common persona role types."""
    ANALYST = "analyst"
    ENGINEER = "engineer"
    SCIENTIST = "scientist"
    BUSINESS_USER = "business_user"
    ADMIN = "admin"
    VIEWER = "viewer"
    CUSTOM = "custom"


class Persona(BaseModel):
    """Persona definition."""
    id: UUID
    name: str
    description: Optional[str] = None
    status: PersonaStatus = PersonaStatus.DRAFT
    version: str = "1.0.0"

    # Role and organization
    role_type: Optional[RoleType] = None
    department: Optional[str] = None

    # Access patterns
    default_datasets: List[UUID] = Field(default_factory=list)
    default_tables: List[str] = Field(default_factory=list)  # ["schema.table", ...]
    allowed_classifications: List[str] = Field(default_factory=list)
    denied_classifications: List[str] = Field(default_factory=list)

    # Preferences
    preferences: Dict[str, Any] = Field(default_factory=dict)
    default_dashboard_id: Optional[UUID] = None
    pinned_queries: List[UUID] = Field(default_factory=list)
    favorite_tables: List[str] = Field(default_factory=list)

    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[UUID] = None
    org_id: Optional[UUID] = None

    class Config:
        from_attributes = True


class PersonaCreate(BaseModel):
    """Request to create a persona."""
    name: str
    description: Optional[str] = None
    role_type: Optional[RoleType] = None
    department: Optional[str] = None

    # Access patterns
    default_datasets: List[UUID] = Field(default_factory=list)
    default_tables: List[str] = Field(default_factory=list)
    allowed_classifications: List[str] = Field(default_factory=list)
    denied_classifications: List[str] = Field(default_factory=list)

    # Preferences
    preferences: Dict[str, Any] = Field(default_factory=dict)
    default_dashboard_id: Optional[UUID] = None

    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)


class PersonaUpdate(BaseModel):
    """Request to update a persona."""
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[PersonaStatus] = None
    role_type: Optional[RoleType] = None
    department: Optional[str] = None

    # Access patterns
    default_datasets: Optional[List[UUID]] = None
    default_tables: Optional[List[str]] = None
    allowed_classifications: Optional[List[str]] = None
    denied_classifications: Optional[List[str]] = None

    # Preferences
    preferences: Optional[Dict[str, Any]] = None
    default_dashboard_id: Optional[UUID] = None
    pinned_queries: Optional[List[UUID]] = None
    favorite_tables: Optional[List[str]] = None

    # Metadata
    metadata: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None


class PersonaVersion(BaseModel):
    """Persona version."""
    id: UUID
    persona_id: UUID
    version: str
    snapshot: Dict[str, Any] = Field(default_factory=dict)
    changes: Dict[str, Any] = Field(default_factory=dict)
    change_reason: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[UUID] = None

    class Config:
        from_attributes = True


class PersonaListResponse(BaseModel):
    """List of personas."""
    personas: List[Persona]
    total: int


class PersonaVersionListResponse(BaseModel):
    """List of persona versions."""
    versions: List[PersonaVersion]
    total: int


# ============================================================================
# PERSONA ASSIGNMENT MODELS
# ============================================================================

class PersonaAssignment(BaseModel):
    """Assignment of a persona to a user."""
    id: UUID
    persona_id: UUID
    user_id: UUID
    is_primary: bool = False
    assigned_by: Optional[UUID] = None
    assigned_at: datetime
    expires_at: Optional[datetime] = None
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class PersonaAssignmentCreate(BaseModel):
    """Request to assign a persona to a user."""
    persona_id: UUID
    user_id: UUID
    is_primary: bool = False
    expires_at: Optional[datetime] = None
    notes: Optional[str] = None


class PersonaAssignmentListResponse(BaseModel):
    """List of persona assignments."""
    assignments: List[PersonaAssignment]
    total: int


# ============================================================================
# ACCESS CHECK MODELS
# ============================================================================

class AccessCheckRequest(BaseModel):
    """Request to check if a persona has access to a resource."""
    persona_id: UUID
    resource_type: str  # dataset, table, dashboard
    resource_id: Optional[UUID] = None
    resource_ref: Optional[str] = None  # For tables: "schema.table"
    classification: Optional[str] = None  # Data classification level


class AccessCheckResult(BaseModel):
    """Result of access check."""
    allowed: bool
    persona_id: UUID
    resource_type: str
    resource_id: Optional[UUID] = None
    resource_ref: Optional[str] = None
    reason: Optional[str] = None  # Why access was allowed/denied
    matching_rules: List[str] = Field(default_factory=list)
