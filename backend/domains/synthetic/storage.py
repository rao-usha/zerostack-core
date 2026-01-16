"""Persistent storage service for synthetic datasets."""
import io
import logging
from typing import Optional, Dict, Any, Tuple
from uuid import UUID

import pandas as pd

from services.object_store.client import ObjectStoreClient, get_object_store
from services.object_store.paths import ObjectStorePaths

logger = logging.getLogger(__name__)


class SyntheticDataStorage:
    """Handle persistent storage of synthetic datasets in S3/MinIO.
    
    Layout:
        synthetic/{dataset_id}/
        ├── data.parquet           # Main data file
        ├── data.csv               # Optional CSV copy
        ├── manifest.json          # Dataset metadata
        ├── quality_report.json    # Quality metrics
        └── source_sample.parquet  # Source data sample for comparisons
    """
    
    def __init__(self, client: Optional[ObjectStoreClient] = None):
        """Initialize storage service.
        
        Args:
            client: Optional ObjectStoreClient instance (uses singleton if not provided)
        """
        self._client = client
    
    @property
    def client(self) -> ObjectStoreClient:
        """Get object store client (lazy initialization)."""
        if self._client is None:
            self._client = get_object_store()
        return self._client
    
    def save_dataset(
        self,
        dataset_id: UUID,
        df: pd.DataFrame,
        job_id: UUID,
        synthesizer_type: str,
        columns_info: list[dict],
        format: str = "parquet",
        save_csv: bool = True,
        quality_score: Optional[float] = None,
    ) -> Tuple[str, int]:
        """Save synthetic dataset to object storage.
        
        Args:
            dataset_id: Unique dataset identifier
            df: Synthetic DataFrame to save
            job_id: Generation job ID
            synthesizer_type: Type of synthesizer used
            columns_info: Column metadata list
            format: Primary format ('parquet' or 'csv')
            save_csv: Also save a CSV copy for easy download
            quality_score: Optional quality score
            
        Returns:
            Tuple of (storage_uri, file_size_bytes)
        """
        dataset_id_str = str(dataset_id)
        
        # Save main data file (parquet)
        parquet_key = ObjectStorePaths.synthetic_data(dataset_id_str, "parquet")
        parquet_buffer = io.BytesIO()
        df.to_parquet(parquet_buffer, index=False, compression='snappy')
        parquet_size = parquet_buffer.tell()
        parquet_buffer.seek(0)
        
        storage_uri = self.client.put_bytes(
            parquet_key,
            parquet_buffer.read(),
            content_type='application/octet-stream'
        )
        logger.info(f"Saved parquet to {storage_uri} ({parquet_size} bytes)")
        
        # Optionally save CSV copy
        if save_csv:
            csv_key = ObjectStorePaths.synthetic_data(dataset_id_str, "csv")
            csv_buffer = io.StringIO()
            df.to_csv(csv_buffer, index=False)
            csv_content = csv_buffer.getvalue()
            
            self.client.put_bytes(
                csv_key,
                csv_content.encode('utf-8'),
                content_type='text/csv'
            )
            logger.debug(f"Saved CSV copy to {csv_key}")
        
        # Save manifest
        manifest = ObjectStorePaths.create_synthetic_manifest(
            dataset_id=dataset_id_str,
            job_id=str(job_id),
            num_rows=len(df),
            num_columns=len(df.columns),
            columns=columns_info,
            synthesizer_type=synthesizer_type,
            file_size_bytes=parquet_size,
            quality_score=quality_score,
        )
        manifest_key = ObjectStorePaths.synthetic_manifest(dataset_id_str)
        self.client.put_json(manifest_key, manifest)
        
        return storage_uri, parquet_size
    
    def save_source_sample(
        self,
        dataset_id: UUID,
        source_df: pd.DataFrame,
        max_rows: int = 10000,
    ) -> str:
        """Save a sample of source data for quality comparisons.
        
        Args:
            dataset_id: Synthetic dataset ID
            source_df: Source DataFrame
            max_rows: Maximum rows to save
            
        Returns:
            Storage URI
        """
        dataset_id_str = str(dataset_id)
        
        # Sample if too large
        if len(source_df) > max_rows:
            sample_df = source_df.sample(max_rows, random_state=42)
        else:
            sample_df = source_df
        
        # Save as parquet
        key = ObjectStorePaths.synthetic_source_sample(dataset_id_str)
        buffer = io.BytesIO()
        sample_df.to_parquet(buffer, index=False, compression='snappy')
        buffer.seek(0)
        
        uri = self.client.put_bytes(
            key,
            buffer.read(),
            content_type='application/octet-stream'
        )
        logger.debug(f"Saved source sample to {uri}")
        return uri
    
    def save_quality_report(
        self,
        dataset_id: UUID,
        report: Dict[str, Any],
    ) -> str:
        """Save quality report JSON.
        
        Args:
            dataset_id: Synthetic dataset ID
            report: Quality report dict
            
        Returns:
            Storage URI
        """
        dataset_id_str = str(dataset_id)
        key = ObjectStorePaths.synthetic_quality_report(dataset_id_str)
        return self.client.put_json(key, report)
    
    def load_dataset(
        self,
        dataset_id: UUID,
        format: str = "parquet",
    ) -> pd.DataFrame:
        """Load synthetic dataset from storage.
        
        Args:
            dataset_id: Dataset ID
            format: Format to load ('parquet' or 'csv')
            
        Returns:
            DataFrame
            
        Raises:
            FileNotFoundError: If dataset not found
        """
        dataset_id_str = str(dataset_id)
        key = ObjectStorePaths.synthetic_data(dataset_id_str, format)
        
        if not self.client.exists(key):
            raise FileNotFoundError(f"Synthetic dataset not found: {dataset_id}")
        
        data = self.client.get_bytes(key)
        
        if format == "parquet":
            return pd.read_parquet(io.BytesIO(data))
        else:
            return pd.read_csv(io.BytesIO(data))
    
    def load_source_sample(self, dataset_id: UUID) -> Optional[pd.DataFrame]:
        """Load source sample for quality comparisons.
        
        Args:
            dataset_id: Synthetic dataset ID
            
        Returns:
            DataFrame or None if not found
        """
        dataset_id_str = str(dataset_id)
        key = ObjectStorePaths.synthetic_source_sample(dataset_id_str)
        
        if not self.client.exists(key):
            return None
        
        data = self.client.get_bytes(key)
        return pd.read_parquet(io.BytesIO(data))
    
    def load_manifest(self, dataset_id: UUID) -> Optional[Dict[str, Any]]:
        """Load dataset manifest.
        
        Args:
            dataset_id: Dataset ID
            
        Returns:
            Manifest dict or None
        """
        dataset_id_str = str(dataset_id)
        key = ObjectStorePaths.synthetic_manifest(dataset_id_str)
        
        if not self.client.exists(key):
            return None
        
        return self.client.get_json(key)
    
    def load_quality_report(self, dataset_id: UUID) -> Optional[Dict[str, Any]]:
        """Load quality report.
        
        Args:
            dataset_id: Dataset ID
            
        Returns:
            Quality report dict or None
        """
        dataset_id_str = str(dataset_id)
        key = ObjectStorePaths.synthetic_quality_report(dataset_id_str)
        
        if not self.client.exists(key):
            return None
        
        return self.client.get_json(key)
    
    def exists(self, dataset_id: UUID) -> bool:
        """Check if dataset exists in storage.
        
        Args:
            dataset_id: Dataset ID
            
        Returns:
            True if exists
        """
        dataset_id_str = str(dataset_id)
        key = ObjectStorePaths.synthetic_data(dataset_id_str, "parquet")
        return self.client.exists(key)
    
    def get_download_url(
        self,
        dataset_id: UUID,
        format: str = "csv",
        expires_in: int = 3600,
    ) -> str:
        """Get presigned download URL.
        
        Args:
            dataset_id: Dataset ID
            format: Format to download
            expires_in: URL validity in seconds
            
        Returns:
            Presigned URL
        """
        dataset_id_str = str(dataset_id)
        key = ObjectStorePaths.synthetic_data(dataset_id_str, format)
        return self.client.generate_presigned_url(key, expires_in=expires_in)
    
    def delete_dataset(self, dataset_id: UUID) -> bool:
        """Delete all files for a synthetic dataset.
        
        Args:
            dataset_id: Dataset ID
            
        Returns:
            True if deleted
        """
        dataset_id_str = str(dataset_id)
        prefix = ObjectStorePaths.synthetic_root(dataset_id_str)
        
        # List and delete all objects with this prefix
        objects = self.client.list_objects(prefix)
        deleted = 0
        
        for obj in objects:
            if self.client.delete(obj['Key']):
                deleted += 1
        
        logger.info(f"Deleted {deleted} files for synthetic dataset {dataset_id}")
        return deleted > 0
    
    def get_storage_info(self, dataset_id: UUID) -> Dict[str, Any]:
        """Get storage information for a dataset.
        
        Args:
            dataset_id: Dataset ID
            
        Returns:
            Dict with storage details
        """
        dataset_id_str = str(dataset_id)
        prefix = ObjectStorePaths.synthetic_root(dataset_id_str)
        
        objects = self.client.list_objects(prefix)
        
        files = []
        total_size = 0
        
        for obj in objects:
            files.append({
                "key": obj['Key'],
                "size": obj.get('Size', 0),
                "last_modified": obj.get('LastModified'),
            })
            total_size += obj.get('Size', 0)
        
        return {
            "dataset_id": dataset_id_str,
            "files": files,
            "total_files": len(files),
            "total_size_bytes": total_size,
            "parquet_exists": self.client.exists(
                ObjectStorePaths.synthetic_data(dataset_id_str, "parquet")
            ),
            "csv_exists": self.client.exists(
                ObjectStorePaths.synthetic_data(dataset_id_str, "csv")
            ),
        }


# Convenience function
def get_synthetic_storage() -> SyntheticDataStorage:
    """Get synthetic data storage instance."""
    return SyntheticDataStorage()
