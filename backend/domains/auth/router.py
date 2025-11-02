"""Auth API router."""
from fastapi import APIRouter, HTTPException, Depends
from typing import List
from uuid import UUID
from domains.auth.models import (
    User, UserCreate, UserLogin, Token, Organization, OrganizationCreate,
    APIToken, APITokenCreate
)
from domains.auth.service import AuthService, OrganizationService, TokenService

router = APIRouter(prefix="/auth", tags=["auth"])

auth_service = AuthService()
org_service = OrganizationService()
token_service = TokenService()


# TODO: Add authentication dependencies
# def get_current_user() -> User:
#     """Get current authenticated user."""
#     pass

# def get_current_org() -> Organization:
#     """Get current organization context."""
#     pass


@router.post("/register", response_model=User, status_code=201)
async def register(user_data: UserCreate):
    """Register a new user."""
    raise HTTPException(status_code=501, detail="Not implemented")


@router.post("/login", response_model=Token)
async def login(login_data: UserLogin):
    """Login and get access token."""
    raise HTTPException(status_code=501, detail="Not implemented")


@router.get("/me", response_model=User)
async def get_current_user():
    """Get current user info."""
    # TODO: Use Depends(get_current_user)
    raise HTTPException(status_code=501, detail="Not implemented")


@router.post("/organizations", response_model=Organization, status_code=201)
async def create_organization(org_data: OrganizationCreate):
    """Create an organization."""
    raise HTTPException(status_code=501, detail="Not implemented")


@router.get("/organizations", response_model=List[Organization])
async def list_organizations():
    """List organizations."""
    raise HTTPException(status_code=501, detail="Not implemented")


@router.post("/tokens", response_model=APIToken, status_code=201)
async def create_api_token(token_data: APITokenCreate):
    """Create an API token."""
    # TODO: Return token only once on creation
    raise HTTPException(status_code=501, detail="Not implemented")


@router.get("/tokens", response_model=List[APIToken])
async def list_api_tokens():
    """List API tokens."""
    raise HTTPException(status_code=501, detail="Not implemented")


@router.delete("/tokens/{token_id}", status_code=204)
async def revoke_api_token(token_id: UUID):
    """Revoke an API token."""
    raise HTTPException(status_code=501, detail="Not implemented")

