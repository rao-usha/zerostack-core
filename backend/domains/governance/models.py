"""Governance models."""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime
from enum import Enum


class PolicyType(str, Enum):
    """Policy types."""
    DATA_ACCESS = "data_access"
    DATA_USAGE = "data_usage"
    QUALITY = "quality"
    PRIVACY = "privacy"
    RETENTION = "retention"


class PolicyStatus(str, Enum):
    """Policy status."""
    ACTIVE = "active"
    DRAFT = "draft"
    ARCHIVED = "archived"


class Policy(BaseModel):
    """Governance policy."""
    id: UUID
    name: str
    description: Optional[str] = None
    policy_type: PolicyType
    status: PolicyStatus = PolicyStatus.DRAFT
    rules: Dict[str, Any] = Field(default_factory=dict)  # Policy rules/conditions
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[UUID] = None
    org_id: Optional[UUID] = None
    
    class Config:
        from_attributes = True


class PolicyCreate(BaseModel):
    """Request to create a policy."""
    name: str
    description: Optional[str] = None
    policy_type: PolicyType
    rules: Dict[str, Any] = Field(default_factory=dict)


class ApprovalStatus(str, Enum):
    """Approval status."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class Approval(BaseModel):
    """Approval request."""
    id: UUID
    resource_type: str  # "dataset", "model", "persona", etc.
    resource_id: UUID
    action: str  # "create", "update", "delete", "access"
    requested_by: UUID
    status: ApprovalStatus = ApprovalStatus.PENDING
    approver: Optional[UUID] = None
    reason: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    reviewed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class ApprovalCreate(BaseModel):
    """Request to create an approval."""
    resource_type: str
    resource_id: UUID
    action: str
    reason: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AuditLogEntry(BaseModel):
    """Audit log entry."""
    id: UUID
    user_id: Optional[UUID] = None
    action: str
    resource_type: str
    resource_id: Optional[UUID] = None
    details: Dict[str, Any] = Field(default_factory=dict)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        from_attributes = True

