"""Persona service - manage user personas, assignments, and access patterns.

Note: Uses the existing 'personas' table from db/models.py which has a simpler schema.
The constraints JSON field is used to store access patterns and preferences.
"""
import logging
import re
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime

from sqlalchemy import select, update, delete, and_
from sqlalchemy.ext.asyncio import AsyncSession

from .db_models import personas, persona_versions, persona_assignments
from .models import (
    Persona, PersonaCreate, PersonaUpdate, PersonaStatus, RoleType,
    PersonaVersion, PersonaAssignment, PersonaAssignmentCreate,
    AccessCheckRequest, AccessCheckResult
)

logger = logging.getLogger(__name__)


def _increment_version(version: str) -> str:
    """Increment semantic version (e.g., 1.0.0 -> 1.0.1)."""
    match = re.match(r'^(\d+)\.(\d+)\.(\d+)$', version)
    if match:
        major, minor, patch = match.groups()
        return f"{major}.{minor}.{int(patch) + 1}"
    return "1.0.1"


class PersonaService:
    """Persona management service.

    The existing personas table has: id, org_id, name, description, constraints, created_at
    We store extended fields in the 'constraints' JSON field.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_persona(
        self,
        persona_data: PersonaCreate,
        created_by: Optional[UUID] = None,
        org_id: Optional[UUID] = None
    ) -> Persona:
        """Create a new persona."""
        persona_id = uuid4()

        # Store extended fields in constraints JSON
        constraints = {
            "status": PersonaStatus.DRAFT.value,
            "version": "1.0.0",
            "role_type": persona_data.role_type.value if persona_data.role_type else None,
            "department": persona_data.department,
            "default_datasets": [str(d) for d in persona_data.default_datasets],
            "default_tables": persona_data.default_tables,
            "allowed_classifications": persona_data.allowed_classifications,
            "denied_classifications": persona_data.denied_classifications,
            "preferences": persona_data.preferences,
            "default_dashboard_id": str(persona_data.default_dashboard_id) if persona_data.default_dashboard_id else None,
            "metadata": persona_data.metadata,
            "tags": persona_data.tags,
            "created_by": str(created_by) if created_by else None,
        }

        await self.session.execute(
            personas.insert().values(
                id=persona_id,
                org_id=org_id or uuid4(),  # Default org if not provided
                name=persona_data.name,
                description=persona_data.description,
                constraints=constraints
            )
        )

        # Create initial version
        await self._create_version(
            persona_id=persona_id,
            version="1.0.0",
            snapshot={"name": persona_data.name, "description": persona_data.description, **constraints},
            changes={"action": "created"},
            change_reason="Initial creation",
            created_by=created_by
        )

        logger.info(f"Created persona {persona_id}: {persona_data.name}")
        return await self.get_persona(persona_id)

    async def get_persona(self, persona_id: UUID) -> Optional[Persona]:
        """Get a persona by ID."""
        result = await self.session.execute(
            select(personas).where(personas.c.id == persona_id)
        )
        row = result.fetchone()

        if not row:
            return None

        return self._row_to_persona(row)

    async def list_personas(
        self,
        org_id: Optional[UUID] = None,
        status: Optional[PersonaStatus] = None,
        role_type: Optional[RoleType] = None,
        department: Optional[str] = None
    ) -> List[Persona]:
        """List personas with optional filters."""
        stmt = select(personas)

        if org_id:
            stmt = stmt.where(personas.c.org_id == org_id)

        stmt = stmt.order_by(personas.c.name)

        result = await self.session.execute(stmt)
        rows = result.fetchall()

        # Apply JSON-based filters in memory
        personas_list = [self._row_to_persona(row) for row in rows]

        if status:
            personas_list = [p for p in personas_list if p.status == status]
        if role_type:
            personas_list = [p for p in personas_list if p.role_type == role_type]
        if department:
            personas_list = [p for p in personas_list if p.department == department]

        return personas_list

    async def update_persona(
        self,
        persona_id: UUID,
        updates: PersonaUpdate,
        updated_by: Optional[UUID] = None,
        change_reason: Optional[str] = None
    ) -> Optional[Persona]:
        """Update a persona and create a new version."""
        # Get current persona
        current = await self.get_persona(persona_id)
        if not current:
            return None

        # Get current row to update constraints
        result = await self.session.execute(
            select(personas).where(personas.c.id == persona_id)
        )
        row = result.fetchone()
        constraints = dict(row.constraints) if row.constraints else {}

        update_values = {}
        changes = {}

        if updates.name is not None and updates.name != current.name:
            update_values["name"] = updates.name
            changes["name"] = {"old": current.name, "new": updates.name}

        if updates.description is not None and updates.description != current.description:
            update_values["description"] = updates.description
            changes["description"] = {"old": current.description, "new": updates.description}

        # Update constraints JSON
        if updates.status is not None and updates.status != current.status:
            constraints["status"] = updates.status.value
            changes["status"] = {"old": current.status.value, "new": updates.status.value}

        if updates.role_type is not None:
            constraints["role_type"] = updates.role_type.value
            changes["role_type"] = {"new": updates.role_type.value}

        if updates.department is not None:
            constraints["department"] = updates.department
            changes["department"] = {"new": updates.department}

        if updates.default_datasets is not None:
            constraints["default_datasets"] = [str(d) for d in updates.default_datasets]
            changes["default_datasets"] = {"updated": True}

        if updates.default_tables is not None:
            constraints["default_tables"] = updates.default_tables
            changes["default_tables"] = {"updated": True}

        if updates.allowed_classifications is not None:
            constraints["allowed_classifications"] = updates.allowed_classifications
            changes["allowed_classifications"] = {"updated": True}

        if updates.denied_classifications is not None:
            constraints["denied_classifications"] = updates.denied_classifications
            changes["denied_classifications"] = {"updated": True}

        if updates.preferences is not None:
            constraints["preferences"] = updates.preferences
            changes["preferences"] = {"updated": True}

        if updates.default_dashboard_id is not None:
            constraints["default_dashboard_id"] = str(updates.default_dashboard_id)
            changes["default_dashboard_id"] = {"updated": True}

        if updates.pinned_queries is not None:
            constraints["pinned_queries"] = [str(q) for q in updates.pinned_queries]
            changes["pinned_queries"] = {"updated": True}

        if updates.favorite_tables is not None:
            constraints["favorite_tables"] = updates.favorite_tables
            changes["favorite_tables"] = {"updated": True}

        if updates.metadata is not None:
            constraints["metadata"] = updates.metadata
            changes["metadata"] = {"updated": True}

        if updates.tags is not None:
            constraints["tags"] = updates.tags
            changes["tags"] = {"updated": True}

        # Increment version if there are changes
        if changes:
            new_version = _increment_version(current.version)
            constraints["version"] = new_version
            update_values["constraints"] = constraints

            await self.session.execute(
                update(personas).where(personas.c.id == persona_id).values(**update_values)
            )

            # Create version record
            updated_persona = await self.get_persona(persona_id)
            await self._create_version(
                persona_id=persona_id,
                version=new_version,
                snapshot=updated_persona.model_dump(mode="json") if updated_persona else {},
                changes=changes,
                change_reason=change_reason,
                created_by=updated_by
            )

            logger.info(f"Updated persona {persona_id} to version {new_version}")
            return updated_persona

        return current

    async def delete_persona(self, persona_id: UUID) -> bool:
        """Delete a persona (soft delete via archive)."""
        result = await self.session.execute(
            select(personas).where(personas.c.id == persona_id)
        )
        row = result.fetchone()
        if not row:
            return False

        constraints = dict(row.constraints) if row.constraints else {}
        constraints["status"] = PersonaStatus.ARCHIVED.value

        await self.session.execute(
            update(personas)
            .where(personas.c.id == persona_id)
            .values(constraints=constraints)
        )
        return True

    async def _create_version(
        self,
        persona_id: UUID,
        version: str,
        snapshot: Dict[str, Any],
        changes: Dict[str, Any],
        change_reason: Optional[str],
        created_by: Optional[UUID]
    ) -> None:
        """Create a version record."""
        # Convert any UUID objects in snapshot to strings for JSON storage
        def serialize(obj):
            if isinstance(obj, UUID):
                return str(obj)
            if isinstance(obj, datetime):
                return obj.isoformat()
            if isinstance(obj, dict):
                return {k: serialize(v) for k, v in obj.items()}
            if isinstance(obj, list):
                return [serialize(v) for v in obj]
            return obj

        await self.session.execute(
            persona_versions.insert().values(
                id=uuid4(),
                persona_id=persona_id,
                version=version,
                snapshot=serialize(snapshot),
                changes=changes,
                change_reason=change_reason,
                created_by=created_by
            )
        )

    async def get_persona_versions(self, persona_id: UUID) -> List[PersonaVersion]:
        """Get all versions of a persona."""
        result = await self.session.execute(
            select(persona_versions)
            .where(persona_versions.c.persona_id == persona_id)
            .order_by(persona_versions.c.created_at.desc())
        )
        rows = result.fetchall()

        return [
            PersonaVersion(
                id=row.id,
                persona_id=row.persona_id,
                version=row.version,
                snapshot=row.snapshot or {},
                changes=row.changes or {},
                change_reason=row.change_reason,
                created_by=row.created_by,
                created_at=row.created_at
            )
            for row in rows
        ]

    async def get_specific_version(self, persona_id: UUID, version: str) -> Optional[PersonaVersion]:
        """Get a specific version of a persona."""
        result = await self.session.execute(
            select(persona_versions).where(
                and_(
                    persona_versions.c.persona_id == persona_id,
                    persona_versions.c.version == version
                )
            )
        )
        row = result.fetchone()

        if not row:
            return None

        return PersonaVersion(
            id=row.id,
            persona_id=row.persona_id,
            version=row.version,
            snapshot=row.snapshot or {},
            changes=row.changes or {},
            change_reason=row.change_reason,
            created_by=row.created_by,
            created_at=row.created_at
        )

    def _row_to_persona(self, row) -> Persona:
        """Convert a database row to a Persona model."""
        constraints = row.constraints or {}

        return Persona(
            id=row.id,
            name=row.name,
            description=row.description,
            status=PersonaStatus(constraints.get("status", "draft")),
            version=constraints.get("version", "1.0.0"),
            role_type=RoleType(constraints["role_type"]) if constraints.get("role_type") else None,
            department=constraints.get("department"),
            default_datasets=[UUID(d) for d in constraints.get("default_datasets", []) if d],
            default_tables=constraints.get("default_tables", []),
            allowed_classifications=constraints.get("allowed_classifications", []),
            denied_classifications=constraints.get("denied_classifications", []),
            preferences=constraints.get("preferences", {}),
            default_dashboard_id=UUID(constraints["default_dashboard_id"]) if constraints.get("default_dashboard_id") else None,
            pinned_queries=[UUID(q) for q in constraints.get("pinned_queries", []) if q],
            favorite_tables=constraints.get("favorite_tables", []),
            metadata=constraints.get("metadata", {}),
            tags=constraints.get("tags", []),
            created_by=UUID(constraints["created_by"]) if constraints.get("created_by") else None,
            org_id=row.org_id,
            created_at=row.created_at,
            updated_at=row.created_at  # Original table doesn't have updated_at
        )


class PersonaAssignmentService:
    """Service for managing persona assignments to users."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def assign_persona(
        self,
        assignment: PersonaAssignmentCreate,
        assigned_by: Optional[UUID] = None
    ) -> PersonaAssignment:
        """Assign a persona to a user."""
        assignment_id = uuid4()

        # If this is primary, unset any existing primary for this user
        if assignment.is_primary:
            await self.session.execute(
                update(persona_assignments)
                .where(persona_assignments.c.user_id == assignment.user_id)
                .values(is_primary="N")
            )

        await self.session.execute(
            persona_assignments.insert().values(
                id=assignment_id,
                persona_id=assignment.persona_id,
                user_id=assignment.user_id,
                is_primary="Y" if assignment.is_primary else "N",
                assigned_by=assigned_by,
                expires_at=assignment.expires_at,
                notes=assignment.notes
            )
        )

        return await self.get_assignment(assignment_id)

    async def get_assignment(self, assignment_id: UUID) -> Optional[PersonaAssignment]:
        """Get an assignment by ID."""
        result = await self.session.execute(
            select(persona_assignments).where(persona_assignments.c.id == assignment_id)
        )
        row = result.fetchone()

        if not row:
            return None

        return PersonaAssignment(
            id=row.id,
            persona_id=row.persona_id,
            user_id=row.user_id,
            is_primary=row.is_primary == "Y",
            assigned_by=row.assigned_by,
            assigned_at=row.assigned_at,
            expires_at=row.expires_at,
            notes=row.notes
        )

    async def get_user_personas(self, user_id: UUID) -> List[PersonaAssignment]:
        """Get all persona assignments for a user."""
        result = await self.session.execute(
            select(persona_assignments)
            .where(persona_assignments.c.user_id == user_id)
            .order_by(persona_assignments.c.is_primary.desc(), persona_assignments.c.assigned_at.desc())
        )
        rows = result.fetchall()

        return [
            PersonaAssignment(
                id=row.id,
                persona_id=row.persona_id,
                user_id=row.user_id,
                is_primary=row.is_primary == "Y",
                assigned_by=row.assigned_by,
                assigned_at=row.assigned_at,
                expires_at=row.expires_at,
                notes=row.notes
            )
            for row in rows
        ]

    async def get_persona_users(self, persona_id: UUID) -> List[PersonaAssignment]:
        """Get all users assigned to a persona."""
        result = await self.session.execute(
            select(persona_assignments)
            .where(persona_assignments.c.persona_id == persona_id)
            .order_by(persona_assignments.c.assigned_at.desc())
        )
        rows = result.fetchall()

        return [
            PersonaAssignment(
                id=row.id,
                persona_id=row.persona_id,
                user_id=row.user_id,
                is_primary=row.is_primary == "Y",
                assigned_by=row.assigned_by,
                assigned_at=row.assigned_at,
                expires_at=row.expires_at,
                notes=row.notes
            )
            for row in rows
        ]

    async def remove_assignment(self, assignment_id: UUID) -> bool:
        """Remove a persona assignment."""
        result = await self.session.execute(
            delete(persona_assignments).where(persona_assignments.c.id == assignment_id)
        )
        return result.rowcount > 0


class AccessCheckService:
    """Service for checking persona-based access."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self._persona_service = PersonaService(session)

    async def check_access(self, request: AccessCheckRequest) -> AccessCheckResult:
        """Check if a persona has access to a resource."""
        persona = await self._persona_service.get_persona(request.persona_id)

        if not persona:
            return AccessCheckResult(
                allowed=False,
                persona_id=request.persona_id,
                resource_type=request.resource_type,
                resource_id=request.resource_id,
                resource_ref=request.resource_ref,
                reason="Persona not found"
            )

        if persona.status != PersonaStatus.ACTIVE:
            return AccessCheckResult(
                allowed=False,
                persona_id=request.persona_id,
                resource_type=request.resource_type,
                resource_id=request.resource_id,
                resource_ref=request.resource_ref,
                reason=f"Persona is {persona.status.value}"
            )

        matching_rules = []

        # Check classification-based access
        if request.classification:
            if request.classification in persona.denied_classifications:
                return AccessCheckResult(
                    allowed=False,
                    persona_id=request.persona_id,
                    resource_type=request.resource_type,
                    resource_id=request.resource_id,
                    resource_ref=request.resource_ref,
                    reason=f"Classification '{request.classification}' is denied for this persona",
                    matching_rules=["denied_classification"]
                )

            if persona.allowed_classifications:
                if request.classification not in persona.allowed_classifications:
                    return AccessCheckResult(
                        allowed=False,
                        persona_id=request.persona_id,
                        resource_type=request.resource_type,
                        resource_id=request.resource_id,
                        resource_ref=request.resource_ref,
                        reason=f"Classification '{request.classification}' is not in allowed list",
                        matching_rules=["allowed_classification"]
                    )
                matching_rules.append("allowed_classification")

        # Check resource-specific access
        if request.resource_type == "dataset" and request.resource_id:
            if request.resource_id in persona.default_datasets:
                matching_rules.append("default_dataset")

        if request.resource_type == "table" and request.resource_ref:
            if request.resource_ref in persona.default_tables:
                matching_rules.append("default_table")
            if request.resource_ref in persona.favorite_tables:
                matching_rules.append("favorite_table")

        # Default: allow if no explicit denial
        return AccessCheckResult(
            allowed=True,
            persona_id=request.persona_id,
            resource_type=request.resource_type,
            resource_id=request.resource_id,
            resource_ref=request.resource_ref,
            reason="Access allowed" if matching_rules else "No restrictions apply",
            matching_rules=matching_rules
        )
