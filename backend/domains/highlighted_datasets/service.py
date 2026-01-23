"""Highlighted Datasets service."""
import logging
from datetime import datetime
from typing import Optional, List
from uuid import UUID, uuid4

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from services.object_store import ObjectStoreClient, ObjectStorePaths
from .db_models import HighlightedDataset, HighlightedDatasetVersion
from .models import AvailabilityState

logger = logging.getLogger(__name__)


class HighlightedDatasetService:
    """Service for managing highlighted datasets."""
    
    def __init__(self, session: AsyncSession, object_store: Optional[ObjectStoreClient] = None):
        self.session = session
        self.storage = object_store or ObjectStoreClient.get_instance()
    
    # ========================================
    # Dataset CRUD
    # ========================================
    
    async def list_datasets(
        self,
        availability_state: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 100,
        offset: int = 0
    ) -> tuple[List[HighlightedDataset], int]:
        """
        List highlighted datasets with optional filters.
        
        Returns:
            Tuple of (datasets, total_count)
        """
        query = select(HighlightedDataset)
        
        if availability_state:
            query = query.where(HighlightedDataset.availability_state == availability_state)
        
        if tags:
            # Filter by any matching tag
            query = query.where(HighlightedDataset.tags.overlap(tags))
        
        # Get total count
        count_result = await self.session.execute(
            select(HighlightedDataset.id).where(query.whereclause) if query.whereclause is not None 
            else select(HighlightedDataset.id)
        )
        total = len(count_result.all())
        
        # Get paginated results
        query = query.order_by(HighlightedDataset.display_name).offset(offset).limit(limit)
        result = await self.session.execute(query)
        datasets = result.scalars().all()
        
        return datasets, total
    
    async def get_dataset(self, dataset_id: str) -> Optional[HighlightedDataset]:
        """Get a single highlighted dataset by ID."""
        result = await self.session.execute(
            select(HighlightedDataset)
            .where(HighlightedDataset.id == dataset_id)
            .options(selectinload(HighlightedDataset.versions))
        )
        return result.scalar_one_or_none()
    
    async def create_dataset(
        self,
        id: str,
        display_name: str,
        source_type: str,
        description: Optional[str] = None,
        tags: List[str] = None,
        resolver_config: dict = None,
        license_notes: Optional[str] = None
    ) -> HighlightedDataset:
        """Create a new highlighted dataset entry."""
        dataset = HighlightedDataset(
            id=id,
            display_name=display_name,
            description=description,
            tags=tags or [],
            source_type=source_type,
            availability_state=AvailabilityState.NOT_PRESENT.value,
            resolver_config=resolver_config or {},
            license_notes=license_notes
        )
        self.session.add(dataset)
        await self.session.flush()
        return dataset
    
    async def update_dataset(
        self,
        dataset_id: str,
        **kwargs
    ) -> Optional[HighlightedDataset]:
        """Update a highlighted dataset."""
        kwargs['updated_at'] = datetime.utcnow()
        
        await self.session.execute(
            update(HighlightedDataset)
            .where(HighlightedDataset.id == dataset_id)
            .values(**{k: v for k, v in kwargs.items() if v is not None})
        )
        await self.session.flush()
        return await self.get_dataset(dataset_id)
    
    async def delete_dataset(self, dataset_id: str) -> bool:
        """Delete a highlighted dataset and its versions."""
        result = await self.session.execute(
            delete(HighlightedDataset).where(HighlightedDataset.id == dataset_id)
        )
        return result.rowcount > 0
    
    # ========================================
    # Version Management
    # ========================================
    
    async def list_versions(self, dataset_id: str) -> List[HighlightedDatasetVersion]:
        """List all versions for a dataset."""
        result = await self.session.execute(
            select(HighlightedDatasetVersion)
            .where(HighlightedDatasetVersion.highlighted_dataset_id == dataset_id)
            .order_by(HighlightedDatasetVersion.created_at.desc())
        )
        return result.scalars().all()
    
    async def get_version(self, version_id: UUID) -> Optional[HighlightedDatasetVersion]:
        """Get a specific version."""
        result = await self.session.execute(
            select(HighlightedDatasetVersion)
            .where(HighlightedDatasetVersion.id == version_id)
        )
        return result.scalar_one_or_none()
    
    async def get_latest_version(self, dataset_id: str) -> Optional[HighlightedDatasetVersion]:
        """Get the latest version for a dataset."""
        result = await self.session.execute(
            select(HighlightedDatasetVersion)
            .where(HighlightedDatasetVersion.highlighted_dataset_id == dataset_id)
            .order_by(HighlightedDatasetVersion.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
    
    async def create_version(
        self,
        dataset_id: str,
        version_label: str,
        manifest_uri: str,
        storage_uri: str,
        file_count: Optional[int] = None,
        total_bytes: Optional[int] = None,
        schema_json: Optional[dict] = None,
        created_by: Optional[str] = None
    ) -> HighlightedDatasetVersion:
        """Create a new version for a dataset."""
        version = HighlightedDatasetVersion(
            id=uuid4(),
            highlighted_dataset_id=dataset_id,
            version_label=version_label,
            manifest_uri=manifest_uri,
            storage_uri=storage_uri,
            file_count=file_count,
            total_bytes=total_bytes,
            schema_json=schema_json,
            created_by=created_by
        )
        self.session.add(version)
        await self.session.flush()
        return version
    
    # ========================================
    # Resolution Logic
    # ========================================
    
    async def resolve(
        self,
        dataset_id: str,
        force_refresh: bool = False,
        credentials: Optional[dict] = None
    ) -> tuple[HighlightedDatasetVersion | None, str]:
        """
        Resolve a dataset - check availability and return version.
        
        Args:
            dataset_id: Dataset to resolve
            force_refresh: Force re-check even if AVAILABLE
            credentials: Optional credentials for protected datasets
            
        Returns:
            Tuple of (version or None, status message)
        """
        dataset = await self.get_dataset(dataset_id)
        if not dataset:
            return None, f"Dataset {dataset_id} not found"
        
        state = dataset.availability_state
        
        # Already available and not forcing refresh
        if state == AvailabilityState.AVAILABLE.value and not force_refresh:
            version = await self.get_latest_version(dataset_id)
            if version:
                # Verify manifest still exists
                if self.storage.exists(self.storage._normalize_key(version.manifest_uri)):
                    return version, "Dataset is available"
                else:
                    # Manifest missing - update state
                    await self.update_dataset(dataset_id, availability_state=AvailabilityState.NOT_PRESENT.value)
                    state = AvailabilityState.NOT_PRESENT.value
        
        # Not present - check resolver config
        if state == AvailabilityState.NOT_PRESENT.value:
            resolver_config = dataset.resolver_config
            ingest_method = resolver_config.get('ingest_method', 'manual_upload')
            
            if ingest_method == 'manual_upload':
                return None, "Dataset requires manual file upload. Use the upload endpoint."
            
            elif ingest_method == 'http_download':
                # TODO: Implement HTTP download
                return None, "HTTP download not yet implemented. Use manual upload."
            
            elif ingest_method == 'kaggle':
                if not credentials or 'kaggle_token' not in credentials:
                    await self.update_dataset(
                        dataset_id, 
                        availability_state=AvailabilityState.REQUIRES_CREDENTIALS.value
                    )
                    return None, "Kaggle credentials required"
                # TODO: Implement Kaggle download
                return None, "Kaggle download not yet implemented. Use manual upload."
        
        # Requires credentials
        if state == AvailabilityState.REQUIRES_CREDENTIALS.value:
            return None, "Dataset requires credentials. Provide them in the request."
        
        # Error state
        if state == AvailabilityState.ERROR.value:
            return None, f"Dataset is in error state. Check logs or retry."
        
        # Ingesting
        if state == AvailabilityState.INGESTING.value:
            return None, "Dataset ingestion is in progress."
        
        return None, f"Unknown state: {state}"
    
    async def finalize_upload(
        self,
        dataset_id: str,
        version_label: str,
        files: List[dict],
        created_by: Optional[str] = None
    ) -> HighlightedDatasetVersion:
        """
        Finalize an upload by creating manifest and version.
        
        Args:
            dataset_id: Dataset being uploaded
            version_label: Version label (e.g., "v1")
            files: List of uploaded file info dicts
            created_by: User who uploaded
            
        Returns:
            Created version
        """
        # Calculate totals
        total_bytes = sum(f.get('bytes', 0) for f in files)
        file_count = len(files)
        
        # Create manifest
        manifest = ObjectStorePaths.create_dataset_manifest(
            dataset_id=dataset_id,
            version=version_label,
            files=files
        )
        
        # Write manifest to storage
        manifest_key = ObjectStorePaths.dataset_manifest(dataset_id, version_label)
        manifest_uri = self.storage.put_json(manifest_key, manifest)
        storage_uri = self.storage.get_uri(ObjectStorePaths.dataset_root(dataset_id, version_label))
        
        # Create version record
        version = await self.create_version(
            dataset_id=dataset_id,
            version_label=version_label,
            manifest_uri=manifest_uri,
            storage_uri=storage_uri,
            file_count=file_count,
            total_bytes=total_bytes,
            created_by=created_by
        )
        
        # Update dataset state to AVAILABLE
        await self.update_dataset(
            dataset_id,
            availability_state=AvailabilityState.AVAILABLE.value
        )
        
        logger.info(f"Finalized upload for {dataset_id} version {version_label}: {file_count} files, {total_bytes} bytes")
        
        return version
