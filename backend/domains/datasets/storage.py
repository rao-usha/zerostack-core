"""Dataset storage service for handling file uploads to object storage."""
import hashlib
import io
import logging
from typing import Optional, Dict, Any, Tuple, BinaryIO
from uuid import UUID

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from services.object_store.client import ObjectStoreClient, get_object_store

logger = logging.getLogger(__name__)


class DatasetStorage:
    """Handle dataset file storage in S3/MinIO.

    Storage Layout:
        datasets/{dataset_id}/
        ├── v1/
        │   ├── data.parquet
        │   ├── data.csv (optional)
        │   └── manifest.json
        ├── v2/
        │   └── ...
        └── latest -> v{n}
    """

    def __init__(self, client: Optional[ObjectStoreClient] = None):
        """Initialize storage service."""
        self._client = client

    @property
    def client(self) -> ObjectStoreClient:
        """Get object store client (lazy initialization)."""
        if self._client is None:
            self._client = get_object_store()
        return self._client

    def upload_file(
        self,
        dataset_id: UUID,
        version_number: int,
        file_obj: BinaryIO,
        original_filename: str,
        target_format: str = "parquet",
    ) -> Tuple[str, str, int, int, int, Dict[str, Any]]:
        """Upload a file and convert to target format.

        Args:
            dataset_id: Dataset UUID
            version_number: Version number for this upload
            file_obj: File-like object with the data
            original_filename: Original filename for format detection
            target_format: Target storage format (parquet, csv)

        Returns:
            Tuple of (storage_uri, sha256, size_bytes, row_count, column_count, schema)
        """
        dataset_id_str = str(dataset_id)

        # Read the file into memory and compute hash
        file_content = file_obj.read()
        sha256 = hashlib.sha256(file_content).hexdigest()

        # Detect source format from filename
        source_format = self._detect_format(original_filename)

        # Parse into DataFrame
        df = self._read_dataframe(file_content, source_format, original_filename)

        # Infer schema
        schema = self._infer_schema(df)

        # Save in target format
        storage_uri, size_bytes = self._save_dataframe(
            df, dataset_id_str, version_number, target_format
        )

        # Also save CSV copy for easy downloads
        if target_format == "parquet":
            self._save_csv_copy(df, dataset_id_str, version_number)

        # Save manifest
        self._save_manifest(
            dataset_id_str,
            version_number,
            original_filename,
            sha256,
            len(df),
            len(df.columns),
            size_bytes,
            schema,
        )

        return storage_uri, sha256, size_bytes, len(df), len(df.columns), schema

    def _detect_format(self, filename: str) -> str:
        """Detect file format from filename."""
        lower = filename.lower()
        if lower.endswith('.csv'):
            return 'csv'
        elif lower.endswith('.parquet') or lower.endswith('.pq'):
            return 'parquet'
        elif lower.endswith('.json') or lower.endswith('.jsonl'):
            return 'json'
        elif lower.endswith('.xlsx') or lower.endswith('.xls'):
            return 'excel'
        else:
            raise ValueError(f"Unsupported file format: {filename}")

    def _read_dataframe(self, content: bytes, format: str, filename: str) -> pd.DataFrame:
        """Read file content into a DataFrame."""
        buffer = io.BytesIO(content)

        if format == 'csv':
            return pd.read_csv(buffer)
        elif format == 'parquet':
            return pd.read_parquet(buffer)
        elif format == 'json':
            # Try JSON lines first, then regular JSON
            try:
                buffer.seek(0)
                return pd.read_json(buffer, lines=True)
            except ValueError:
                buffer.seek(0)
                return pd.read_json(buffer)
        elif format == 'excel':
            return pd.read_excel(buffer)
        else:
            raise ValueError(f"Cannot read format: {format}")

    def _infer_schema(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Infer schema from DataFrame."""
        columns = []
        for col in df.columns:
            dtype = str(df[col].dtype)
            col_info = {
                "name": col,
                "dtype": dtype,
                "nullable": df[col].isna().any(),
            }

            # Add stats for profiling
            if pd.api.types.is_numeric_dtype(df[col]):
                col_info["stats"] = {
                    "min": float(df[col].min()) if not df[col].isna().all() else None,
                    "max": float(df[col].max()) if not df[col].isna().all() else None,
                    "mean": float(df[col].mean()) if not df[col].isna().all() else None,
                    "null_count": int(df[col].isna().sum()),
                }
            else:
                col_info["stats"] = {
                    "unique_count": int(df[col].nunique()),
                    "null_count": int(df[col].isna().sum()),
                    "sample_values": df[col].dropna().head(5).tolist(),
                }

            columns.append(col_info)

        return {"columns": columns}

    def _save_dataframe(
        self, df: pd.DataFrame, dataset_id: str, version: int, format: str
    ) -> Tuple[str, int]:
        """Save DataFrame to object storage."""
        key = f"datasets/{dataset_id}/v{version}/data.{format}"

        if format == "parquet":
            buffer = io.BytesIO()
            df.to_parquet(buffer, index=False, compression='snappy')
            size = buffer.tell()
            buffer.seek(0)
            storage_uri = self.client.put_bytes(
                key, buffer.read(), content_type='application/octet-stream'
            )
        elif format == "csv":
            buffer = io.StringIO()
            df.to_csv(buffer, index=False)
            csv_bytes = buffer.getvalue().encode('utf-8')
            size = len(csv_bytes)
            storage_uri = self.client.put_bytes(key, csv_bytes, content_type='text/csv')
        else:
            raise ValueError(f"Unsupported save format: {format}")

        logger.info(f"Saved dataset to {storage_uri} ({size} bytes)")
        return storage_uri, size

    def _save_csv_copy(self, df: pd.DataFrame, dataset_id: str, version: int) -> str:
        """Save a CSV copy for easy downloads."""
        key = f"datasets/{dataset_id}/v{version}/data.csv"
        buffer = io.StringIO()
        df.to_csv(buffer, index=False)
        csv_bytes = buffer.getvalue().encode('utf-8')
        return self.client.put_bytes(key, csv_bytes, content_type='text/csv')

    def _save_manifest(
        self,
        dataset_id: str,
        version: int,
        original_filename: str,
        sha256: str,
        row_count: int,
        column_count: int,
        size_bytes: int,
        schema: Dict[str, Any],
    ) -> str:
        """Save version manifest."""
        from datetime import datetime

        key = f"datasets/{dataset_id}/v{version}/manifest.json"
        manifest = {
            "dataset_id": dataset_id,
            "version": version,
            "original_filename": original_filename,
            "sha256": sha256,
            "row_count": row_count,
            "column_count": column_count,
            "size_bytes": size_bytes,
            "schema": schema,
            "created_at": datetime.utcnow().isoformat(),
        }
        return self.client.put_json(key, manifest)

    def get_download_url(
        self, dataset_id: UUID, version: int, format: str = "csv", expires_in: int = 3600
    ) -> str:
        """Get presigned download URL."""
        key = f"datasets/{str(dataset_id)}/v{version}/data.{format}"
        return self.client.generate_presigned_url(key, expires_in=expires_in)

    def read_sample(
        self, dataset_id: UUID, version: int, format: str = "parquet", limit: int = 100
    ) -> Tuple[list, list]:
        """Read a sample of rows from stored dataset.

        Returns:
            (rows, columns) where rows is list of dicts
        """
        key = f"datasets/{str(dataset_id)}/v{version}/data.{format}"
        data = self.client.get_bytes(key)

        if format == "parquet":
            df = pd.read_parquet(io.BytesIO(data))
        elif format == "csv":
            df = pd.read_csv(io.BytesIO(data))
        else:
            raise ValueError(f"Unsupported format: {format}")

        df = df.head(limit)

        # Make JSON-safe
        rows = df.to_dict(orient='records')
        for row in rows:
            for k, v in row.items():
                if pd.isna(v):
                    row[k] = None
                elif hasattr(v, 'isoformat'):
                    row[k] = v.isoformat()

        return rows, list(df.columns)

    def delete_version(self, dataset_id: UUID, version: int) -> bool:
        """Delete a specific version."""
        prefix = f"datasets/{str(dataset_id)}/v{version}/"
        objects = self.client.list_objects(prefix)
        deleted = 0
        for obj in objects:
            if self.client.delete(obj['Key']):
                deleted += 1
        logger.info(f"Deleted {deleted} files for dataset {dataset_id} v{version}")
        return deleted > 0

    def delete_dataset(self, dataset_id: UUID) -> bool:
        """Delete all versions of a dataset."""
        prefix = f"datasets/{str(dataset_id)}/"
        objects = self.client.list_objects(prefix)
        deleted = 0
        for obj in objects:
            if self.client.delete(obj['Key']):
                deleted += 1
        logger.info(f"Deleted {deleted} files for dataset {dataset_id}")
        return deleted > 0

    def find_by_hash(self, sha256: str) -> Optional[Dict[str, Any]]:
        """Find existing dataset version by content hash.

        This allows detecting duplicate uploads.
        Returns manifest if found, None otherwise.
        """
        # This would need a DB query in practice
        # For now, return None (no deduplication)
        return None


def get_dataset_storage() -> DatasetStorage:
    """Get dataset storage instance."""
    return DatasetStorage()
