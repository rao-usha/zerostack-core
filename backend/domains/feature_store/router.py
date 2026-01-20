"""Feature store API router."""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List
from uuid import UUID

from db_session import get_session
from sqlalchemy.orm import Session

from .service import FeatureStoreService
from .models import (
    # Entities
    EntityCreate, EntityUpdate, Entity, EntityListResponse,
    # Features
    FeatureDefinitionCreate, FeatureDefinitionUpdate, FeatureDefinition,
    FeatureDefinitionListResponse, FeatureDefinitionWithEntity,
    # Feature Sets
    FeatureSetCreate, FeatureSetUpdate, FeatureSet,
    FeatureSetListResponse, FeatureSetWithFeatures,
    # Actions
    AddFeaturesToSetRequest, RemoveFeaturesFromSetRequest,
)

router = APIRouter(prefix="/features", tags=["Feature Store"])


def get_service(session: Session = Depends(get_session)) -> FeatureStoreService:
    """Get feature store service."""
    return FeatureStoreService(session)


# ============================================================================
# Entity Endpoints
# ============================================================================

@router.post("/entities", response_model=Entity, status_code=201)
def create_entity(
    data: EntityCreate,
    service: FeatureStoreService = Depends(get_service),
):
    """Create a new feature entity."""
    # Check for duplicate name
    existing = service.get_entity_by_name(data.name)
    if existing:
        raise HTTPException(status_code=409, detail=f"Entity '{data.name}' already exists")

    result = service.create_entity(data)
    return result


@router.get("/entities", response_model=EntityListResponse)
def list_entities(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    service: FeatureStoreService = Depends(get_service),
):
    """List all feature entities."""
    items, total = service.list_entities(page=page, page_size=page_size)
    return EntityListResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/entities/{entity_id}", response_model=Entity)
def get_entity(
    entity_id: UUID,
    service: FeatureStoreService = Depends(get_service),
):
    """Get a feature entity by ID."""
    result = service.get_entity(entity_id)
    if not result:
        raise HTTPException(status_code=404, detail="Entity not found")
    return result


@router.put("/entities/{entity_id}", response_model=Entity)
def update_entity(
    entity_id: UUID,
    data: EntityUpdate,
    service: FeatureStoreService = Depends(get_service),
):
    """Update a feature entity."""
    result = service.update_entity(entity_id, data)
    if not result:
        raise HTTPException(status_code=404, detail="Entity not found")
    return result


@router.delete("/entities/{entity_id}", status_code=204)
def delete_entity(
    entity_id: UUID,
    service: FeatureStoreService = Depends(get_service),
):
    """Delete a feature entity."""
    if not service.delete_entity(entity_id):
        raise HTTPException(status_code=404, detail="Entity not found")


# ============================================================================
# Feature Definition Endpoints
# ============================================================================

@router.post("/definitions", response_model=FeatureDefinition, status_code=201)
def create_feature_definition(
    data: FeatureDefinitionCreate,
    service: FeatureStoreService = Depends(get_service),
):
    """Create a new feature definition."""
    # Verify entity exists if provided
    if data.entity_id:
        entity = service.get_entity(data.entity_id)
        if not entity:
            raise HTTPException(status_code=400, detail="Entity not found")

    # Check for duplicate name (same name, version 1)
    existing = service.get_feature_definition_by_name(data.name, version=1)
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Feature '{data.name}' already exists. Use POST /definitions/{{id}}/versions to create a new version."
        )

    result = service.create_feature_definition(data)
    return result


@router.get("/definitions", response_model=FeatureDefinitionListResponse)
def list_feature_definitions(
    entity_id: Optional[UUID] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    service: FeatureStoreService = Depends(get_service),
):
    """List feature definitions with optional filtering."""
    items, total = service.list_feature_definitions(
        entity_id=entity_id,
        status=status,
        search=search,
        page=page,
        page_size=page_size,
    )
    return FeatureDefinitionListResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/definitions/{feature_id}", response_model=FeatureDefinitionWithEntity)
def get_feature_definition(
    feature_id: UUID,
    service: FeatureStoreService = Depends(get_service),
):
    """Get a feature definition by ID."""
    result = service.get_feature_definition(feature_id)
    if not result:
        raise HTTPException(status_code=404, detail="Feature definition not found")

    # Include entity if present
    if result.get("entity_id"):
        entity = service.get_entity(result["entity_id"])
        result["entity"] = entity

    return result


@router.put("/definitions/{feature_id}", response_model=FeatureDefinition)
def update_feature_definition(
    feature_id: UUID,
    data: FeatureDefinitionUpdate,
    service: FeatureStoreService = Depends(get_service),
):
    """Update a feature definition (metadata only, not transformation code)."""
    result = service.update_feature_definition(feature_id, data)
    if not result:
        raise HTTPException(status_code=404, detail="Feature definition not found")
    return result


@router.post("/definitions/{feature_id}/versions", response_model=FeatureDefinition, status_code=201)
def create_feature_version(
    feature_id: UUID,
    transformation_code: str,
    description: Optional[str] = None,
    service: FeatureStoreService = Depends(get_service),
):
    """Create a new version of a feature definition with updated transformation code."""
    result = service.create_feature_version(feature_id, transformation_code, description)
    if not result:
        raise HTTPException(status_code=404, detail="Feature definition not found")
    return result


@router.delete("/definitions/{feature_id}", status_code=204)
def delete_feature_definition(
    feature_id: UUID,
    service: FeatureStoreService = Depends(get_service),
):
    """Delete a feature definition."""
    if not service.delete_feature_definition(feature_id):
        raise HTTPException(status_code=404, detail="Feature definition not found")


# ============================================================================
# Feature Set Endpoints
# ============================================================================

@router.post("/sets", response_model=FeatureSet, status_code=201)
def create_feature_set(
    data: FeatureSetCreate,
    service: FeatureStoreService = Depends(get_service),
):
    """Create a new feature set."""
    # Verify entity exists if provided
    if data.entity_id:
        entity = service.get_entity(data.entity_id)
        if not entity:
            raise HTTPException(status_code=400, detail="Entity not found")

    result = service.create_feature_set(data)
    return result


@router.get("/sets", response_model=FeatureSetListResponse)
def list_feature_sets(
    entity_id: Optional[UUID] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    service: FeatureStoreService = Depends(get_service),
):
    """List feature sets with optional filtering."""
    items, total = service.list_feature_sets(
        entity_id=entity_id,
        search=search,
        page=page,
        page_size=page_size,
    )
    return FeatureSetListResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/sets/{set_id}", response_model=FeatureSetWithFeatures)
def get_feature_set(
    set_id: UUID,
    service: FeatureStoreService = Depends(get_service),
):
    """Get a feature set by ID with its features."""
    result = service.get_feature_set_with_features(set_id)
    if not result:
        raise HTTPException(status_code=404, detail="Feature set not found")
    return result


@router.put("/sets/{set_id}", response_model=FeatureSet)
def update_feature_set(
    set_id: UUID,
    data: FeatureSetUpdate,
    service: FeatureStoreService = Depends(get_service),
):
    """Update a feature set."""
    result = service.update_feature_set(set_id, data)
    if not result:
        raise HTTPException(status_code=404, detail="Feature set not found")
    return result


@router.delete("/sets/{set_id}", status_code=204)
def delete_feature_set(
    set_id: UUID,
    service: FeatureStoreService = Depends(get_service),
):
    """Delete a feature set."""
    if not service.delete_feature_set(set_id):
        raise HTTPException(status_code=404, detail="Feature set not found")


@router.post("/sets/{set_id}/features")
def add_features_to_set(
    set_id: UUID,
    data: AddFeaturesToSetRequest,
    service: FeatureStoreService = Depends(get_service),
):
    """Add features to a feature set."""
    # Verify set exists
    if not service.get_feature_set(set_id):
        raise HTTPException(status_code=404, detail="Feature set not found")

    count = service.add_features_to_set(set_id, data.feature_ids)
    return {"added": count, "message": f"Added {count} features to set"}


@router.delete("/sets/{set_id}/features")
def remove_features_from_set(
    set_id: UUID,
    data: RemoveFeaturesFromSetRequest,
    service: FeatureStoreService = Depends(get_service),
):
    """Remove features from a feature set."""
    # Verify set exists
    if not service.get_feature_set(set_id):
        raise HTTPException(status_code=404, detail="Feature set not found")

    count = service.remove_features_from_set(set_id, data.feature_ids)
    return {"removed": count, "message": f"Removed {count} features from set"}
