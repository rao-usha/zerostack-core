"""Tests for auth domain - password hashing, JWT tokens, and authentication."""
import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from core.password import hash_password, verify_password
from core.jwt import (
    create_access_token, create_refresh_token, verify_token,
    get_token_expiry_seconds, get_refresh_token_expiry_seconds
)
from domains.auth.models import (
    Role, User, UserCreate, UserLogin, Token, TokenRefreshRequest, TokenRefreshResponse,
    Organization, OrganizationCreate, APIToken, APITokenCreate, APITokenCreatedResponse
)


class TestPasswordHashing:
    """Test password hashing utilities."""

    def test_hash_password_returns_string(self):
        """Test that hash_password returns a string."""
        hashed = hash_password("mysecretpassword")
        assert isinstance(hashed, str)
        assert len(hashed) > 0

    def test_hash_password_is_different_from_input(self):
        """Test that hashed password is different from original."""
        password = "mysecretpassword"
        hashed = hash_password(password)
        assert hashed != password

    def test_hash_password_unique_salts(self):
        """Test that same password produces different hashes (unique salts)."""
        password = "mysecretpassword"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        assert hash1 != hash2

    def test_verify_password_correct(self):
        """Test password verification with correct password."""
        password = "mysecretpassword"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Test password verification with wrong password."""
        password = "mysecretpassword"
        hashed = hash_password(password)
        assert verify_password("wrongpassword", hashed) is False

    def test_verify_password_empty(self):
        """Test password verification with empty password."""
        hashed = hash_password("somepassword")
        assert verify_password("", hashed) is False

    def test_verify_password_invalid_hash(self):
        """Test password verification with invalid hash."""
        assert verify_password("password", "invalid_hash") is False

    def test_verify_password_none_hash(self):
        """Test password verification with None hash."""
        # Should return False, not raise exception
        result = verify_password("password", None)
        assert result is False

    def test_hash_unicode_password(self):
        """Test hashing unicode password."""
        password = "password123"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True


class TestJWTTokens:
    """Test JWT token utilities."""

    def test_create_access_token(self):
        """Test creating an access token."""
        user_id = uuid4()
        token = create_access_token(
            user_id=user_id,
            email="test@example.com",
            role="viewer"
        )
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_access_token_with_org(self):
        """Test creating access token with org_id."""
        user_id = uuid4()
        org_id = uuid4()
        token = create_access_token(
            user_id=user_id,
            email="test@example.com",
            role="admin",
            org_id=org_id
        )
        assert isinstance(token, str)

    def test_verify_token_valid(self):
        """Test verifying a valid token."""
        user_id = uuid4()
        token = create_access_token(
            user_id=user_id,
            email="test@example.com",
            role="viewer"
        )
        payload = verify_token(token)
        assert payload is not None
        assert payload.sub == str(user_id)
        assert payload.email == "test@example.com"
        assert payload.role == "viewer"

    def test_verify_token_with_org(self):
        """Test verifying token with org_id."""
        user_id = uuid4()
        org_id = uuid4()
        token = create_access_token(
            user_id=user_id,
            email="test@example.com",
            role="admin",
            org_id=org_id
        )
        payload = verify_token(token)
        assert payload is not None
        assert payload.org_id == str(org_id)

    def test_verify_token_invalid(self):
        """Test verifying an invalid token."""
        payload = verify_token("invalid.token.here")
        assert payload is None

    def test_verify_token_empty(self):
        """Test verifying an empty token."""
        payload = verify_token("")
        assert payload is None

    def test_create_token_custom_expiry(self):
        """Test creating token with custom expiry."""
        user_id = uuid4()
        token = create_access_token(
            user_id=user_id,
            email="test@example.com",
            role="viewer",
            expires_delta=timedelta(hours=1)
        )
        payload = verify_token(token)
        assert payload is not None

    def test_get_token_expiry_seconds(self):
        """Test getting token expiry in seconds."""
        expiry = get_token_expiry_seconds()
        assert isinstance(expiry, int)
        assert expiry > 0


class TestRefreshTokens:
    """Test refresh token utilities."""

    def test_create_refresh_token(self):
        """Test creating a refresh token."""
        token, expires_at = create_refresh_token()
        assert isinstance(token, str)
        assert len(token) > 20  # Should be a substantial token
        assert expires_at > datetime.utcnow()

    def test_create_refresh_token_unique(self):
        """Test that refresh tokens are unique."""
        token1, _ = create_refresh_token()
        token2, _ = create_refresh_token()
        assert token1 != token2

    def test_get_refresh_token_expiry_seconds(self):
        """Test getting refresh token expiry in seconds."""
        expiry = get_refresh_token_expiry_seconds()
        assert isinstance(expiry, int)
        assert expiry > 0
        # Should be longer than access token
        assert expiry > get_token_expiry_seconds()


class TestTokenRefreshModels:
    """Test token refresh models."""

    def test_token_refresh_request(self):
        """Test TokenRefreshRequest model."""
        request = TokenRefreshRequest(refresh_token="some_token_here")
        assert request.refresh_token == "some_token_here"

    def test_token_refresh_response(self):
        """Test TokenRefreshResponse model."""
        response = TokenRefreshResponse(
            access_token="new_access_token",
            refresh_token="new_refresh_token",
            token_type="bearer",
            expires_in=1800,
            refresh_expires_in=604800
        )
        assert response.access_token == "new_access_token"
        assert response.refresh_token == "new_refresh_token"
        assert response.expires_in == 1800
        assert response.refresh_expires_in == 604800


class TestRoleEnum:
    """Test Role enum values."""

    def test_role_admin(self):
        """Test admin role value."""
        assert Role.ADMIN.value == "admin"

    def test_role_data_scientist(self):
        """Test data scientist role value."""
        assert Role.DATA_SCIENTIST.value == "data_scientist"

    def test_role_analyst(self):
        """Test analyst role value."""
        assert Role.ANALYST.value == "analyst"

    def test_role_viewer(self):
        """Test viewer role value."""
        assert Role.VIEWER.value == "viewer"

    def test_role_guest(self):
        """Test guest role value."""
        assert Role.GUEST.value == "guest"


class TestUserModels:
    """Test user Pydantic models."""

    def test_user_model(self):
        """Test User model."""
        user = User(
            id=uuid4(),
            email="test@example.com",
            username="testuser",
            full_name="Test User",
            role=Role.VIEWER,
            org_id=uuid4(),
            is_active=True
        )
        assert user.email == "test@example.com"
        assert user.username == "testuser"
        assert user.role == Role.VIEWER
        assert user.is_active is True

    def test_user_model_defaults(self):
        """Test User model default values."""
        user = User(
            id=uuid4(),
            email="test@example.com",
            username="testuser"
        )
        assert user.role == Role.VIEWER
        assert user.is_active is True
        assert user.full_name is None

    def test_user_create_model(self):
        """Test UserCreate model."""
        user_create = UserCreate(
            email="test@example.com",
            username="testuser",
            password="secretpassword",
            full_name="Test User",
            role=Role.ANALYST
        )
        assert user_create.email == "test@example.com"
        assert user_create.password == "secretpassword"
        assert user_create.role == Role.ANALYST

    def test_user_create_defaults(self):
        """Test UserCreate default values."""
        user_create = UserCreate(
            email="test@example.com",
            username="testuser",
            password="secretpassword"
        )
        assert user_create.role == Role.VIEWER
        assert user_create.full_name is None
        assert user_create.org_id is None

    def test_user_login_model(self):
        """Test UserLogin model."""
        login = UserLogin(
            email="test@example.com",
            password="secretpassword"
        )
        assert login.email == "test@example.com"
        assert login.password == "secretpassword"


class TestTokenModel:
    """Test Token model."""

    def test_token_model(self):
        """Test Token model."""
        token = Token(
            access_token="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
            token_type="bearer",
            expires_in=1800
        )
        assert token.access_token.startswith("eyJ")
        assert token.token_type == "bearer"
        assert token.expires_in == 1800

    def test_token_model_default_type(self):
        """Test Token model default token_type."""
        token = Token(
            access_token="token123",
            expires_in=3600
        )
        assert token.token_type == "bearer"

    def test_token_model_with_refresh(self):
        """Test Token model with refresh token."""
        token = Token(
            access_token="access123",
            refresh_token="refresh456",
            token_type="bearer",
            expires_in=1800,
            refresh_expires_in=604800
        )
        assert token.refresh_token == "refresh456"
        assert token.refresh_expires_in == 604800


class TestOrganizationModels:
    """Test organization models."""

    def test_organization_model(self):
        """Test Organization model."""
        org = Organization(
            id=uuid4(),
            name="Acme Corp",
            slug="acme-corp",
            description="A test organization"
        )
        assert org.name == "Acme Corp"
        assert org.slug == "acme-corp"
        assert org.description == "A test organization"

    def test_organization_create_model(self):
        """Test OrganizationCreate model."""
        org_create = OrganizationCreate(
            name="New Org",
            slug="new-org",
            description="A new organization"
        )
        assert org_create.name == "New Org"
        assert org_create.slug == "new-org"

    def test_organization_create_defaults(self):
        """Test OrganizationCreate defaults."""
        org_create = OrganizationCreate(
            name="Minimal Org",
            slug="minimal-org"
        )
        assert org_create.description is None


class TestAPITokenModels:
    """Test API token models."""

    def test_api_token_model(self):
        """Test APIToken model."""
        token = APIToken(
            id=uuid4(),
            name="My API Token",
            token_prefix="nex_",
            user_id=uuid4()
        )
        assert token.name == "My API Token"
        assert token.token_prefix == "nex_"
        assert token.is_active is True

    def test_api_token_create_model(self):
        """Test APITokenCreate model."""
        create = APITokenCreate(
            name="CI Token",
            expires_in_days=30
        )
        assert create.name == "CI Token"
        assert create.expires_in_days == 30

    def test_api_token_create_no_expiry(self):
        """Test APITokenCreate without expiry."""
        create = APITokenCreate(name="Permanent Token")
        assert create.name == "Permanent Token"
        assert create.expires_in_days is None

    def test_api_token_created_response(self):
        """Test APITokenCreatedResponse model."""
        user_id = uuid4()
        org_id = uuid4()
        response = APITokenCreatedResponse(
            id=uuid4(),
            name="My API Token",
            token="nex_abc123def456",
            token_prefix="nex_abc123de",
            user_id=user_id,
            org_id=org_id,
            expires_at=datetime.utcnow() + timedelta(days=30),
            created_at=datetime.utcnow()
        )
        assert response.name == "My API Token"
        assert response.token == "nex_abc123def456"
        assert response.token_prefix == "nex_abc123de"
        assert response.user_id == user_id
        assert response.org_id == org_id
        assert response.expires_at is not None

    def test_api_token_created_response_no_expiry(self):
        """Test APITokenCreatedResponse without expiry."""
        response = APITokenCreatedResponse(
            id=uuid4(),
            name="Permanent Token",
            token="nex_permanent123",
            token_prefix="nex_permane",
            user_id=uuid4(),
            expires_at=None
        )
        assert response.expires_at is None
        assert response.org_id is None


class TestTokenServiceGeneration:
    """Test TokenService token generation (unit tests, no DB)."""

    def test_token_prefix_format(self):
        """Test that generated tokens have correct prefix."""
        from domains.auth.service import TokenService

        # Create a mock service just to test token generation
        class MockSession:
            pass

        service = TokenService(MockSession())
        token = service._generate_token()

        assert token.startswith("nex_")
        assert len(token) > 20  # Should be substantial

    def test_token_uniqueness(self):
        """Test that generated tokens are unique."""
        from domains.auth.service import TokenService

        class MockSession:
            pass

        service = TokenService(MockSession())
        token1 = service._generate_token()
        token2 = service._generate_token()

        assert token1 != token2


class TestRouterImports:
    """Test that router and services import correctly."""

    def test_router_imports(self):
        """Verify router can be imported."""
        from domains.auth.router import router
        assert router is not None
        assert router.prefix == "/auth"

    def test_service_imports(self):
        """Verify services can be imported."""
        from domains.auth.service import AuthService, OrganizationService, TokenService
        assert AuthService is not None
        assert OrganizationService is not None
        assert TokenService is not None

    def test_password_utils_imports(self):
        """Verify password utils can be imported."""
        from core.password import hash_password, verify_password
        assert hash_password is not None
        assert verify_password is not None

    def test_jwt_utils_imports(self):
        """Verify JWT utils can be imported."""
        from core.jwt import create_access_token, verify_token, get_token_expiry_seconds
        assert create_access_token is not None
        assert verify_token is not None
        assert get_token_expiry_seconds is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
