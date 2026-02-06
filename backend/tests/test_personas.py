"""Tests for personas domain - user roles, assignments, and access patterns."""
import pytest
from uuid import uuid4
from datetime import datetime, timedelta

from domains.personas.models import (
    Persona, PersonaCreate, PersonaUpdate, PersonaStatus, RoleType,
    PersonaListResponse, PersonaVersion, PersonaVersionListResponse,
    PersonaAssignment, PersonaAssignmentCreate, PersonaAssignmentListResponse,
    AccessCheckRequest, AccessCheckResult
)


class TestPersonaModels:
    """Test persona Pydantic models."""

    def test_persona_create_minimal(self):
        """Test creating a persona with minimal fields."""
        persona = PersonaCreate(name="Test Analyst")
        assert persona.name == "Test Analyst"
        assert persona.role_type is None
        assert persona.default_datasets == []

    def test_persona_create_full(self):
        """Test creating a persona with all fields."""
        dataset_id = uuid4()
        dashboard_id = uuid4()

        persona = PersonaCreate(
            name="Senior Data Analyst",
            description="Experienced analyst with access to sensitive data",
            role_type=RoleType.ANALYST,
            department="Marketing",
            default_datasets=[dataset_id],
            default_tables=["analytics.customers", "analytics.orders"],
            allowed_classifications=["public", "internal", "confidential"],
            denied_classifications=["restricted"],
            preferences={"theme": "dark", "timezone": "US/Pacific"},
            default_dashboard_id=dashboard_id,
            metadata={"team": "Growth"},
            tags=["marketing", "analytics"]
        )

        assert persona.name == "Senior Data Analyst"
        assert persona.role_type == RoleType.ANALYST
        assert persona.department == "Marketing"
        assert dataset_id in persona.default_datasets
        assert "analytics.customers" in persona.default_tables
        assert "confidential" in persona.allowed_classifications
        assert "restricted" in persona.denied_classifications

    def test_persona_update_partial(self):
        """Test partial persona update."""
        update = PersonaUpdate(status=PersonaStatus.ACTIVE)
        assert update.status == PersonaStatus.ACTIVE
        assert update.name is None
        assert update.role_type is None

    def test_role_types(self):
        """Test all role types are available."""
        assert RoleType.ANALYST.value == "analyst"
        assert RoleType.ENGINEER.value == "engineer"
        assert RoleType.SCIENTIST.value == "scientist"
        assert RoleType.BUSINESS_USER.value == "business_user"
        assert RoleType.ADMIN.value == "admin"
        assert RoleType.VIEWER.value == "viewer"
        assert RoleType.CUSTOM.value == "custom"

    def test_persona_statuses(self):
        """Test all persona statuses."""
        assert PersonaStatus.DRAFT.value == "draft"
        assert PersonaStatus.ACTIVE.value == "active"
        assert PersonaStatus.ARCHIVED.value == "archived"


class TestPersonaVersionModels:
    """Test persona version models."""

    def test_persona_version(self):
        """Test persona version model."""
        version = PersonaVersion(
            id=uuid4(),
            persona_id=uuid4(),
            version="1.0.1",
            snapshot={"name": "Test", "status": "active"},
            changes={"status": {"old": "draft", "new": "active"}},
            change_reason="Activated for production use",
            created_at=datetime.utcnow()
        )
        assert version.version == "1.0.1"
        assert "status" in version.changes


class TestPersonaAssignmentModels:
    """Test persona assignment models."""

    def test_assignment_create(self):
        """Test creating an assignment."""
        persona_id = uuid4()
        user_id = uuid4()

        assignment = PersonaAssignmentCreate(
            persona_id=persona_id,
            user_id=user_id,
            is_primary=True,
            expires_at=datetime.utcnow() + timedelta(days=365),
            notes="Annual assignment for marketing team"
        )

        assert assignment.persona_id == persona_id
        assert assignment.user_id == user_id
        assert assignment.is_primary is True

    def test_assignment_response(self):
        """Test assignment response model."""
        assignment = PersonaAssignment(
            id=uuid4(),
            persona_id=uuid4(),
            user_id=uuid4(),
            is_primary=True,
            assigned_at=datetime.utcnow()
        )
        assert assignment.is_primary is True


class TestAccessCheckModels:
    """Test access check models."""

    def test_access_check_request_dataset(self):
        """Test access check for dataset."""
        request = AccessCheckRequest(
            persona_id=uuid4(),
            resource_type="dataset",
            resource_id=uuid4(),
            classification="confidential"
        )
        assert request.resource_type == "dataset"
        assert request.classification == "confidential"

    def test_access_check_request_table(self):
        """Test access check for table."""
        request = AccessCheckRequest(
            persona_id=uuid4(),
            resource_type="table",
            resource_ref="analytics.customers",
            classification="internal"
        )
        assert request.resource_type == "table"
        assert request.resource_ref == "analytics.customers"

    def test_access_check_result_allowed(self):
        """Test access allowed result."""
        result = AccessCheckResult(
            allowed=True,
            persona_id=uuid4(),
            resource_type="table",
            resource_ref="analytics.customers",
            reason="Access allowed",
            matching_rules=["default_table", "allowed_classification"]
        )
        assert result.allowed is True
        assert len(result.matching_rules) == 2

    def test_access_check_result_denied(self):
        """Test access denied result."""
        result = AccessCheckResult(
            allowed=False,
            persona_id=uuid4(),
            resource_type="dataset",
            resource_id=uuid4(),
            reason="Classification 'restricted' is denied for this persona",
            matching_rules=["denied_classification"]
        )
        assert result.allowed is False
        assert "denied_classification" in result.matching_rules


class TestRouterImports:
    """Test that router imports correctly."""

    def test_router_imports(self):
        """Verify router can be imported."""
        from domains.personas.router import router
        assert router is not None
        assert router.prefix == "/personas"

    def test_service_imports(self):
        """Verify services can be imported."""
        from domains.personas.service import (
            PersonaService, PersonaAssignmentService, AccessCheckService
        )
        assert PersonaService is not None
        assert PersonaAssignmentService is not None
        assert AccessCheckService is not None

    def test_db_models_imports(self):
        """Verify db models can be imported."""
        from domains.personas.db_models import (
            personas, persona_versions, persona_assignments
        )
        assert personas is not None
        assert persona_versions is not None
        assert persona_assignments is not None


class TestListResponses:
    """Test list response models."""

    def test_persona_list_response(self):
        """Test persona list response."""
        response = PersonaListResponse(personas=[], total=0)
        assert response.total == 0
        assert response.personas == []

    def test_version_list_response(self):
        """Test version list response."""
        response = PersonaVersionListResponse(versions=[], total=0)
        assert response.total == 0

    def test_assignment_list_response(self):
        """Test assignment list response."""
        response = PersonaAssignmentListResponse(assignments=[], total=0)
        assert response.total == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
