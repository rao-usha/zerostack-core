"""Persona API router - manage user personas, assignments, and access patterns."""
import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from core.config import settings
from .models import (
    Persona, PersonaCreate, PersonaUpdate, PersonaStatus, RoleType,
    PersonaListResponse, PersonaVersion, PersonaVersionListResponse,
    PersonaAssignment, PersonaAssignmentCreate, PersonaAssignmentListResponse,
    AccessCheckRequest, AccessCheckResult
)
from .service import PersonaService, PersonaAssignmentService, AccessCheckService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/personas", tags=["personas"])


# ============================================================================
# SESSION DEPENDENCY
# ============================================================================

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


# ============================================================================
# ROLE TYPES (Static endpoint)
# ============================================================================

@router.get("/role-types", response_model=List[dict])
async def list_role_types():
    """List available persona role types."""
    return [
        {"id": RoleType.ANALYST.value, "name": "Data Analyst", "description": "Analyzes data and creates reports"},
        {"id": RoleType.ENGINEER.value, "name": "Data Engineer", "description": "Builds and maintains data pipelines"},
        {"id": RoleType.SCIENTIST.value, "name": "Data Scientist", "description": "Develops ML models and experiments"},
        {"id": RoleType.BUSINESS_USER.value, "name": "Business User", "description": "Consumes data for business decisions"},
        {"id": RoleType.ADMIN.value, "name": "Administrator", "description": "Full system access and configuration"},
        {"id": RoleType.VIEWER.value, "name": "Viewer", "description": "Read-only access to data"},
        {"id": RoleType.CUSTOM.value, "name": "Custom", "description": "Custom role with specific permissions"}
    ]


# ============================================================================
# PERSONA CRUD ENDPOINTS
# ============================================================================

@router.post("", response_model=Persona, status_code=201)
async def create_persona(
    persona: PersonaCreate,
    session: AsyncSession = Depends(get_async_session)
):
    """Create a new persona.

    Personas define user types with specific access patterns, preferences, and defaults.
    """
    service = PersonaService(session)
    return await service.create_persona(persona)


@router.get("", response_model=PersonaListResponse)
async def list_personas(
    status: Optional[PersonaStatus] = Query(None, description="Filter by status"),
    role_type: Optional[RoleType] = Query(None, description="Filter by role type"),
    department: Optional[str] = Query(None, description="Filter by department"),
    session: AsyncSession = Depends(get_async_session)
):
    """List all personas with optional filters."""
    service = PersonaService(session)
    personas = await service.list_personas(
        status=status,
        role_type=role_type,
        department=department
    )
    return PersonaListResponse(personas=personas, total=len(personas))


@router.get("/{persona_id}", response_model=Persona)
async def get_persona(
    persona_id: UUID,
    session: AsyncSession = Depends(get_async_session)
):
    """Get a specific persona by ID."""
    service = PersonaService(session)
    persona = await service.get_persona(persona_id)
    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")
    return persona


@router.put("/{persona_id}", response_model=Persona)
async def update_persona(
    persona_id: UUID,
    update: PersonaUpdate,
    change_reason: Optional[str] = Query(None, description="Reason for the change"),
    session: AsyncSession = Depends(get_async_session)
):
    """Update a persona.

    Changes are versioned automatically. Provide a change_reason for audit purposes.
    """
    service = PersonaService(session)

    existing = await service.get_persona(persona_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Persona not found")

    return await service.update_persona(persona_id, update, change_reason=change_reason)


@router.delete("/{persona_id}", status_code=204)
async def delete_persona(
    persona_id: UUID,
    session: AsyncSession = Depends(get_async_session)
):
    """Delete (archive) a persona.

    Personas are soft-deleted by changing status to 'archived'.
    """
    service = PersonaService(session)
    success = await service.delete_persona(persona_id)
    if not success:
        raise HTTPException(status_code=404, detail="Persona not found")


@router.post("/{persona_id}/activate", response_model=Persona)
async def activate_persona(
    persona_id: UUID,
    session: AsyncSession = Depends(get_async_session)
):
    """Activate a persona (change status from draft to active)."""
    service = PersonaService(session)

    existing = await service.get_persona(persona_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Persona not found")

    if existing.status == PersonaStatus.ARCHIVED:
        raise HTTPException(status_code=400, detail="Cannot activate an archived persona")

    update = PersonaUpdate(status=PersonaStatus.ACTIVE)
    return await service.update_persona(persona_id, update, change_reason="Activated persona")


# ============================================================================
# VERSION ENDPOINTS
# ============================================================================

@router.get("/{persona_id}/versions", response_model=PersonaVersionListResponse)
async def get_persona_versions(
    persona_id: UUID,
    session: AsyncSession = Depends(get_async_session)
):
    """Get all versions of a persona."""
    service = PersonaService(session)

    # Verify persona exists
    persona = await service.get_persona(persona_id)
    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")

    versions = await service.get_persona_versions(persona_id)
    return PersonaVersionListResponse(versions=versions, total=len(versions))


@router.get("/{persona_id}/versions/{version}", response_model=PersonaVersion)
async def get_persona_version(
    persona_id: UUID,
    version: str,
    session: AsyncSession = Depends(get_async_session)
):
    """Get a specific version of a persona."""
    service = PersonaService(session)

    version_record = await service.get_specific_version(persona_id, version)
    if not version_record:
        raise HTTPException(status_code=404, detail="Version not found")

    return version_record


# ============================================================================
# ASSIGNMENT ENDPOINTS
# ============================================================================

@router.post("/assignments", response_model=PersonaAssignment, status_code=201)
async def assign_persona(
    assignment: PersonaAssignmentCreate,
    assigned_by: Optional[UUID] = Query(None, description="User making the assignment"),
    session: AsyncSession = Depends(get_async_session)
):
    """Assign a persona to a user.

    A user can have multiple personas, but only one can be marked as primary.
    """
    # Verify persona exists
    persona_service = PersonaService(session)
    persona = await persona_service.get_persona(assignment.persona_id)
    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")

    if persona.status != PersonaStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="Can only assign active personas")

    assignment_service = PersonaAssignmentService(session)
    return await assignment_service.assign_persona(assignment, assigned_by=assigned_by)


@router.get("/assignments/user/{user_id}", response_model=PersonaAssignmentListResponse)
async def get_user_personas(
    user_id: UUID,
    session: AsyncSession = Depends(get_async_session)
):
    """Get all persona assignments for a user."""
    service = PersonaAssignmentService(session)
    assignments = await service.get_user_personas(user_id)
    return PersonaAssignmentListResponse(assignments=assignments, total=len(assignments))


@router.get("/{persona_id}/assignments", response_model=PersonaAssignmentListResponse)
async def get_persona_users(
    persona_id: UUID,
    session: AsyncSession = Depends(get_async_session)
):
    """Get all users assigned to a persona."""
    # Verify persona exists
    persona_service = PersonaService(session)
    persona = await persona_service.get_persona(persona_id)
    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")

    assignment_service = PersonaAssignmentService(session)
    assignments = await assignment_service.get_persona_users(persona_id)
    return PersonaAssignmentListResponse(assignments=assignments, total=len(assignments))


@router.delete("/assignments/{assignment_id}", status_code=204)
async def remove_assignment(
    assignment_id: UUID,
    session: AsyncSession = Depends(get_async_session)
):
    """Remove a persona assignment."""
    service = PersonaAssignmentService(session)
    success = await service.remove_assignment(assignment_id)
    if not success:
        raise HTTPException(status_code=404, detail="Assignment not found")


# ============================================================================
# ACCESS CHECK ENDPOINTS
# ============================================================================

@router.post("/access-check", response_model=AccessCheckResult)
async def check_access(
    request: AccessCheckRequest,
    session: AsyncSession = Depends(get_async_session)
):
    """Check if a persona has access to a resource.

    Uses the persona's allowed/denied classifications and default resources
    to determine access.
    """
    service = AccessCheckService(session)
    return await service.check_access(request)
