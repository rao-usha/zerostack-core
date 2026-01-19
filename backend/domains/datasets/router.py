"""Dataset API router - File upload and dataset management."""
import logging
from typing import List, Optional
from uuid import UUID, uuid4
from datetime import datetime

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends, Query
from sqlalchemy import select, func, update, delete
from sqlmodel import Session

from db_session import get_session
from .db_models import datasets, dataset_versions
from .models import (
    Dataset, DatasetCreate, DatasetUpdate, DatasetVersion,
    DatasetUploadResponse, DatasetListResponse, DatasetVersionListResponse,
    DatasetPreviewResponse, DatasetDownloadResponse, DatasetStatus, DatasetSourceType,
    Transform, SyntheticDataRequest, SyntheticDataResult
)
from .storage import get_dataset_storage

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/datasets", tags=["datasets"])


@router.post("/upload", response_model=DatasetUploadResponse, status_code=201)
async def upload_dataset(
    name: str = Form(..., description="Dataset name"),
    description: Optional[str] = Form(None, description="Dataset description"),
    org_id: str = Form("default", description="Organization ID"),
    tags: Optional[str] = Form(None, description="Comma-separated tags"),
    file: UploadFile = File(..., description="Data file (CSV, Parquet, JSON, Excel)"),
    session: Session = Depends(get_session),
):
    """Upload a dataset file.

    Supported formats: CSV, Parquet, JSON/JSONL, Excel (xlsx/xls)

    The file will be:
    1. Streamed to object storage
    2. Converted to Parquet for efficient querying
    3. Schema will be automatically inferred
    4. SHA256 hash computed for versioning/deduplication
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    # Parse tags
    tag_list = [t.strip() for t in tags.split(",")] if tags else []

    # Generate IDs
    dataset_id = uuid4()
    version_id = uuid4()
    version_number = 1

    try:
        # Upload and process file
        storage = get_dataset_storage()
        storage_uri, sha256, size_bytes, row_count, column_count, schema = storage.upload_file(
            dataset_id=dataset_id,
            version_number=version_number,
            file_obj=file.file,
            original_filename=file.filename,
            target_format="parquet",
        )

        # Insert dataset record
        now = datetime.utcnow()
        session.execute(
            datasets.insert().values(
                id=dataset_id,
                name=name,
                description=description,
                org_id=org_id,
                tags=tag_list,
                source_type=DatasetSourceType.UPLOAD.value,
                current_version_id=version_id,
                current_version_number=version_number,
                storage_uri=storage_uri,
                storage_format="parquet",
                schema=schema,
                row_count=row_count,
                column_count=column_count,
                size_bytes=size_bytes,
                status=DatasetStatus.ACTIVE.value,
                created_at=now,
                updated_at=now,
            )
        )

        # Insert version record
        session.execute(
            dataset_versions.insert().values(
                id=version_id,
                dataset_id=dataset_id,
                version_number=version_number,
                sha256=sha256,
                storage_uri=storage_uri,
                storage_format="parquet",
                original_filename=file.filename,
                row_count=row_count,
                column_count=column_count,
                size_bytes=size_bytes,
                schema=schema,
                created_at=now,
            )
        )

        session.commit()

        logger.info(f"Uploaded dataset {dataset_id} ({row_count} rows, {column_count} cols)")

        # Build response
        dataset = Dataset(
            id=dataset_id,
            name=name,
            description=description,
            status=DatasetStatus.ACTIVE,
            source_type=DatasetSourceType.UPLOAD,
            schema=schema,
            row_count=row_count,
            column_count=column_count,
            size_bytes=size_bytes,
            storage_uri=storage_uri,
            storage_format="parquet",
            current_version_number=version_number,
            tags=tag_list,
            org_id=org_id,
            created_at=now,
            updated_at=now,
        )

        version = DatasetVersion(
            id=version_id,
            dataset_id=dataset_id,
            version_number=version_number,
            sha256=sha256,
            storage_uri=storage_uri,
            storage_format="parquet",
            original_filename=file.filename,
            row_count=row_count,
            column_count=column_count,
            size_bytes=size_bytes,
            schema=schema,
            created_at=now,
        )

        return DatasetUploadResponse(
            dataset=dataset,
            version=version,
            message=f"Successfully uploaded {file.filename} ({row_count:,} rows)",
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.post("/{dataset_id}/versions", response_model=DatasetVersion, status_code=201)
async def upload_new_version(
    dataset_id: UUID,
    notes: Optional[str] = Form(None, description="Version notes"),
    file: UploadFile = File(..., description="New data file"),
    session: Session = Depends(get_session),
):
    """Upload a new version of an existing dataset."""
    # Check dataset exists
    result = session.execute(
        select(datasets).where(datasets.c.id == dataset_id)
    )
    dataset_row = result.fetchone()
    if not dataset_row:
        raise HTTPException(status_code=404, detail="Dataset not found")

    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    # Get next version number
    version_number = (dataset_row.current_version_number or 0) + 1
    version_id = uuid4()

    try:
        storage = get_dataset_storage()
        storage_uri, sha256, size_bytes, row_count, column_count, schema = storage.upload_file(
            dataset_id=dataset_id,
            version_number=version_number,
            file_obj=file.file,
            original_filename=file.filename,
            target_format="parquet",
        )

        now = datetime.utcnow()

        # Insert version record
        session.execute(
            dataset_versions.insert().values(
                id=version_id,
                dataset_id=dataset_id,
                version_number=version_number,
                sha256=sha256,
                storage_uri=storage_uri,
                storage_format="parquet",
                original_filename=file.filename,
                row_count=row_count,
                column_count=column_count,
                size_bytes=size_bytes,
                schema=schema,
                notes=notes,
                created_at=now,
            )
        )

        # Update dataset with new version info
        session.execute(
            update(datasets)
            .where(datasets.c.id == dataset_id)
            .values(
                current_version_id=version_id,
                current_version_number=version_number,
                storage_uri=storage_uri,
                schema=schema,
                row_count=row_count,
                column_count=column_count,
                size_bytes=size_bytes,
                updated_at=now,
            )
        )

        session.commit()

        logger.info(f"Uploaded version {version_number} for dataset {dataset_id}")

        return DatasetVersion(
            id=version_id,
            dataset_id=dataset_id,
            version_number=version_number,
            sha256=sha256,
            storage_uri=storage_uri,
            storage_format="parquet",
            original_filename=file.filename,
            row_count=row_count,
            column_count=column_count,
            size_bytes=size_bytes,
            schema=schema,
            notes=notes,
            created_at=now,
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Version upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("", response_model=DatasetListResponse)
async def list_datasets(
    status: Optional[DatasetStatus] = Query(None, description="Filter by status"),
    source_type: Optional[DatasetSourceType] = Query(None, description="Filter by source type"),
    org_id: Optional[str] = Query(None, description="Filter by organization"),
    search: Optional[str] = Query(None, description="Search by name"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    session: Session = Depends(get_session),
):
    """List datasets with filtering and pagination."""
    query = select(datasets)

    # Apply filters
    if status:
        query = query.where(datasets.c.status == status.value)
    if source_type:
        query = query.where(datasets.c.source_type == source_type.value)
    if org_id:
        query = query.where(datasets.c.org_id == org_id)
    if search:
        query = query.where(datasets.c.name.ilike(f"%{search}%"))

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total = session.execute(count_query).scalar() or 0

    # Apply pagination
    query = query.order_by(datasets.c.updated_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = session.execute(query)
    rows = result.fetchall()

    items = [
        Dataset(
            id=row.id,
            name=row.name,
            description=row.description,
            status=DatasetStatus(row.status) if row.status else DatasetStatus.ACTIVE,
            source_type=DatasetSourceType(row.source_type) if row.source_type else DatasetSourceType.UPLOAD,
            source_id=row.source_id,
            schema=row.schema or {},
            row_count=row.row_count,
            column_count=row.column_count,
            size_bytes=row.size_bytes,
            storage_uri=row.storage_uri,
            storage_format=row.storage_format or "parquet",
            current_version_number=row.current_version_number or 0,
            tags=row.tags or [],
            org_id=row.org_id or "default",
            created_at=row.created_at,
            updated_at=row.updated_at,
            created_by=row.created_by,
        )
        for row in rows
    ]

    return DatasetListResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/{dataset_id}", response_model=Dataset)
async def get_dataset(
    dataset_id: UUID,
    session: Session = Depends(get_session),
):
    """Get a dataset by ID."""
    result = session.execute(
        select(datasets).where(datasets.c.id == dataset_id)
    )
    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Dataset not found")

    return Dataset(
        id=row.id,
        name=row.name,
        description=row.description,
        status=DatasetStatus(row.status) if row.status else DatasetStatus.ACTIVE,
        source_type=DatasetSourceType(row.source_type) if row.source_type else DatasetSourceType.UPLOAD,
        source_id=row.source_id,
        schema=row.schema or {},
        row_count=row.row_count,
        column_count=row.column_count,
        size_bytes=row.size_bytes,
        storage_uri=row.storage_uri,
        storage_format=row.storage_format or "parquet",
        current_version_number=row.current_version_number or 0,
        tags=row.tags or [],
        org_id=row.org_id or "default",
        created_at=row.created_at,
        updated_at=row.updated_at,
        created_by=row.created_by,
    )


@router.patch("/{dataset_id}", response_model=Dataset)
async def update_dataset(
    dataset_id: UUID,
    data: DatasetUpdate,
    session: Session = Depends(get_session),
):
    """Update dataset metadata."""
    result = session.execute(
        select(datasets).where(datasets.c.id == dataset_id)
    )
    if not result.fetchone():
        raise HTTPException(status_code=404, detail="Dataset not found")

    # Build update values
    values = {"updated_at": datetime.utcnow()}
    if data.name is not None:
        values["name"] = data.name
    if data.description is not None:
        values["description"] = data.description
    if data.tags is not None:
        values["tags"] = data.tags
    if data.status is not None:
        values["status"] = data.status.value

    session.execute(
        update(datasets).where(datasets.c.id == dataset_id).values(**values)
    )
    session.commit()

    return await get_dataset(dataset_id, session)


@router.delete("/{dataset_id}", status_code=204)
async def delete_dataset(
    dataset_id: UUID,
    delete_storage: bool = Query(True, description="Also delete from object storage"),
    session: Session = Depends(get_session),
):
    """Delete a dataset and optionally its storage."""
    result = session.execute(
        select(datasets).where(datasets.c.id == dataset_id)
    )
    if not result.fetchone():
        raise HTTPException(status_code=404, detail="Dataset not found")

    # Delete from storage if requested
    if delete_storage:
        try:
            storage = get_dataset_storage()
            storage.delete_dataset(dataset_id)
        except Exception as e:
            logger.warning(f"Failed to delete storage for {dataset_id}: {e}")

    # Delete from DB (versions cascade)
    session.execute(delete(datasets).where(datasets.c.id == dataset_id))
    session.commit()

    logger.info(f"Deleted dataset {dataset_id}")
    return None


@router.get("/{dataset_id}/versions", response_model=DatasetVersionListResponse)
async def list_versions(
    dataset_id: UUID,
    session: Session = Depends(get_session),
):
    """List all versions of a dataset."""
    # Check dataset exists
    result = session.execute(
        select(datasets).where(datasets.c.id == dataset_id)
    )
    if not result.fetchone():
        raise HTTPException(status_code=404, detail="Dataset not found")

    # Get versions
    result = session.execute(
        select(dataset_versions)
        .where(dataset_versions.c.dataset_id == dataset_id)
        .order_by(dataset_versions.c.version_number.desc())
    )
    rows = result.fetchall()

    items = [
        DatasetVersion(
            id=row.id,
            dataset_id=row.dataset_id,
            version_number=row.version_number,
            sha256=row.sha256,
            storage_uri=row.storage_uri,
            storage_format=row.storage_format,
            original_filename=row.original_filename,
            row_count=row.row_count,
            column_count=row.column_count,
            size_bytes=row.size_bytes,
            schema=row.schema or {},
            quality_profile=row.quality_profile or {},
            created_at=row.created_at,
            created_by=row.created_by,
            notes=row.notes,
        )
        for row in rows
    ]

    return DatasetVersionListResponse(items=items, total=len(items))


@router.get("/{dataset_id}/preview", response_model=DatasetPreviewResponse)
async def preview_dataset(
    dataset_id: UUID,
    version: Optional[int] = Query(None, description="Version number (default: latest)"),
    limit: int = Query(100, ge=1, le=1000, description="Number of rows"),
    session: Session = Depends(get_session),
):
    """Preview dataset data."""
    # Get dataset
    result = session.execute(
        select(datasets).where(datasets.c.id == dataset_id)
    )
    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Dataset not found")

    # Use specified version or current
    version_number = version or row.current_version_number or 1

    try:
        storage = get_dataset_storage()
        rows, columns = storage.read_sample(
            dataset_id=dataset_id,
            version=version_number,
            format="parquet",
            limit=limit,
        )

        return DatasetPreviewResponse(
            columns=columns,
            rows=rows,
            total_rows=row.row_count or len(rows),
            preview_rows=len(rows),
        )

    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Dataset file not found")
    except Exception as e:
        logger.error(f"Preview failed: {e}")
        raise HTTPException(status_code=500, detail=f"Preview failed: {str(e)}")


@router.get("/{dataset_id}/download", response_model=DatasetDownloadResponse)
async def get_download_url(
    dataset_id: UUID,
    version: Optional[int] = Query(None, description="Version number (default: latest)"),
    format: str = Query("csv", description="Download format (csv or parquet)"),
    expires_in: int = Query(3600, ge=60, le=86400, description="URL expiry in seconds"),
    session: Session = Depends(get_session),
):
    """Get a presigned download URL for the dataset."""
    if format not in ("csv", "parquet"):
        raise HTTPException(status_code=400, detail="Format must be 'csv' or 'parquet'")

    # Get dataset
    result = session.execute(
        select(datasets).where(datasets.c.id == dataset_id)
    )
    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Dataset not found")

    version_number = version or row.current_version_number or 1

    try:
        storage = get_dataset_storage()
        download_url = storage.get_download_url(
            dataset_id=dataset_id,
            version=version_number,
            format=format,
            expires_in=expires_in,
        )

        return DatasetDownloadResponse(
            download_url=download_url,
            expires_in=expires_in,
            format=format,
        )

    except Exception as e:
        logger.error(f"Download URL generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate download URL: {str(e)}")


# Legacy endpoints for backward compatibility
@router.post("", response_model=Dataset, status_code=201)
async def create_dataset(dataset: DatasetCreate, session: Session = Depends(get_session)):
    """Create a dataset record (metadata only, no file)."""
    dataset_id = uuid4()
    now = datetime.utcnow()

    session.execute(
        datasets.insert().values(
            id=dataset_id,
            name=dataset.name,
            description=dataset.description,
            org_id=dataset.org_id or "default",
            tags=dataset.tags or [],
            source_type=DatasetSourceType.UPLOAD.value,
            current_version_number=0,
            status=DatasetStatus.ACTIVE.value,
            created_at=now,
            updated_at=now,
        )
    )
    session.commit()

    return Dataset(
        id=dataset_id,
        name=dataset.name,
        description=dataset.description,
        status=DatasetStatus.ACTIVE,
        source_type=DatasetSourceType.UPLOAD,
        tags=dataset.tags or [],
        org_id=dataset.org_id or "default",
        created_at=now,
        updated_at=now,
    )


@router.post("/{dataset_id}/transforms", response_model=Transform, status_code=201)
async def create_transform(
    dataset_id: UUID,
    name: str,
    transform_type: str,
    config: dict
):
    """Create a transform (not implemented)."""
    raise HTTPException(status_code=501, detail="Transforms not yet implemented")


@router.get("/{dataset_id}/transforms", response_model=List[Transform])
async def list_transforms(dataset_id: UUID):
    """List transforms for a dataset (not implemented)."""
    raise HTTPException(status_code=501, detail="Transforms not yet implemented")


@router.post("/synthetic/generate", response_model=SyntheticDataResult, status_code=201)
async def generate_synthetic_data(request: SyntheticDataRequest):
    """Generate synthetic data (use /api/v1/synthetic/ instead)."""
    raise HTTPException(
        status_code=501,
        detail="Use /api/v1/synthetic/generate for synthetic data generation"
    )
