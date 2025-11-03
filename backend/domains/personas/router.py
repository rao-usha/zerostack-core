"""Persona API router."""
from fastapi import APIRouter, HTTPException
from typing import List, Optional
from uuid import UUID
from domains.personas.models import Persona, PersonaCreate, PersonaUpdate, PersonaVersion, PersonaStatus
from domains.personas.service import PersonaService

router = APIRouter(prefix="/personas", tags=["personas"])

persona_service = PersonaService()


@router.post("", status_code=201)
async def create_persona(persona: PersonaCreate):
    """
    Create a new persona.
    
    TODO: Store persona in database, validate constraints.
    """
    return {"persona_id": "per_stub", "status": "stub"}


@router.get("", response_model=List[Persona])
async def list_personas(status: Optional[PersonaStatus] = None):
    """List personas."""
    raise HTTPException(status_code=501, detail="Not implemented")


@router.get("/{persona_id}", response_model=Persona)
async def get_persona(persona_id: UUID):
    """Get a persona."""
    raise HTTPException(status_code=501, detail="Not implemented")


@router.put("/{persona_id}", response_model=Persona)
async def update_persona(persona_id: UUID, update: PersonaUpdate):
    """Update a persona."""
    raise HTTPException(status_code=501, detail="Not implemented")


@router.delete("/{persona_id}", status_code=204)
async def delete_persona(persona_id: UUID):
    """Delete a persona."""
    raise HTTPException(status_code=501, detail="Not implemented")


@router.post("/{persona_id}/versions", response_model=PersonaVersion, status_code=201)
async def version_persona(persona_id: UUID, new_version: str):
    """Create a new persona version."""
    raise HTTPException(status_code=501, detail="Not implemented")


@router.get("/{persona_id}/versions", response_model=List[PersonaVersion])
async def get_persona_versions(persona_id: UUID):
    """Get persona versions."""
    raise HTTPException(status_code=501, detail="Not implemented")

