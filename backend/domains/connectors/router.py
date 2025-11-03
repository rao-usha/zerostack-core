"""Connector API router."""
from fastapi import APIRouter, HTTPException, Depends
from typing import List
from uuid import UUID
from domains.connectors.models import Connector, ConnectorCreate, ConnectorUpdate, ConnectorTest
from domains.connectors.service import ConnectorRegistry

router = APIRouter(prefix="/connectors", tags=["connectors"])

# TODO: Add authentication dependency
# TODO: Add organization context dependency

connector_registry = ConnectorRegistry()


@router.get("", response_model=List[Connector])
async def list_connectors():
    """List all connectors."""
    # TODO: Add pagination, filtering
    raise HTTPException(status_code=501, detail="Not implemented")


@router.post("", response_model=Connector, status_code=201)
async def create_connector(connector: ConnectorCreate):
    """Create a new connector."""
    # TODO: Get user ID from auth context
    raise HTTPException(status_code=501, detail="Not implemented")


@router.get("/{connector_id}", response_model=Connector)
async def get_connector(connector_id: UUID):
    """Get a connector by ID."""
    raise HTTPException(status_code=501, detail="Not implemented")


@router.put("/{connector_id}", response_model=Connector)
async def update_connector(connector_id: UUID, update: ConnectorUpdate):
    """Update a connector."""
    raise HTTPException(status_code=501, detail="Not implemented")


@router.delete("/{connector_id}", status_code=204)
async def delete_connector(connector_id: UUID):
    """Delete a connector."""
    raise HTTPException(status_code=501, detail="Not implemented")


@router.post("/{connector_id}/test", response_model=ConnectorTest)
async def test_connector(connector_id: UUID):
    """Test a connector connection."""
    raise HTTPException(status_code=501, detail="Not implemented")

