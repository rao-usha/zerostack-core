"""Auth API router with JWT authentication."""
from fastapi import APIRouter, HTTPException, Depends, Request
from typing import List
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.jwt import verify_token
from core.rate_limit import limiter
from core.rbac import require_admin, require_role
from core.auth_deps import get_current_user, get_current_user_optional, get_async_session
from domains.auth.models import (
    User, UserCreate, UserLogin, Token, TokenRefreshRequest, TokenRefreshResponse,
    Organization, OrganizationCreate, APIToken, APITokenCreate
)
from domains.auth.service import AuthService, OrganizationService, TokenService

router = APIRouter(prefix="/auth", tags=["auth"])


# ============================================================================
# PUBLIC ENDPOINTS
# ============================================================================

@router.post("/register", response_model=User, status_code=201)
@limiter.limit("5/minute")  # Prevent registration spam
async def register(
    request: Request,
    user_data: UserCreate,
    session: AsyncSession = Depends(get_async_session)
):
    """Register a new user.

    Creates a new user account with hashed password.
    Rate limited to 5 registrations per minute per IP.
    """
    auth_service = AuthService(session)

    try:
        user = await auth_service.register_user(user_data)
        return user
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login", response_model=Token)
@limiter.limit("10/minute")  # Prevent brute force attacks
async def login(
    request: Request,
    login_data: UserLogin,
    session: AsyncSession = Depends(get_async_session)
):
    """Login and get access token.

    Authenticates user credentials and returns a JWT access token.
    Rate limited to 10 attempts per minute per IP.
    """
    auth_service = AuthService(session)
    token = await auth_service.authenticate_user(login_data)

    if not token:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    return token


# ============================================================================
# TOKEN REFRESH & LOGOUT
# ============================================================================

@router.post("/refresh", response_model=TokenRefreshResponse)
@limiter.limit("30/minute")  # Allow reasonable refresh frequency
async def refresh_token(
    request: Request,
    refresh_request: TokenRefreshRequest,
    session: AsyncSession = Depends(get_async_session)
):
    """Refresh access token using a refresh token.

    The old refresh token is revoked and a new one is issued (token rotation).
    Rate limited to 30 refreshes per minute per IP.
    """
    auth_service = AuthService(session)
    result = await auth_service.refresh_access_token(refresh_request.refresh_token)

    if not result:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired refresh token"
        )

    return result


@router.post("/logout", status_code=204)
async def logout(
    logout_request: TokenRefreshRequest,
    session: AsyncSession = Depends(get_async_session)
):
    """Logout by revoking a refresh token.

    The refresh token will be invalidated. The access token will remain
    valid until it expires (typically 30 minutes).
    """
    auth_service = AuthService(session)
    await auth_service.logout(logout_request.refresh_token)
    return None


@router.post("/logout-all", status_code=204)
async def logout_all(
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """Logout from all devices.

    Revokes all refresh tokens for the current user. Requires authentication.
    """
    auth_service = AuthService(session)
    await auth_service.logout_all(current_user.id)
    return None


# ============================================================================
# PROTECTED ENDPOINTS
# ============================================================================

@router.get("/me", response_model=User)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current user info.

    Returns information about the currently authenticated user.
    """
    return current_user


@router.post("/organizations", response_model=Organization, status_code=201)
async def create_organization(
    org_data: OrganizationCreate,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(require_admin)
):
    """Create an organization.

    Requires admin role.
    """
    org_service = OrganizationService(session)

    try:
        org = await org_service.create_organization(org_data)
        return org
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/organizations", response_model=List[Organization])
async def list_organizations(
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """List organizations.

    Returns all organizations the current user has access to.
    """
    org_service = OrganizationService(session)
    return await org_service.list_organizations()


@router.get("/organizations/{org_id}", response_model=Organization)
async def get_organization(
    org_id: UUID,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """Get an organization by ID."""
    org_service = OrganizationService(session)
    org = await org_service.get_organization(org_id)

    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    return org


# ============================================================================
# API TOKEN ENDPOINTS (Placeholder - requires api_tokens table)
# ============================================================================

@router.post("/tokens", response_model=APIToken, status_code=201)
async def create_api_token(
    token_data: APITokenCreate,
    current_user: User = Depends(get_current_user)
):
    """Create an API token.

    Note: This endpoint is not yet implemented. Requires api_tokens table.
    """
    raise HTTPException(
        status_code=501,
        detail="API tokens not yet implemented. Use JWT authentication."
    )


@router.get("/tokens", response_model=List[APIToken])
async def list_api_tokens(current_user: User = Depends(get_current_user)):
    """List API tokens.

    Note: This endpoint is not yet implemented. Requires api_tokens table.
    """
    raise HTTPException(
        status_code=501,
        detail="API tokens not yet implemented. Use JWT authentication."
    )


@router.delete("/tokens/{token_id}", status_code=204)
async def revoke_api_token(
    token_id: UUID,
    current_user: User = Depends(get_current_user)
):
    """Revoke an API token.

    Note: This endpoint is not yet implemented. Requires api_tokens table.
    """
    raise HTTPException(
        status_code=501,
        detail="API tokens not yet implemented. Use JWT authentication."
    )
