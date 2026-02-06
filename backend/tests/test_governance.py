"""Tests for governance domain - policies, approvals, audit logging."""
import pytest
from uuid import uuid4
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch

from domains.governance.models import (
    Policy, PolicyCreate, PolicyUpdate, PolicyType, PolicyStatus,
    Approval, ApprovalCreate, ApprovalStatus, ApprovalReview,
    AuditLogEntry, AuditLogCreate,
    DataClassification, DataClassificationCreate, Classification,
    PolicyEvaluationRequest, PolicyEvaluationResult,
    ComplianceFramework, ComplianceReportResponse
)


class TestPolicyModels:
    """Test policy Pydantic models."""

    def test_policy_create_minimal(self):
        """Test creating a policy with minimal fields."""
        policy = PolicyCreate(
            name="Test Policy",
            policy_type=PolicyType.DATA_ACCESS
        )
        assert policy.name == "Test Policy"
        assert policy.policy_type == PolicyType.DATA_ACCESS
        assert policy.rules == {}

    def test_policy_create_with_rules(self):
        """Test creating a policy with rules."""
        rules = {
            "conditions": [{"field": "classification", "operator": "eq", "value": "pii"}],
            "actions": ["require_approval", "log_access"],
            "applies_to": {"resource_types": ["dataset", "table"]}
        }
        policy = PolicyCreate(
            name="PII Access Policy",
            description="Requires approval for PII data access",
            policy_type=PolicyType.PRIVACY,
            rules=rules
        )
        assert policy.rules == rules
        assert "conditions" in policy.rules

    def test_policy_update_partial(self):
        """Test partial policy update."""
        update = PolicyUpdate(status=PolicyStatus.ACTIVE)
        assert update.status == PolicyStatus.ACTIVE
        assert update.name is None
        assert update.rules is None

    def test_policy_types(self):
        """Test all policy types are available."""
        assert PolicyType.DATA_ACCESS.value == "data_access"
        assert PolicyType.DATA_USAGE.value == "data_usage"
        assert PolicyType.QUALITY.value == "quality"
        assert PolicyType.PRIVACY.value == "privacy"
        assert PolicyType.RETENTION.value == "retention"


class TestApprovalModels:
    """Test approval Pydantic models."""

    def test_approval_create(self):
        """Test creating an approval request."""
        resource_id = uuid4()
        approval = ApprovalCreate(
            resource_type="dataset",
            resource_id=resource_id,
            action="access",
            reason="Need to analyze customer data"
        )
        assert approval.resource_type == "dataset"
        assert approval.resource_id == resource_id
        assert approval.action == "access"

    def test_approval_review(self):
        """Test approval review model."""
        review = ApprovalReview(
            status=ApprovalStatus.APPROVED,
            reason="Legitimate business need"
        )
        assert review.status == ApprovalStatus.APPROVED
        assert review.reason == "Legitimate business need"

    def test_approval_statuses(self):
        """Test all approval statuses."""
        assert ApprovalStatus.PENDING.value == "pending"
        assert ApprovalStatus.APPROVED.value == "approved"
        assert ApprovalStatus.REJECTED.value == "rejected"
        assert ApprovalStatus.CANCELLED.value == "cancelled"


class TestAuditLogModels:
    """Test audit log Pydantic models."""

    def test_audit_log_create(self):
        """Test creating an audit log entry."""
        entry = AuditLogCreate(
            action="dataset.access",
            resource_type="dataset",
            resource_id=uuid4(),
            resource_name="Customer Data",
            details={"query": "SELECT * FROM customers"},
            compliance_tags=["gdpr", "pii_access"]
        )
        assert entry.action == "dataset.access"
        assert "gdpr" in entry.compliance_tags

    def test_audit_log_entry_response(self):
        """Test audit log entry response model."""
        entry = AuditLogEntry(
            id=uuid4(),
            user_id=uuid4(),
            action="dataset.create",
            resource_type="dataset",
            resource_id=uuid4(),
            details={"name": "New Dataset"},
            ip_address="192.168.1.1",
            status="success",
            compliance_tags=["audit"],
            created_at=datetime.utcnow()
        )
        assert entry.status == "success"
        assert entry.ip_address == "192.168.1.1"


class TestDataClassificationModels:
    """Test data classification models."""

    def test_classification_create(self):
        """Test creating a data classification."""
        classification = DataClassificationCreate(
            resource_type="dataset",
            resource_id=uuid4(),
            classification=Classification.PII,
            sub_classification="email",
            compliance_tags=["gdpr_personal", "ccpa_sensitive"],
            retention_days=365,
            notes="Contains customer email addresses"
        )
        assert classification.classification == Classification.PII
        assert classification.retention_days == 365

    def test_classification_levels(self):
        """Test all classification levels."""
        assert Classification.PUBLIC.value == "public"
        assert Classification.INTERNAL.value == "internal"
        assert Classification.CONFIDENTIAL.value == "confidential"
        assert Classification.RESTRICTED.value == "restricted"
        assert Classification.PII.value == "pii"


class TestPolicyEvaluation:
    """Test policy evaluation models."""

    def test_evaluation_request(self):
        """Test policy evaluation request."""
        request = PolicyEvaluationRequest(
            resource_type="dataset",
            resource_id=uuid4(),
            action="access",
            context={"classification": "pii", "user_role": "analyst"}
        )
        assert request.action == "access"
        assert request.context["classification"] == "pii"

    def test_evaluation_result_allowed(self):
        """Test policy evaluation result when allowed."""
        result = PolicyEvaluationResult(
            allowed=True,
            matching_policies=[],
            required_approvals=False,
            denial_reason=None,
            actions_triggered=["log_access"]
        )
        assert result.allowed is True
        assert result.required_approvals is False

    def test_evaluation_result_denied(self):
        """Test policy evaluation result when denied."""
        result = PolicyEvaluationResult(
            allowed=False,
            matching_policies=[],
            required_approvals=True,
            denial_reason="PII data requires approval",
            actions_triggered=["deny", "require_approval"]
        )
        assert result.allowed is False
        assert "deny" in result.actions_triggered


class TestComplianceModels:
    """Test compliance reporting models."""

    def test_compliance_frameworks(self):
        """Test all compliance frameworks."""
        assert ComplianceFramework.GDPR.value == "gdpr"
        assert ComplianceFramework.HIPAA.value == "hipaa"
        assert ComplianceFramework.CCPA.value == "ccpa"
        assert ComplianceFramework.SOC2.value == "soc2"
        assert ComplianceFramework.PCI_DSS.value == "pci_dss"


class TestRouterImports:
    """Test that router imports correctly."""

    def test_router_imports(self):
        """Verify router can be imported."""
        from domains.governance.router import router
        assert router is not None
        assert router.prefix == "/governance"

    def test_service_imports(self):
        """Verify services can be imported."""
        from domains.governance.service import (
            PolicyService, ApprovalService, AuditLogService,
            DataClassificationService, ComplianceService
        )
        assert PolicyService is not None
        assert ApprovalService is not None
        assert AuditLogService is not None
        assert DataClassificationService is not None
        assert ComplianceService is not None

    def test_db_models_imports(self):
        """Verify db models can be imported."""
        from domains.governance.db_models import (
            policies, approvals, audit_logs, data_classifications
        )
        assert policies is not None
        assert approvals is not None
        assert audit_logs is not None
        assert data_classifications is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
