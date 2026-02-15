"""Authentication dependencies for FastAPI.

This module provides dependencies for protecting endpoints with authentication.
Separated from router to avoid circular imports with RBAC.
"""
from typing import Optional

from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from core.config import settings
from core.jwt import verify_token
from domains.auth.models import User


security = HTTPBearer(auto_error=False)

# Module-level engine (shared across all requests)
_engine = None
_async_session_factory = None


def _get_session_factory():
    """Get or create the async session factory (singleton pattern)."""
    global _engine, _async_session_factory
    if _engine is None:
        async_url = settings.database_url.replace('postgresql+psycopg', 'postgresql+asyncpg')
        if 'asyncpg' not in async_url:
            async_url = settings.database_url.replace('postgresql://', 'postgresql+asyncpg://')
        _engine = create_async_engine(async_url)
        _async_session_factory = sessionmaker(_engine, class_=AsyncSession, expire_on_commit=False)
    return _async_session_factory


async def get_async_session():
    """Get async database session."""
    session_factory = _get_session_factory()
    async with session_factory() as session:
        yield session
        await session.commit()


async def _verify_token_or_api_key(token: str, session: AsyncSession) -> Optional[User]:
    """Try to verify as JWT first, then as API token.

    Args:
        token: The bearer token (could be JWT or API token)
        session: Database session

    Returns:
        User if authentication succeeds, None otherwise
    """
    from domains.auth.service import AuthService, TokenService

    # Check if it looks like an API token (starts with nex_)
    if token.startswith("nex_"):
        token_service = TokenService(session)
        return await token_service.verify_api_token(token)

    # Otherwise, try JWT verification
    auth_service = AuthService(session)
    return await auth_service.verify_token(token)


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    session: AsyncSession = Depends(get_async_session)
) -> Optional[User]:
    """Get current user from JWT token or API key (optional - returns None if no token)."""
    if not credentials:
        return None

    user = await _verify_token_or_api_key(credentials.credentials, session)
    return user


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
    session: AsyncSession = Depends(get_async_session)
) -> User:
    """Get current authenticated user (required - raises 401 if not authenticated).

    Supports both JWT tokens and API keys (starting with 'nex_').
    """
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")

    user = await _verify_token_or_api_key(credentials.credentials, session)

    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="User account is disabled")

    return user
