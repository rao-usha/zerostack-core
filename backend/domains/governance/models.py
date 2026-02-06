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


class Classification(str, Enum):
    """Data classification levels."""
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"
    PII = "pii"


class ComplianceFramework(str, Enum):
    """Compliance frameworks."""
    GDPR = "gdpr"
    HIPAA = "hipaa"
    CCPA = "ccpa"
    SOC2 = "soc2"
    PCI_DSS = "pci_dss"


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
    metadata: Dict[str, Any] = Field(default_factory=dict)


class PolicyUpdate(BaseModel):
    """Request to update a policy."""
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[PolicyStatus] = None
    rules: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


class PolicyListResponse(BaseModel):
    """List of policies."""
    policies: List[Policy]
    total: int


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
    resource_name: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    status: str = "success"
    error_message: Optional[str] = None
    compliance_tags: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True


class AuditLogCreate(BaseModel):
    """Request to create an audit log entry."""
    action: str
    resource_type: str
    resource_id: Optional[UUID] = None
    resource_name: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    status: str = "success"
    error_message: Optional[str] = None
    compliance_tags: List[str] = Field(default_factory=list)


class AuditLogListResponse(BaseModel):
    """List of audit log entries."""
    entries: List[AuditLogEntry]
    total: int


class ApprovalListResponse(BaseModel):
    """List of approvals."""
    approvals: List[Approval]
    total: int


class ApprovalReview(BaseModel):
    """Request to review an approval."""
    status: ApprovalStatus
    reason: Optional[str] = None


# ============================================================================
# DATA CLASSIFICATION MODELS
# ============================================================================

class DataClassification(BaseModel):
    """Data classification for a resource."""
    id: UUID
    resource_type: str
    resource_id: UUID
    resource_path: Optional[str] = None
    classification: Classification
    sub_classification: Optional[str] = None
    compliance_tags: List[str] = Field(default_factory=list)
    retention_days: Optional[int] = None
    classified_by: Optional[UUID] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DataClassificationCreate(BaseModel):
    """Request to classify data."""
    resource_type: str
    resource_id: UUID
    resource_path: Optional[str] = None
    classification: Classification
    sub_classification: Optional[str] = None
    compliance_tags: List[str] = Field(default_factory=list)
    retention_days: Optional[int] = None
    notes: Optional[str] = None


class DataClassificationListResponse(BaseModel):
    """List of data classifications."""
    classifications: List[DataClassification]
    total: int


# ============================================================================
# COMPLIANCE REPORTING MODELS
# ============================================================================

class ComplianceCheckResult(BaseModel):
    """Result of a single compliance check."""
    check_name: str
    description: str
    status: str  # passed, failed, warning, not_applicable
    details: Optional[str] = None
    affected_resources: List[str] = Field(default_factory=list)
    recommendation: Optional[str] = None


class ComplianceFrameworkReport(BaseModel):
    """Compliance report for a single framework."""
    framework: ComplianceFramework
    overall_status: str  # compliant, non_compliant, partial, not_assessed
    compliance_score: float  # 0-100
    checks: List[ComplianceCheckResult]
    last_assessed: datetime


class ComplianceReportResponse(BaseModel):
    """Full compliance report."""
    report_id: UUID
    generated_at: datetime
    frameworks: List[ComplianceFrameworkReport]
    summary: Dict[str, Any]  # {total_checks, passed, failed, warnings}
    recommendations: List[str] = Field(default_factory=list)


class PolicyEvaluationRequest(BaseModel):
    """Request to evaluate policies against a resource/action."""
    resource_type: str
    resource_id: UUID
    action: str
    context: Dict[str, Any] = Field(default_factory=dict)


class PolicyEvaluationResult(BaseModel):
    """Result of policy evaluation."""
    allowed: bool
    matching_policies: List[Policy] = Field(default_factory=list)
    required_approvals: bool = False
    denial_reason: Optional[str] = None
    actions_triggered: List[str] = Field(default_factory=list)  # ["log", "notify", "require_approval"]

