"""Highlighted Datasets API router."""
import logging
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, UploadFile, File, Depends
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from core.config import settings
from services.object_store import ObjectStoreClient, ObjectStorePaths
from services.interaction_logger import InteractionLogger, EventType
from .service import HighlightedDatasetService
from .models import (
    HighlightedDatasetResponse,
    HighlightedDatasetListResponse,
    DatasetVersionResponse,
    DatasetVersionListResponse,
    HighlightedDatasetCreate,
    HighlightedDatasetUpdate,
    ResolveRequest,
    ResolveResponse,
    FileUploadResponse,
    UploadCompleteRequest,
    UploadCompleteResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/highlighted-datasets", tags=["highlighted-datasets"])


# Session dependency
async def get_async_session():
    """Get async database session."""
    # Create async engine
    async_url = settings.database_url.replace('postgresql+psycopg', 'postgresql+asyncpg')
    if 'asyncpg' not in async_url:
        async_url = settings.database_url.replace('postgresql://', 'postgresql+asyncpg://')
    
    engine = create_async_engine(async_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        yield session
        await session.commit()


# ========================================
# List & Get Endpoints
# ========================================

@router.get("", response_model=HighlightedDatasetListResponse)
async def list_highlighted_datasets(
    availability_state: Optional[str] = Query(None, description="Filter by availability state"),
    tags: Optional[str] = Query(None, description="Comma-separated tags to filter by"),
    limit: int = Query(100, le=500),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_async_session)
):
    """
    List all highlighted datasets in the catalog.
    
    Returns datasets with their current availability state.
    """
    service = HighlightedDatasetService(session)
    
    tag_list = [t.strip() for t in tags.split(',')] if tags else None
    datasets, total = await service.list_datasets(
        availability_state=availability_state,
        tags=tag_list,
        limit=limit,
        offset=offset
    )
    
    # Build response with latest version info
    response_datasets = []
    for ds in datasets:
        latest_version = await service.get_latest_version(ds.id)
        response_datasets.append(
            HighlightedDatasetResponse(
                id=ds.id,
                display_name=ds.display_name,
                description=ds.description,
                tags=ds.tags,
                source_type=ds.source_type,
                availability_state=ds.availability_state,
                license_notes=ds.license_notes,
                created_at=ds.created_at,
                updated_at=ds.updated_at,
                latest_version=DatasetVersionResponse.model_validate(latest_version) if latest_version else None
            )
        )
    
    return HighlightedDatasetListResponse(datasets=response_datasets, total=total)


@router.get("/{dataset_id}", response_model=HighlightedDatasetResponse)
async def get_highlighted_dataset(
    dataset_id: str,
    session: AsyncSession = Depends(get_async_session)
):
    """Get a specific highlighted dataset by ID."""
    service = HighlightedDatasetService(session)
    dataset = await service.get_dataset(dataset_id)
    
    if not dataset:
        raise HTTPException(status_code=404, detail=f"Dataset {dataset_id} not found")
    
    latest_version = await service.get_latest_version(dataset_id)
    
    return HighlightedDatasetResponse(
        id=dataset.id,
        display_name=dataset.display_name,
        description=dataset.description,
        tags=dataset.tags,
        source_type=dataset.source_type,
        availability_state=dataset.availability_state,
        license_notes=dataset.license_notes,
        created_at=dataset.created_at,
        updated_at=dataset.updated_at,
        latest_version=DatasetVersionResponse.model_validate(latest_version) if latest_version else None
    )


@router.get("/{dataset_id}/versions", response_model=DatasetVersionListResponse)
async def list_dataset_versions(
    dataset_id: str,
    session: AsyncSession = Depends(get_async_session)
):
    """List all versions for a highlighted dataset."""
    service = HighlightedDatasetService(session)
    
    dataset = await service.get_dataset(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail=f"Dataset {dataset_id} not found")
    
    versions = await service.list_versions(dataset_id)
    
    return DatasetVersionListResponse(
        versions=[DatasetVersionResponse.model_validate(v) for v in versions],
        total=len(versions)
    )


@router.get("/{dataset_id}/versions/{version_id}", response_model=DatasetVersionResponse)
async def get_dataset_version(
    dataset_id: str,
    version_id: UUID,
    session: AsyncSession = Depends(get_async_session)
):
    """Get a specific version of a dataset."""
    service = HighlightedDatasetService(session)
    
    version = await service.get_version(version_id)
    if not version or version.highlighted_dataset_id != dataset_id:
        raise HTTPException(status_code=404, detail="Version not found")
    
    return DatasetVersionResponse.model_validate(version)


# ========================================
# Create & Update Endpoints
# ========================================

@router.post("", response_model=HighlightedDatasetResponse, status_code=201)
async def create_highlighted_dataset(
    request: HighlightedDatasetCreate,
    session: AsyncSession = Depends(get_async_session)
):
    """Create a new highlighted dataset entry."""
    service = HighlightedDatasetService(session)
    
    # Check if already exists
    existing = await service.get_dataset(request.id)
    if existing:
        raise HTTPException(status_code=409, detail=f"Dataset {request.id} already exists")
    
    dataset = await service.create_dataset(
        id=request.id,
        display_name=request.display_name,
        source_type=request.source_type.value,
        description=request.description,
        tags=request.tags,
        resolver_config=request.resolver_config,
        license_notes=request.license_notes
    )
    
    return HighlightedDatasetResponse(
        id=dataset.id,
        display_name=dataset.display_name,
        description=dataset.description,
        tags=dataset.tags,
        source_type=dataset.source_type,
        availability_state=dataset.availability_state,
        license_notes=dataset.license_notes,
        created_at=dataset.created_at,
        updated_at=dataset.updated_at,
        latest_version=None
    )


@router.put("/{dataset_id}", response_model=HighlightedDatasetResponse)
async def update_highlighted_dataset(
    dataset_id: str,
    request: HighlightedDatasetUpdate,
    session: AsyncSession = Depends(get_async_session)
):
    """Update a highlighted dataset."""
    service = HighlightedDatasetService(session)
    
    dataset = await service.get_dataset(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail=f"Dataset {dataset_id} not found")
    
    updated = await service.update_dataset(
        dataset_id,
        display_name=request.display_name,
        description=request.description,
        tags=request.tags,
        resolver_config=request.resolver_config,
        license_notes=request.license_notes
    )
    
    latest_version = await service.get_latest_version(dataset_id)
    
    return HighlightedDatasetResponse(
        id=updated.id,
        display_name=updated.display_name,
        description=updated.description,
        tags=updated.tags,
        source_type=updated.source_type,
        availability_state=updated.availability_state,
        license_notes=updated.license_notes,
        created_at=updated.created_at,
        updated_at=updated.updated_at,
        latest_version=DatasetVersionResponse.model_validate(latest_version) if latest_version else None
    )


@router.delete("/{dataset_id}", status_code=204)
async def delete_highlighted_dataset(
    dataset_id: str,
    session: AsyncSession = Depends(get_async_session)
):
    """Delete a highlighted dataset."""
    service = HighlightedDatasetService(session)
    
    success = await service.delete_dataset(dataset_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Dataset {dataset_id} not found")


# ========================================
# Resolve & Upload Endpoints
# ========================================

@router.post("/{dataset_id}/resolve", response_model=ResolveResponse)
async def resolve_dataset(
    dataset_id: str,
    request: ResolveRequest = ResolveRequest(),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Resolve a dataset - check availability and return version info.
    
    If the dataset is NOT_PRESENT and requires manual upload, returns
    instructions. If HTTP download is configured, triggers download.
    """
    service = HighlightedDatasetService(session)
    interaction_logger = InteractionLogger(session)
    
    # Log the resolve attempt
    await interaction_logger.log(
        EventType.DATASET_RESOLVE,
        refs={'dataset_id': dataset_id}
    )
    
    version, message = await service.resolve(
        dataset_id,
        force_refresh=request.force_refresh,
        credentials=request.credentials
    )
    
    dataset = await service.get_dataset(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail=f"Dataset {dataset_id} not found")
    
    return ResolveResponse(
        dataset_id=dataset_id,
        availability_state=dataset.availability_state,
        version=DatasetVersionResponse.model_validate(version) if version else None,
        message=message
    )


@router.post("/{dataset_id}/upload", response_model=FileUploadResponse)
async def upload_dataset_file(
    dataset_id: str,
    file: UploadFile = File(...),
    version_label: str = Query("v1", description="Version label for this upload"),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Upload a file for a highlighted dataset.
    
    Call this endpoint for each file needed. After all files are uploaded,
    call POST /{dataset_id}/upload/complete to finalize the version.
    """
    service = HighlightedDatasetService(session)
    storage = ObjectStoreClient.get_instance()
    
    dataset = await service.get_dataset(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail=f"Dataset {dataset_id} not found")
    
    # Read file content
    content = await file.read()
    
    # Determine storage path
    file_key = ObjectStorePaths.dataset_raw_file(dataset_id, version_label, file.filename)
    
    # Upload to storage
    storage_uri = storage.put_bytes(file_key, content, content_type=file.content_type or 'application/octet-stream')
    
    logger.info(f"Uploaded {file.filename} ({len(content)} bytes) to {storage_uri}")
    
    return FileUploadResponse(
        filename=file.filename,
        size_bytes=len(content),
        storage_path=file_key,
        uploaded=True
    )


@router.post("/{dataset_id}/upload/complete", response_model=UploadCompleteResponse)
async def complete_dataset_upload(
    dataset_id: str,
    request: UploadCompleteRequest,
    session: AsyncSession = Depends(get_async_session)
):
    """
    Complete the upload process and create a new version.
    
    This scans the uploaded files and creates the manifest.
    """
    service = HighlightedDatasetService(session)
    storage = ObjectStoreClient.get_instance()
    interaction_logger = InteractionLogger(session)
    
    dataset = await service.get_dataset(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail=f"Dataset {dataset_id} not found")
    
    # Log ingest start
    await interaction_logger.log(
        EventType.INGEST_START,
        refs={'dataset_id': dataset_id}
    )
    
    # List uploaded files
    prefix = ObjectStorePaths.dataset_raw(dataset_id, request.version_label)
    objects = storage.list_objects(prefix)
    
    if not objects:
        raise HTTPException(status_code=400, detail="No files found. Upload files first.")
    
    # Build file list for manifest
    files = []
    for obj in objects:
        key = obj['Key']
        filename = key.split('/')[-1]
        files.append({
            'path': f"raw/{filename}",
            'bytes': obj.get('Size', 0),
            'key': key
        })
    
    # Finalize and create version
    version = await service.finalize_upload(
        dataset_id=dataset_id,
        version_label=request.version_label,
        files=files,
        created_by=None  # TODO: Get from auth
    )
    
    # Log ingest complete
    await interaction_logger.log(
        EventType.INGEST_COMPLETE,
        refs={'dataset_id': dataset_id, 'version_id': str(version.id)}
    )
    
    return UploadCompleteResponse(
        dataset_id=dataset_id,
        version=DatasetVersionResponse.model_validate(version),
        message=f"Created version {request.version_label} with {len(files)} files"
    )
