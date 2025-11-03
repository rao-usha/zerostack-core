"""Auth models."""
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from enum import Enum


class Role(str, Enum):
    """User roles."""
    ADMIN = "admin"
    DATA_SCIENTIST = "data_scientist"
    ANALYST = "analyst"
    VIEWER = "viewer"
    GUEST = "guest"


class User(BaseModel):
    """User model."""
    id: UUID
    email: EmailStr
    username: str
    full_name: Optional[str] = None
    role: Role = Role.VIEWER
    org_id: Optional[UUID] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    """Request to create a user."""
    email: EmailStr
    username: str
    password: str
    full_name: Optional[str] = None
    role: Role = Role.VIEWER
    org_id: Optional[UUID] = None


class UserLogin(BaseModel):
    """Login request."""
    email: EmailStr
    password: str


class Token(BaseModel):
    """Auth token."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class Organization(BaseModel):
    """Organization model."""
    id: UUID
    name: str
    slug: str
    description: Optional[str] = None
    metadata: dict = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        from_attributes = True


class OrganizationCreate(BaseModel):
    """Request to create an organization."""
    name: str
    slug: str
    description: Optional[str] = None


class APIToken(BaseModel):
    """API token for programmatic access."""
    id: UUID
    name: str
    token_prefix: str  # First few chars of token
    user_id: UUID
    org_id: Optional[UUID] = None
    expires_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True
    
    class Config:
        from_attributes = True


class APITokenCreate(BaseModel):
    """Request to create an API token."""
    name: str
    expires_in_days: Optional[int] = None

