"""Role-Based Access Control (RBAC) utilities.

Provides dependencies for protecting endpoints based on user roles.
"""
from functools import wraps
from typing import List, Callable, Optional

from fastapi import HTTPException, Depends, Request
from starlette.status import HTTP_403_FORBIDDEN

from domains.auth.models import User, Role
from core.auth_deps import get_current_user


# Role hierarchy - higher index = more permissions
ROLE_HIERARCHY = {
    Role.GUEST: 0,
    Role.VIEWER: 1,
    Role.ANALYST: 2,
    Role.DATA_SCIENTIST: 3,
    Role.ADMIN: 4,
}


def get_role_level(role: Role) -> int:
    """Get the permission level for a role."""
    return ROLE_HIERARCHY.get(role, 0)


class RoleChecker:
    """Dependency class for checking user roles.

    Usage:
        @router.get("/admin-only")
        async def admin_endpoint(user: User = Depends(require_admin)):
            ...

        @router.get("/analysts-plus")
        async def analyst_endpoint(user: User = Depends(require_role(Role.ANALYST))):
            ...
    """

    def __init__(
        self,
        allowed_roles: Optional[List[Role]] = None,
        min_role: Optional[Role] = None
    ):
        """
        Args:
            allowed_roles: Specific roles that are allowed (exact match)
            min_role: Minimum role level required (uses hierarchy)
        """
        self.allowed_roles = allowed_roles
        self.min_role = min_role

    async def __call__(self, user: User = Depends(get_current_user)) -> User:
        """Check if user has required role."""
        if not user:
            raise HTTPException(
                status_code=HTTP_403_FORBIDDEN,
                detail="Not authenticated"
            )

        # Check specific allowed roles
        if self.allowed_roles:
            if user.role not in self.allowed_roles:
                raise HTTPException(
                    status_code=HTTP_403_FORBIDDEN,
                    detail=f"Access denied. Required roles: {[r.value for r in self.allowed_roles]}"
                )

        # Check minimum role level
        if self.min_role:
            user_level = get_role_level(user.role)
            required_level = get_role_level(self.min_role)

            if user_level < required_level:
                raise HTTPException(
                    status_code=HTTP_403_FORBIDDEN,
                    detail=f"Access denied. Minimum role required: {self.min_role.value}"
                )

        return user


# Pre-configured dependencies for common use cases
require_admin = RoleChecker(allowed_roles=[Role.ADMIN])
require_data_scientist = RoleChecker(min_role=Role.DATA_SCIENTIST)
require_analyst = RoleChecker(min_role=Role.ANALYST)
require_viewer = RoleChecker(min_role=Role.VIEWER)


def require_role(role: Role) -> RoleChecker:
    """Create a dependency that requires at least the specified role.

    Uses role hierarchy, so admin can access analyst endpoints.

    Example:
        @router.get("/reports")
        async def get_reports(user: User = Depends(require_role(Role.ANALYST))):
            ...
    """
    return RoleChecker(min_role=role)


def require_any_role(*roles: Role) -> RoleChecker:
    """Create a dependency that requires any of the specified roles.

    Does NOT use hierarchy - exact role match required.

    Example:
        @router.post("/special")
        async def special(user: User = Depends(require_any_role(Role.ADMIN, Role.DATA_SCIENTIST))):
            ...
    """
    return RoleChecker(allowed_roles=list(roles))


# Middleware for setting user on request.state (useful for rate limiting)
async def set_user_on_request(
    request: Request,
    user: Optional[User] = Depends(get_current_user)
):
    """Middleware dependency that sets user on request.state.

    This allows other middleware (like rate limiting) to access the user.
    """
    if user:
        request.state.user = user
    return user
