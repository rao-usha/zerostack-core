"""JWT token utilities for authentication.

Handles JWT token creation and verification for user authentication.
Supports both access tokens (short-lived) and refresh tokens (long-lived).
"""
import secrets
from datetime import datetime, timedelta
from typing import Optional, Tuple
from uuid import UUID
from jose import JWTError, jwt
from pydantic import BaseModel

from core.config import settings


# Use a default secret if none configured (for development only)
SECRET_KEY = settings.secret_key or "dev-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes
REFRESH_TOKEN_EXPIRE_DAYS = settings.refresh_token_expire_days


class TokenPayload(BaseModel):
    """JWT token payload."""
    sub: str  # User ID
    email: str
    role: str
    org_id: Optional[str] = None
    exp: datetime
    type: str = "access"  # "access" or "refresh"


def create_access_token(
    user_id: UUID,
    email: str,
    role: str,
    org_id: Optional[UUID] = None,
    expires_delta: Optional[timedelta] = None
) -> str:
    """Create a JWT access token.

    Args:
        user_id: User's UUID
        email: User's email
        role: User's role
        org_id: Optional organization ID
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT token string
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    payload = {
        "sub": str(user_id),
        "email": email,
        "role": role,
        "org_id": str(org_id) if org_id else None,
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access",
    }

    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token() -> Tuple[str, datetime]:
    """Create a secure refresh token.

    Returns:
        Tuple of (token_string, expiry_datetime)
    """
    token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    return token, expires_at


def verify_token(token: str) -> Optional[TokenPayload]:
    """Verify and decode a JWT token.

    Args:
        token: JWT token string

    Returns:
        TokenPayload if valid, None if invalid
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return TokenPayload(
            sub=payload["sub"],
            email=payload["email"],
            role=payload["role"],
            org_id=payload.get("org_id"),
            exp=datetime.fromtimestamp(payload["exp"]),
            type=payload.get("type", "access")
        )
    except JWTError:
        return None


def get_token_expiry_seconds() -> int:
    """Get access token expiry time in seconds."""
    return ACCESS_TOKEN_EXPIRE_MINUTES * 60


def get_refresh_token_expiry_seconds() -> int:
    """Get refresh token expiry time in seconds."""
    return REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
