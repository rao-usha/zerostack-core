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


class Persona(BaseModel):
    """Persona definition."""
    id: UUID
    name: str
    description: Optional[str] = None
    status: PersonaStatus = PersonaStatus.DRAFT
    metadata: Dict[str, Any] = Field(default_factory=dict)
    version: str = "1.0.0"
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
    metadata: Dict[str, Any] = Field(default_factory=dict)


class PersonaUpdate(BaseModel):
    """Request to update a persona."""
    name: Optional[str] = None
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    status: Optional[PersonaStatus] = None


class PersonaVersion(BaseModel):
    """Persona version."""
    id: UUID
    persona_id: UUID
    version: str
    changes: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[UUID] = None

