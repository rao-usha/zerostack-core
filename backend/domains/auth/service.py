"""Auth service with password hashing, JWT tokens, and refresh tokens."""
import hashlib
from typing import Optional
from uuid import UUID, uuid4
from datetime import datetime

from sqlalchemy import select, insert, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import users, orgs, refresh_tokens, api_tokens
from core.password import hash_password, verify_password
from core.jwt import (
    create_access_token, create_refresh_token, verify_token,
    get_token_expiry_seconds, get_refresh_token_expiry_seconds
)
from .models import (
    User, UserCreate, UserLogin, Token, TokenRefreshResponse,
    Organization, OrganizationCreate, APIToken, APITokenCreate,
    APITokenCreatedResponse, Role
)


def _hash_token(token: str) -> str:
    """Hash a refresh token for storage."""
    return hashlib.sha256(token.encode()).hexdigest()


class AuthService:
    """Authentication service with password hashing, JWT, and refresh tokens."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def register_user(self, user_data: UserCreate) -> User:
        """Register a new user with hashed password.

        Args:
            user_data: User registration data

        Returns:
            Created user

        Raises:
            ValueError: If email or username already exists
        """
        # Check for existing email
        existing = await self.session.execute(
            select(users).where(users.c.email == user_data.email)
        )
        if existing.first():
            raise ValueError("Email already registered")

        # Check for existing username
        existing_username = await self.session.execute(
            select(users).where(users.c.username == user_data.username)
        )
        if existing_username.first():
            raise ValueError("Username already taken")

        # Hash the password
        password_hashed = hash_password(user_data.password)

        # Create user
        user_id = uuid4()
        now = datetime.utcnow()

        # Get or create default org if not specified
        org_id = user_data.org_id
        if not org_id:
            org_id = await self._get_or_create_default_org()

        await self.session.execute(
            insert(users).values(
                id=user_id,
                email=user_data.email,
                username=user_data.username,
                password_hash=password_hashed,
                full_name=user_data.full_name,
                role=user_data.role.value,
                org_id=org_id,
                is_active=True,
                created_at=now,
                updated_at=now,
            )
        )
        await self.session.commit()

        return User(
            id=user_id,
            email=user_data.email,
            username=user_data.username,
            full_name=user_data.full_name,
            role=user_data.role,
            org_id=org_id,
            is_active=True,
            created_at=now,
            updated_at=now,
        )

    async def authenticate_user(
        self,
        login: UserLogin,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> Optional[Token]:
        """Authenticate a user and return access + refresh tokens.

        Args:
            login: Login credentials
            user_agent: Optional user agent string
            ip_address: Optional IP address

        Returns:
            Token if authentication successful, None otherwise
        """
        # Find user by email
        result = await self.session.execute(
            select(users).where(users.c.email == login.email)
        )
        user_row = result.first()

        if not user_row:
            return None

        # Check if user is active
        if not user_row.is_active:
            return None

        # Verify password
        if not user_row.password_hash:
            return None

        if not verify_password(login.password, user_row.password_hash):
            return None

        # Generate access token
        access_token = create_access_token(
            user_id=user_row.id,
            email=user_row.email,
            role=user_row.role,
            org_id=user_row.org_id
        )

        # Generate and store refresh token
        refresh_token_str, refresh_expires_at = create_refresh_token()
        token_hash = _hash_token(refresh_token_str)

        await self.session.execute(
            insert(refresh_tokens).values(
                id=uuid4(),
                user_id=user_row.id,
                token_hash=token_hash,
                expires_at=refresh_expires_at,
                revoked=False,
                user_agent=user_agent,
                ip_address=ip_address,
                created_at=datetime.utcnow(),
            )
        )
        await self.session.commit()

        return Token(
            access_token=access_token,
            refresh_token=refresh_token_str,
            token_type="bearer",
            expires_in=get_token_expiry_seconds(),
            refresh_expires_in=get_refresh_token_expiry_seconds(),
        )

    async def refresh_access_token(
        self,
        refresh_token_str: str,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> Optional[TokenRefreshResponse]:
        """Refresh an access token using a refresh token.

        Implements token rotation: old refresh token is revoked,
        new one is issued.

        Args:
            refresh_token_str: The refresh token
            user_agent: Optional user agent string
            ip_address: Optional IP address

        Returns:
            New tokens if refresh token is valid, None otherwise
        """
        token_hash = _hash_token(refresh_token_str)

        # Find the refresh token
        result = await self.session.execute(
            select(refresh_tokens).where(
                refresh_tokens.c.token_hash == token_hash,
                refresh_tokens.c.revoked == False,
                refresh_tokens.c.expires_at > datetime.utcnow()
            )
        )
        token_row = result.first()

        if not token_row:
            return None

        # Get user
        user = await self.get_user(token_row.user_id)
        if not user or not user.is_active:
            return None

        # Revoke old refresh token (token rotation)
        await self.session.execute(
            update(refresh_tokens)
            .where(refresh_tokens.c.id == token_row.id)
            .values(revoked=True, revoked_at=datetime.utcnow())
        )

        # Generate new access token
        access_token = create_access_token(
            user_id=user.id,
            email=user.email,
            role=user.role.value,
            org_id=user.org_id
        )

        # Generate and store new refresh token
        new_refresh_token, refresh_expires_at = create_refresh_token()
        new_token_hash = _hash_token(new_refresh_token)

        await self.session.execute(
            insert(refresh_tokens).values(
                id=uuid4(),
                user_id=user.id,
                token_hash=new_token_hash,
                expires_at=refresh_expires_at,
                revoked=False,
                user_agent=user_agent,
                ip_address=ip_address,
                created_at=datetime.utcnow(),
            )
        )
        await self.session.commit()

        return TokenRefreshResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            expires_in=get_token_expiry_seconds(),
            refresh_expires_in=get_refresh_token_expiry_seconds(),
        )

    async def logout(self, refresh_token_str: str) -> bool:
        """Logout by revoking a refresh token.

        Args:
            refresh_token_str: The refresh token to revoke

        Returns:
            True if token was revoked, False if not found
        """
        token_hash = _hash_token(refresh_token_str)

        result = await self.session.execute(
            update(refresh_tokens)
            .where(
                refresh_tokens.c.token_hash == token_hash,
                refresh_tokens.c.revoked == False
            )
            .values(revoked=True, revoked_at=datetime.utcnow())
        )
        await self.session.commit()

        return result.rowcount > 0

    async def logout_all(self, user_id: UUID) -> int:
        """Logout from all devices by revoking all refresh tokens.

        Args:
            user_id: The user's ID

        Returns:
            Number of tokens revoked
        """
        result = await self.session.execute(
            update(refresh_tokens)
            .where(
                refresh_tokens.c.user_id == user_id,
                refresh_tokens.c.revoked == False
            )
            .values(revoked=True, revoked_at=datetime.utcnow())
        )
        await self.session.commit()

        return result.rowcount

    async def verify_token(self, token: str) -> Optional[User]:
        """Verify and decode a token, returning the user.

        Args:
            token: JWT token string

        Returns:
            User if token is valid, None otherwise
        """
        payload = verify_token(token)
        if not payload:
            return None

        # Get user from database to ensure they still exist and are active
        return await self.get_user(UUID(payload.sub))

    async def get_user(self, user_id: UUID) -> Optional[User]:
        """Get a user by ID.

        Args:
            user_id: User's UUID

        Returns:
            User if found, None otherwise
        """
        result = await self.session.execute(
            select(users).where(users.c.id == user_id)
        )
        row = result.first()

        if not row:
            return None

        return User(
            id=row.id,
            email=row.email,
            username=row.username or row.email.split('@')[0],
            full_name=row.full_name,
            role=Role(row.role) if row.role in [r.value for r in Role] else Role.VIEWER,
            org_id=row.org_id,
            is_active=row.is_active if hasattr(row, 'is_active') else True,
            created_at=row.created_at,
            updated_at=row.updated_at if hasattr(row, 'updated_at') else row.created_at,
        )

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get a user by email.

        Args:
            email: User's email address

        Returns:
            User if found, None otherwise
        """
        result = await self.session.execute(
            select(users).where(users.c.email == email)
        )
        row = result.first()

        if not row:
            return None

        return User(
            id=row.id,
            email=row.email,
            username=row.username or row.email.split('@')[0],
            full_name=row.full_name,
            role=Role(row.role) if row.role in [r.value for r in Role] else Role.VIEWER,
            org_id=row.org_id,
            is_active=row.is_active if hasattr(row, 'is_active') else True,
            created_at=row.created_at,
            updated_at=row.updated_at if hasattr(row, 'updated_at') else row.created_at,
        )

    async def cleanup_expired_tokens(self) -> int:
        """Remove expired refresh tokens from the database.

        Returns:
            Number of tokens deleted
        """
        result = await self.session.execute(
            delete(refresh_tokens).where(
                refresh_tokens.c.expires_at < datetime.utcnow()
            )
        )
        await self.session.commit()
        return result.rowcount

    async def _get_or_create_default_org(self) -> UUID:
        """Get or create a default organization."""
        result = await self.session.execute(
            select(orgs).where(orgs.c.name == "Default")
        )
        row = result.first()

        if row:
            return row.id

        # Create default org
        org_id = uuid4()
        await self.session.execute(
            insert(orgs).values(
                id=org_id,
                name="Default",
                created_at=datetime.utcnow(),
            )
        )
        return org_id


class OrganizationService:
    """Organization management service."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_organization(self, org_data: OrganizationCreate) -> Organization:
        """Create an organization.

        Args:
            org_data: Organization creation data

        Returns:
            Created organization

        Raises:
            ValueError: If organization name or slug already exists
        """
        # Check for existing name
        existing = await self.session.execute(
            select(orgs).where(orgs.c.name == org_data.name)
        )
        if existing.first():
            raise ValueError("Organization name already exists")

        org_id = uuid4()
        now = datetime.utcnow()

        await self.session.execute(
            insert(orgs).values(
                id=org_id,
                name=org_data.name,
                created_at=now,
            )
        )
        await self.session.commit()

        return Organization(
            id=org_id,
            name=org_data.name,
            slug=org_data.slug,
            description=org_data.description,
            metadata={},
            created_at=now,
            updated_at=now,
        )

    async def get_organization(self, org_id: UUID) -> Optional[Organization]:
        """Get an organization by ID."""
        result = await self.session.execute(
            select(orgs).where(orgs.c.id == org_id)
        )
        row = result.first()

        if not row:
            return None

        return Organization(
            id=row.id,
            name=row.name,
            slug=row.name.lower().replace(" ", "-"),
            description=None,
            metadata={},
            created_at=row.created_at,
            updated_at=row.created_at,
        )

    async def list_organizations(self) -> list[Organization]:
        """List all organizations."""
        result = await self.session.execute(select(orgs))
        rows = result.fetchall()

        return [
            Organization(
                id=row.id,
                name=row.name,
                slug=row.name.lower().replace(" ", "-"),
                description=None,
                metadata={},
                created_at=row.created_at,
                updated_at=row.created_at,
            )
            for row in rows
        ]


class TokenService:
    """API token management service for programmatic access."""

    # Token prefix for API tokens (helps identify token type)
    TOKEN_PREFIX = "nex_"

    def __init__(self, session: AsyncSession):
        self.session = session

    def _generate_token(self) -> str:
        """Generate a secure random API token."""
        import secrets
        # Generate 32 bytes of random data, encode as hex (64 chars)
        random_part = secrets.token_hex(32)
        return f"{self.TOKEN_PREFIX}{random_part}"

    async def create_api_token(
        self,
        user_id: UUID,
        token_data: APITokenCreate,
        org_id: Optional[UUID] = None
    ) -> APITokenCreatedResponse:
        """Create a new API token.

        Args:
            user_id: ID of the user creating the token
            token_data: Token creation request data
            org_id: Optional organization ID

        Returns:
            APITokenCreatedResponse with the full token (only shown once)
        """
        # Generate the token
        full_token = self._generate_token()
        token_hash = _hash_token(full_token)
        token_prefix = full_token[:12]  # Store first 12 chars for identification

        # Calculate expiration if specified
        expires_at = None
        if token_data.expires_in_days:
            from datetime import timedelta
            expires_at = datetime.utcnow() + timedelta(days=token_data.expires_in_days)

        token_id = uuid4()
        now = datetime.utcnow()

        await self.session.execute(
            insert(api_tokens).values(
                id=token_id,
                user_id=user_id,
                org_id=org_id,
                name=token_data.name,
                token_hash=token_hash,
                token_prefix=token_prefix,
                expires_at=expires_at,
                is_active=True,
                created_at=now,
            )
        )
        await self.session.commit()

        return APITokenCreatedResponse(
            id=token_id,
            name=token_data.name,
            token=full_token,
            token_prefix=token_prefix,
            user_id=user_id,
            org_id=org_id,
            expires_at=expires_at,
            created_at=now,
        )

    async def verify_api_token(self, token: str) -> Optional[User]:
        """Verify an API token and return the associated user.

        Args:
            token: The full API token

        Returns:
            User if token is valid and active, None otherwise
        """
        token_hash = _hash_token(token)

        # Find the token
        result = await self.session.execute(
            select(api_tokens).where(
                api_tokens.c.token_hash == token_hash,
                api_tokens.c.is_active == True,
            )
        )
        token_row = result.first()

        if not token_row:
            return None

        # Check expiration
        if token_row.expires_at and token_row.expires_at < datetime.utcnow():
            return None

        # Update last_used_at
        await self.session.execute(
            update(api_tokens)
            .where(api_tokens.c.id == token_row.id)
            .values(last_used_at=datetime.utcnow())
        )
        await self.session.commit()

        # Get the user
        user_result = await self.session.execute(
            select(users).where(users.c.id == token_row.user_id)
        )
        user_row = user_result.first()

        if not user_row or not user_row.is_active:
            return None

        return User(
            id=user_row.id,
            email=user_row.email,
            username=user_row.username or user_row.email.split('@')[0],
            full_name=user_row.full_name,
            role=Role(user_row.role) if user_row.role in [r.value for r in Role] else Role.VIEWER,
            org_id=user_row.org_id,
            is_active=user_row.is_active,
            created_at=user_row.created_at,
            updated_at=user_row.updated_at if hasattr(user_row, 'updated_at') else user_row.created_at,
        )

    async def revoke_api_token(self, token_id: UUID, user_id: UUID) -> bool:
        """Revoke an API token.

        Args:
            token_id: ID of the token to revoke
            user_id: ID of the user (for authorization)

        Returns:
            True if token was revoked, False if not found or not authorized
        """
        result = await self.session.execute(
            update(api_tokens)
            .where(
                api_tokens.c.id == token_id,
                api_tokens.c.user_id == user_id,
                api_tokens.c.is_active == True,
            )
            .values(is_active=False, revoked_at=datetime.utcnow())
        )
        await self.session.commit()

        return result.rowcount > 0

    async def list_api_tokens(self, user_id: UUID) -> list[APIToken]:
        """List all API tokens for a user.

        Args:
            user_id: ID of the user

        Returns:
            List of API tokens (without the actual token values)
        """
        result = await self.session.execute(
            select(api_tokens)
            .where(api_tokens.c.user_id == user_id)
            .order_by(api_tokens.c.created_at.desc())
        )
        rows = result.fetchall()

        return [
            APIToken(
                id=row.id,
                name=row.name,
                token_prefix=row.token_prefix,
                user_id=row.user_id,
                org_id=row.org_id,
                expires_at=row.expires_at,
                last_used_at=row.last_used_at,
                created_at=row.created_at,
                is_active=row.is_active,
            )
            for row in rows
        ]

    async def get_api_token(self, token_id: UUID, user_id: UUID) -> Optional[APIToken]:
        """Get a specific API token.

        Args:
            token_id: ID of the token
            user_id: ID of the user (for authorization)

        Returns:
            APIToken if found and authorized, None otherwise
        """
        result = await self.session.execute(
            select(api_tokens).where(
                api_tokens.c.id == token_id,
                api_tokens.c.user_id == user_id,
            )
        )
        row = result.first()

        if not row:
            return None

        return APIToken(
            id=row.id,
            name=row.name,
            token_prefix=row.token_prefix,
            user_id=row.user_id,
            org_id=row.org_id,
            expires_at=row.expires_at,
            last_used_at=row.last_used_at,
            created_at=row.created_at,
            is_active=row.is_active,
        )

    async def cleanup_expired_tokens(self) -> int:
        """Deactivate expired API tokens.

        Returns:
            Number of tokens deactivated
        """
        result = await self.session.execute(
            update(api_tokens)
            .where(
                api_tokens.c.expires_at < datetime.utcnow(),
                api_tokens.c.is_active == True,
            )
            .values(is_active=False)
        )
        await self.session.commit()
        return result.rowcount
