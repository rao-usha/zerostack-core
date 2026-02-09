"""Governance API router - policies, approvals, audit logging, and compliance."""
import logging
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query, Depends, Request
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from core.config import settings
from core.rbac import require_admin, require_role
from domains.auth.models import User, Role
from .models import (
    Policy, PolicyCreate, PolicyUpdate, PolicyType, PolicyStatus, PolicyListResponse,
    Approval, ApprovalCreate, ApprovalStatus, ApprovalListResponse, ApprovalReview,
    AuditLogEntry, AuditLogCreate, AuditLogListResponse,
    DataClassification, DataClassificationCreate, DataClassificationListResponse, Classification,
    PolicyEvaluationRequest, PolicyEvaluationResult,
    ComplianceFramework, ComplianceReportResponse
)
from .service import (
    PolicyService, ApprovalService, AuditLogService,
    DataClassificationService, ComplianceService
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/governance", tags=["governance"])


# ============================================================================
# SESSION DEPENDENCY
# ============================================================================

async def get_async_session():
    """Get async database session."""
    async_url = settings.database_url.replace('postgresql+psycopg', 'postgresql+asyncpg')
    if 'asyncpg' not in async_url:
        async_url = settings.database_url.replace('postgresql://', 'postgresql+asyncpg://')

    engine = create_async_engine(async_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        yield session
        await session.commit()


# ============================================================================
# POLICY ENDPOINTS
# ============================================================================

@router.post("/policies", response_model=Policy, status_code=201)
async def create_policy(
    policy: PolicyCreate,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(require_admin)
):
    """Create a governance policy.

    Requires admin role.

    Policies define rules for data access, usage, privacy, quality, and retention.

    Example rules structure:
    ```json
    {
      "conditions": [{"field": "classification", "operator": "eq", "value": "pii"}],
      "actions": ["require_approval", "log_access"],
      "applies_to": {"resource_types": ["dataset", "table"], "tags": ["sensitive"]}
    }
    ```
    """
    service = PolicyService(session)
    return await service.create_policy(policy)


@router.get("/policies", response_model=PolicyListResponse)
async def list_policies(
    policy_type: Optional[PolicyType] = Query(None, description="Filter by policy type"),
    status: Optional[PolicyStatus] = Query(None, description="Filter by status"),
    session: AsyncSession = Depends(get_async_session)
):
    """List all governance policies."""
    service = PolicyService(session)
    policies = await service.list_policies(policy_type=policy_type, status=status)
    return PolicyListResponse(policies=policies, total=len(policies))


@router.get("/policies/{policy_id}", response_model=Policy)
async def get_policy(
    policy_id: UUID,
    session: AsyncSession = Depends(get_async_session)
):
    """Get a specific policy by ID."""
    service = PolicyService(session)
    policy = await service.get_policy(policy_id)
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    return policy


@router.patch("/policies/{policy_id}", response_model=Policy)
async def update_policy(
    policy_id: UUID,
    updates: PolicyUpdate,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(require_admin)
):
    """Update a policy.

    Requires admin role.
    All fields are optional. Use status to activate, deactivate, or archive policies.
    """
    service = PolicyService(session)

    # Check exists
    existing = await service.get_policy(policy_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Policy not found")

    return await service.update_policy(policy_id, updates)


@router.delete("/policies/{policy_id}", status_code=204)
async def delete_policy(
    policy_id: UUID,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(require_admin)
):
    """Delete (archive) a policy.

    Requires admin role.
    Policies are soft-deleted by changing status to 'archived'.
    """
    service = PolicyService(session)
    success = await service.delete_policy(policy_id)
    if not success:
        raise HTTPException(status_code=404, detail="Policy not found")


@router.post("/policies/evaluate", response_model=PolicyEvaluationResult)
async def evaluate_policies(
    request: PolicyEvaluationRequest,
    session: AsyncSession = Depends(get_async_session)
):
    """Evaluate all active policies against a resource/action.

    Returns whether the action is allowed, which policies matched,
    and what actions (like approvals) are required.
    """
    service = PolicyService(session)
    return await service.evaluate_policies(request)


# ============================================================================
# APPROVAL ENDPOINTS
# ============================================================================

@router.post("/approvals", response_model=Approval, status_code=201)
async def create_approval(
    approval: ApprovalCreate,
    requested_by: UUID = Query(..., description="User ID requesting approval"),
    session: AsyncSession = Depends(get_async_session)
):
    """Create an approval request.

    Use this when a policy requires approval for a data access or action.
    """
    service = ApprovalService(session)
    return await service.create_approval(approval, requested_by=requested_by)


@router.get("/approvals", response_model=ApprovalListResponse)
async def list_approvals(
    status: Optional[ApprovalStatus] = Query(None, description="Filter by status"),
    resource_type: Optional[str] = Query(None, description="Filter by resource type"),
    requested_by: Optional[UUID] = Query(None, description="Filter by requester"),
    session: AsyncSession = Depends(get_async_session)
):
    """List approval requests."""
    service = ApprovalService(session)
    approvals = await service.list_approvals(
        status=status,
        resource_type=resource_type,
        requested_by=requested_by
    )
    return ApprovalListResponse(approvals=approvals, total=len(approvals))


@router.get("/approvals/{approval_id}", response_model=Approval)
async def get_approval(
    approval_id: UUID,
    session: AsyncSession = Depends(get_async_session)
):
    """Get a specific approval request."""
    service = ApprovalService(session)
    approval = await service.get_approval(approval_id)
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")
    return approval


@router.post("/approvals/{approval_id}/review", response_model=Approval)
async def review_approval(
    approval_id: UUID,
    review: ApprovalReview,
    approver_id: UUID = Query(..., description="User ID of the approver"),
    session: AsyncSession = Depends(get_async_session)
):
    """Review (approve or reject) an approval request."""
    service = ApprovalService(session)

    # Check exists
    existing = await service.get_approval(approval_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Approval not found")

    if existing.status != ApprovalStatus.PENDING:
        raise HTTPException(status_code=400, detail="Approval is not pending")

    try:
        return await service.review_approval(
            approval_id=approval_id,
            approver_id=approver_id,
            status=review.status,
            reason=review.reason
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/approvals/{approval_id}/cancel", response_model=Approval)
async def cancel_approval(
    approval_id: UUID,
    session: AsyncSession = Depends(get_async_session)
):
    """Cancel a pending approval request."""
    service = ApprovalService(session)

    existing = await service.get_approval(approval_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Approval not found")

    if existing.status != ApprovalStatus.PENDING:
        raise HTTPException(status_code=400, detail="Only pending approvals can be cancelled")

    return await service.cancel_approval(approval_id)


# ============================================================================
# AUDIT LOG ENDPOINTS
# ============================================================================

@router.post("/audit-log", response_model=AuditLogEntry, status_code=201)
async def create_audit_entry(
    entry: AuditLogCreate,
    request: Request,
    user_id: Optional[UUID] = Query(None, description="User performing the action"),
    session: AsyncSession = Depends(get_async_session)
):
    """Create an audit log entry.

    This is typically called automatically by other services,
    but can be used directly for manual logging.
    """
    service = AuditLogService(session)

    # Extract request metadata
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    return await service.log(
        action=entry.action,
        resource_type=entry.resource_type,
        resource_id=entry.resource_id,
        resource_name=entry.resource_name,
        user_id=user_id,
        details=entry.details,
        ip_address=ip_address,
        user_agent=user_agent,
        status=entry.status,
        error_message=entry.error_message,
        compliance_tags=entry.compliance_tags
    )


@router.get("/audit-log", response_model=AuditLogListResponse)
async def query_audit_log(
    user_id: Optional[UUID] = Query(None, description="Filter by user"),
    resource_type: Optional[str] = Query(None, description="Filter by resource type"),
    resource_id: Optional[UUID] = Query(None, description="Filter by resource ID"),
    action: Optional[str] = Query(None, description="Filter by action"),
    start_date: Optional[datetime] = Query(None, description="Start date filter"),
    end_date: Optional[datetime] = Query(None, description="End date filter"),
    limit: int = Query(100, ge=1, le=1000, description="Max entries to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    session: AsyncSession = Depends(get_async_session)
):
    """Query the audit log with filters.

    Returns immutable records of all actions taken in the system.
    """
    service = AuditLogService(session)
    entries, total = await service.query(
        user_id=user_id,
        resource_type=resource_type,
        resource_id=resource_id,
        action=action,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        offset=offset
    )
    return AuditLogListResponse(entries=entries, total=total)


# ============================================================================
# DATA CLASSIFICATION ENDPOINTS
# ============================================================================

@router.post("/classifications", response_model=DataClassification, status_code=201)
async def classify_data(
    classification: DataClassificationCreate,
    classified_by: Optional[UUID] = Query(None, description="User ID performing classification"),
    session: AsyncSession = Depends(get_async_session)
):
    """Classify a data resource.

    Classifications help identify sensitive data and enable policy enforcement.
    """
    service = DataClassificationService(session)
    return await service.classify(classification, classified_by=classified_by)


@router.get("/classifications", response_model=DataClassificationListResponse)
async def list_classifications(
    resource_type: Optional[str] = Query(None, description="Filter by resource type"),
    classification: Optional[Classification] = Query(None, description="Filter by classification level"),
    session: AsyncSession = Depends(get_async_session)
):
    """List data classifications."""
    service = DataClassificationService(session)
    classifications = await service.list_classifications(
        resource_type=resource_type,
        classification=classification
    )
    return DataClassificationListResponse(classifications=classifications, total=len(classifications))


@router.get("/classifications/{classification_id}", response_model=DataClassification)
async def get_classification(
    classification_id: UUID,
    session: AsyncSession = Depends(get_async_session)
):
    """Get a specific classification by ID."""
    service = DataClassificationService(session)
    classification = await service.get_classification(classification_id)
    if not classification:
        raise HTTPException(status_code=404, detail="Classification not found")
    return classification


@router.get("/classifications/resource/{resource_type}/{resource_id}", response_model=DataClassification)
async def get_resource_classification(
    resource_type: str,
    resource_id: UUID,
    session: AsyncSession = Depends(get_async_session)
):
    """Get classification for a specific resource."""
    service = DataClassificationService(session)
    classification = await service.get_resource_classification(resource_type, resource_id)
    if not classification:
        raise HTTPException(status_code=404, detail="No classification found for this resource")
    return classification


# ============================================================================
# COMPLIANCE REPORTING ENDPOINTS
# ============================================================================

@router.get("/compliance/report", response_model=ComplianceReportResponse)
async def generate_compliance_report(
    frameworks: Optional[List[ComplianceFramework]] = Query(
        None,
        description="Frameworks to include (default: all)"
    ),
    session: AsyncSession = Depends(get_async_session)
):
    """Generate a compliance report.

    Evaluates the system against various compliance frameworks:
    - GDPR: General Data Protection Regulation
    - HIPAA: Health Insurance Portability and Accountability Act
    - CCPA: California Consumer Privacy Act
    - SOC2: Service Organization Control 2
    - PCI-DSS: Payment Card Industry Data Security Standard
    """
    service = ComplianceService(session)
    return await service.generate_report(frameworks=frameworks)


@router.get("/compliance/frameworks", response_model=List[dict])
async def list_compliance_frameworks():
    """List available compliance frameworks."""
    return [
        {
            "id": ComplianceFramework.GDPR.value,
            "name": "General Data Protection Regulation",
            "description": "EU data protection and privacy regulation",
            "regions": ["EU", "EEA"]
        },
        {
            "id": ComplianceFramework.HIPAA.value,
            "name": "Health Insurance Portability and Accountability Act",
            "description": "US healthcare data protection regulation",
            "regions": ["US"]
        },
        {
            "id": ComplianceFramework.CCPA.value,
            "name": "California Consumer Privacy Act",
            "description": "California consumer privacy regulation",
            "regions": ["US-CA"]
        },
        {
            "id": ComplianceFramework.SOC2.value,
            "name": "Service Organization Control 2",
            "description": "Security, availability, and confidentiality controls",
            "regions": ["Global"]
        },
        {
            "id": ComplianceFramework.PCI_DSS.value,
            "name": "Payment Card Industry Data Security Standard",
            "description": "Payment card data security requirements",
            "regions": ["Global"]
        }
    ]
