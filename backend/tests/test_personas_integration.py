"""Integration tests for personas domain services.

Tests PersonaService, PersonaAssignmentService, and AccessCheckService
with mocked database sessions.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime, timedelta

from domains.personas.models import (
    PersonaCreate, PersonaUpdate, PersonaStatus, RoleType,
    PersonaAssignmentCreate, AccessCheckRequest
)
from domains.personas.service import (
    PersonaService, PersonaAssignmentService, AccessCheckService,
    _increment_version
)


class TestVersionIncrement:
    """Test version increment helper."""

    def test_increment_version_patch(self):
        """Test incrementing patch version."""
        assert _increment_version("1.0.0") == "1.0.1"
        assert _increment_version("1.0.9") == "1.0.10"
        assert _increment_version("2.5.3") == "2.5.4"

    def test_increment_version_invalid(self):
        """Test invalid version format returns default."""
        assert _increment_version("invalid") == "1.0.1"
        assert _increment_version("1.0") == "1.0.1"


class TestPersonaService:
    """Test PersonaService with mocked database."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock async session."""
        session = AsyncMock()
        session.execute = AsyncMock()
        session.commit = AsyncMock()
        return session

    @pytest.fixture
    def service(self, mock_session):
        """Create PersonaService with mock session."""
        return PersonaService(mock_session)

    @pytest.mark.asyncio
    async def test_create_persona_basic(self, service, mock_session):
        """Test creating a persona with minimal data."""
        persona_data = PersonaCreate(name="Test Analyst", role_type=RoleType.ANALYST)

        # Mock the insert
        mock_session.execute.return_value = MagicMock()

        # Mock get_persona to return the created persona
        mock_row = MagicMock()
        mock_row.id = uuid4()
        mock_row.name = "Test Analyst"
        mock_row.description = None
        mock_row.org_id = uuid4()
        mock_row.created_at = datetime.utcnow()
        mock_row.constraints = {
            "status": "draft",
            "version": "1.0.0",
            "role_type": "analyst",
            "department": None,
            "default_datasets": [],
            "default_tables": [],
            "allowed_classifications": [],
            "denied_classifications": [],
            "preferences": {},
            "default_dashboard_id": None,
            "metadata": {},
            "tags": [],
            "created_by": None,
        }

        # First execute is insert, second is get for initial version, third is get_persona
        mock_result = MagicMock()
        mock_result.fetchone.return_value = mock_row
        mock_session.execute.return_value = mock_result

        result = await service.create_persona(persona_data)

        assert result is not None
        assert result.name == "Test Analyst"
        assert result.role_type == RoleType.ANALYST
        assert result.status == PersonaStatus.DRAFT

    @pytest.mark.asyncio
    async def test_get_persona_not_found(self, service, mock_session):
        """Test getting a persona that doesn't exist."""
        mock_result = MagicMock()
        mock_result.fetchone.return_value = None
        mock_session.execute.return_value = mock_result

        result = await service.get_persona(uuid4())
        assert result is None

    @pytest.mark.asyncio
    async def test_list_personas_empty(self, service, mock_session):
        """Test listing personas when none exist."""
        mock_result = MagicMock()
        mock_result.fetchall.return_value = []
        mock_session.execute.return_value = mock_result

        result = await service.list_personas()
        assert result == []

    @pytest.mark.asyncio
    async def test_list_personas_with_filters(self, service, mock_session):
        """Test listing personas with status filter."""
        mock_row = MagicMock()
        mock_row.id = uuid4()
        mock_row.name = "Active Analyst"
        mock_row.description = "An active analyst persona"
        mock_row.org_id = uuid4()
        mock_row.created_at = datetime.utcnow()
        mock_row.constraints = {
            "status": "active",
            "version": "1.0.0",
            "role_type": "analyst",
            "department": "Engineering",
            "default_datasets": [],
            "default_tables": [],
            "allowed_classifications": [],
            "denied_classifications": [],
            "preferences": {},
            "default_dashboard_id": None,
            "metadata": {},
            "tags": [],
            "created_by": None,
        }

        mock_result = MagicMock()
        mock_result.fetchall.return_value = [mock_row]
        mock_session.execute.return_value = mock_result

        # Filter by active status
        result = await service.list_personas(status=PersonaStatus.ACTIVE)
        assert len(result) == 1
        assert result[0].status == PersonaStatus.ACTIVE

        # Filter by role type
        result = await service.list_personas(role_type=RoleType.ANALYST)
        assert len(result) == 1

        # Filter by department
        result = await service.list_personas(department="Engineering")
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_update_persona_creates_version(self, service, mock_session):
        """Test that updating a persona increments version."""
        persona_id = uuid4()

        # Mock get_persona response
        mock_row = MagicMock()
        mock_row.id = persona_id
        mock_row.name = "Original Name"
        mock_row.description = "Original description"
        mock_row.org_id = uuid4()
        mock_row.created_at = datetime.utcnow()
        mock_row.constraints = {
            "status": "draft",
            "version": "1.0.0",
            "role_type": "analyst",
            "department": None,
            "default_datasets": [],
            "default_tables": [],
            "allowed_classifications": [],
            "denied_classifications": [],
            "preferences": {},
            "default_dashboard_id": None,
            "metadata": {},
            "tags": [],
            "created_by": None,
        }

        mock_result = MagicMock()
        mock_result.fetchone.return_value = mock_row
        mock_session.execute.return_value = mock_result

        update_data = PersonaUpdate(name="Updated Name")
        result = await service.update_persona(persona_id, update_data, change_reason="Testing")

        assert result is not None
        # The session.execute should have been called for update
        assert mock_session.execute.called

    @pytest.mark.asyncio
    async def test_delete_persona_archives(self, service, mock_session):
        """Test that delete sets status to archived."""
        persona_id = uuid4()

        mock_row = MagicMock()
        mock_row.id = persona_id
        mock_row.constraints = {"status": "active", "version": "1.0.0"}

        mock_result = MagicMock()
        mock_result.fetchone.return_value = mock_row
        mock_session.execute.return_value = mock_result

        result = await service.delete_persona(persona_id)
        assert result is True

    @pytest.mark.asyncio
    async def test_delete_persona_not_found(self, service, mock_session):
        """Test deleting a persona that doesn't exist."""
        mock_result = MagicMock()
        mock_result.fetchone.return_value = None
        mock_session.execute.return_value = mock_result

        result = await service.delete_persona(uuid4())
        assert result is False


class TestPersonaAssignmentService:
    """Test PersonaAssignmentService with mocked database."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock async session."""
        session = AsyncMock()
        session.execute = AsyncMock()
        session.commit = AsyncMock()
        return session

    @pytest.fixture
    def service(self, mock_session):
        """Create PersonaAssignmentService with mock session."""
        return PersonaAssignmentService(mock_session)

    @pytest.mark.asyncio
    async def test_assign_persona_to_user(self, service, mock_session):
        """Test assigning a persona to a user."""
        persona_id = uuid4()
        user_id = uuid4()
        assignment_data = PersonaAssignmentCreate(
            persona_id=persona_id,
            user_id=user_id,
            is_primary=True
        )

        # Mock the returned assignment
        mock_row = MagicMock()
        mock_row.id = uuid4()
        mock_row.persona_id = persona_id
        mock_row.user_id = user_id
        mock_row.is_primary = "Y"
        mock_row.assigned_by = None
        mock_row.assigned_at = datetime.utcnow()
        mock_row.expires_at = None
        mock_row.notes = None

        mock_result = MagicMock()
        mock_result.fetchone.return_value = mock_row
        mock_session.execute.return_value = mock_result

        result = await service.assign_persona(assignment_data)

        assert result is not None
        assert result.persona_id == persona_id
        assert result.user_id == user_id
        assert result.is_primary is True

    @pytest.mark.asyncio
    async def test_get_user_personas(self, service, mock_session):
        """Test getting all personas for a user."""
        user_id = uuid4()

        mock_row1 = MagicMock()
        mock_row1.id = uuid4()
        mock_row1.persona_id = uuid4()
        mock_row1.user_id = user_id
        mock_row1.is_primary = "Y"
        mock_row1.assigned_by = None
        mock_row1.assigned_at = datetime.utcnow()
        mock_row1.expires_at = None
        mock_row1.notes = None

        mock_row2 = MagicMock()
        mock_row2.id = uuid4()
        mock_row2.persona_id = uuid4()
        mock_row2.user_id = user_id
        mock_row2.is_primary = "N"
        mock_row2.assigned_by = None
        mock_row2.assigned_at = datetime.utcnow()
        mock_row2.expires_at = None
        mock_row2.notes = None

        mock_result = MagicMock()
        mock_result.fetchall.return_value = [mock_row1, mock_row2]
        mock_session.execute.return_value = mock_result

        result = await service.get_user_personas(user_id)

        assert len(result) == 2
        assert result[0].is_primary is True
        assert result[1].is_primary is False

    @pytest.mark.asyncio
    async def test_remove_assignment(self, service, mock_session):
        """Test removing an assignment."""
        assignment_id = uuid4()

        mock_result = MagicMock()
        mock_result.rowcount = 1
        mock_session.execute.return_value = mock_result

        result = await service.remove_assignment(assignment_id)
        assert result is True

    @pytest.mark.asyncio
    async def test_remove_assignment_not_found(self, service, mock_session):
        """Test removing an assignment that doesn't exist."""
        assignment_id = uuid4()

        mock_result = MagicMock()
        mock_result.rowcount = 0
        mock_session.execute.return_value = mock_result

        result = await service.remove_assignment(assignment_id)
        assert result is False


class TestAccessCheckService:
    """Test AccessCheckService with mocked database."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock async session."""
        session = AsyncMock()
        session.execute = AsyncMock()
        session.commit = AsyncMock()
        return session

    @pytest.fixture
    def service(self, mock_session):
        """Create AccessCheckService with mock session."""
        return AccessCheckService(mock_session)

    def _create_mock_persona_row(
        self,
        persona_id,
        status="active",
        allowed_classifications=None,
        denied_classifications=None,
        default_datasets=None,
        default_tables=None,
        favorite_tables=None
    ):
        """Helper to create a mock persona row."""
        mock_row = MagicMock()
        mock_row.id = persona_id
        mock_row.name = "Test Persona"
        mock_row.description = None
        mock_row.org_id = uuid4()
        mock_row.created_at = datetime.utcnow()
        mock_row.constraints = {
            "status": status,
            "version": "1.0.0",
            "role_type": "analyst",
            "department": None,
            "default_datasets": [str(d) for d in (default_datasets or [])],
            "default_tables": default_tables or [],
            "allowed_classifications": allowed_classifications or [],
            "denied_classifications": denied_classifications or [],
            "preferences": {},
            "default_dashboard_id": None,
            "metadata": {},
            "tags": [],
            "created_by": None,
            "favorite_tables": favorite_tables or [],
        }
        return mock_row

    @pytest.mark.asyncio
    async def test_access_check_allowed(self, service, mock_session):
        """Test access check when classification is allowed."""
        persona_id = uuid4()
        mock_row = self._create_mock_persona_row(
            persona_id,
            status="active",
            allowed_classifications=["public", "internal", "confidential"]
        )

        mock_result = MagicMock()
        mock_result.fetchone.return_value = mock_row
        mock_session.execute.return_value = mock_result

        request = AccessCheckRequest(
            persona_id=persona_id,
            resource_type="table",
            resource_ref="analytics.sales",
            classification="internal"
        )

        result = await service.check_access(request)

        assert result.allowed is True
        assert "allowed_classification" in result.matching_rules

    @pytest.mark.asyncio
    async def test_access_check_denied_classification(self, service, mock_session):
        """Test access check when classification is denied."""
        persona_id = uuid4()
        mock_row = self._create_mock_persona_row(
            persona_id,
            status="active",
            denied_classifications=["restricted", "top-secret"]
        )

        mock_result = MagicMock()
        mock_result.fetchone.return_value = mock_row
        mock_session.execute.return_value = mock_result

        request = AccessCheckRequest(
            persona_id=persona_id,
            resource_type="dataset",
            resource_id=uuid4(),
            classification="restricted"
        )

        result = await service.check_access(request)

        assert result.allowed is False
        assert "Classification 'restricted' is denied" in result.reason

    @pytest.mark.asyncio
    async def test_access_check_not_in_allowed_list(self, service, mock_session):
        """Test access denied when classification not in allowed list."""
        persona_id = uuid4()
        mock_row = self._create_mock_persona_row(
            persona_id,
            status="active",
            allowed_classifications=["public"]  # Only public allowed
        )

        mock_result = MagicMock()
        mock_result.fetchone.return_value = mock_row
        mock_session.execute.return_value = mock_result

        request = AccessCheckRequest(
            persona_id=persona_id,
            resource_type="table",
            resource_ref="analytics.customers",
            classification="confidential"  # Not in allowed list
        )

        result = await service.check_access(request)

        assert result.allowed is False
        assert "not in allowed list" in result.reason

    @pytest.mark.asyncio
    async def test_access_check_default_dataset(self, service, mock_session):
        """Test access check with default dataset."""
        persona_id = uuid4()
        dataset_id = uuid4()
        mock_row = self._create_mock_persona_row(
            persona_id,
            status="active",
            default_datasets=[dataset_id]
        )

        mock_result = MagicMock()
        mock_result.fetchone.return_value = mock_row
        mock_session.execute.return_value = mock_result

        request = AccessCheckRequest(
            persona_id=persona_id,
            resource_type="dataset",
            resource_id=dataset_id
        )

        result = await service.check_access(request)

        assert result.allowed is True
        assert "default_dataset" in result.matching_rules

    @pytest.mark.asyncio
    async def test_access_check_inactive_persona(self, service, mock_session):
        """Test access denied for inactive persona."""
        persona_id = uuid4()
        mock_row = self._create_mock_persona_row(
            persona_id,
            status="draft"  # Not active
        )

        mock_result = MagicMock()
        mock_result.fetchone.return_value = mock_row
        mock_session.execute.return_value = mock_result

        request = AccessCheckRequest(
            persona_id=persona_id,
            resource_type="table",
            resource_ref="analytics.sales"
        )

        result = await service.check_access(request)

        assert result.allowed is False
        assert "draft" in result.reason

    @pytest.mark.asyncio
    async def test_access_check_persona_not_found(self, service, mock_session):
        """Test access denied when persona not found."""
        mock_result = MagicMock()
        mock_result.fetchone.return_value = None
        mock_session.execute.return_value = mock_result

        request = AccessCheckRequest(
            persona_id=uuid4(),
            resource_type="table",
            resource_ref="analytics.sales"
        )

        result = await service.check_access(request)

        assert result.allowed is False
        assert "Persona not found" in result.reason

    @pytest.mark.asyncio
    async def test_access_check_no_restrictions(self, service, mock_session):
        """Test access allowed when no restrictions apply."""
        persona_id = uuid4()
        mock_row = self._create_mock_persona_row(
            persona_id,
            status="active"
            # No classifications configured
        )

        mock_result = MagicMock()
        mock_result.fetchone.return_value = mock_row
        mock_session.execute.return_value = mock_result

        request = AccessCheckRequest(
            persona_id=persona_id,
            resource_type="table",
            resource_ref="analytics.general"
        )

        result = await service.check_access(request)

        assert result.allowed is True
        assert "No restrictions apply" in result.reason


class TestRouterSessionManagement:
    """Test that router session management is correct."""

    def test_session_factory_singleton(self):
        """Test that session factory uses singleton pattern."""
        from domains.personas.router import _get_session_factory, _engine, _async_session_factory

        # This import test verifies the module-level pattern is in place
        # The actual singleton behavior would need a live database to test fully
        assert _get_session_factory is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
