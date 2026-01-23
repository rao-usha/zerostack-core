"""Dataset export service for notebooks."""
import io
import logging
from datetime import datetime
from typing import List, Dict, Any, Tuple, Optional
from uuid import UUID

import pyarrow as pa
import pyarrow.parquet as pq
import pandas as pd

from services.object_store.client import ObjectStoreClient

logger = logging.getLogger(__name__)


class DatasetExporter:
    """Exports query results to object storage."""
    
    def __init__(self):
        self.object_store = ObjectStoreClient.get_instance()
    
    def export_to_parquet(
        self,
        dataset_id: UUID,
        rows: List[Dict[str, Any]],
        columns: List[Dict[str, str]]
    ) -> Tuple[str, int]:
        """
        Export rows to Parquet format in object storage.
        
        Args:
            dataset_id: Dataset UUID for path
            rows: List of row dictionaries
            columns: Column metadata [{name, type}, ...]
            
        Returns:
            (storage_uri, size_bytes)
        """
        if not rows:
            raise ValueError("No data to export")
        
        # Convert to pandas DataFrame
        df = pd.DataFrame(rows)
        
        # Convert to PyArrow Table
        table = pa.Table.from_pandas(df)
        
        # Write to Parquet in memory
        buffer = io.BytesIO()
        pq.write_table(table, buffer, compression='snappy')
        buffer.seek(0)
        parquet_bytes = buffer.getvalue()
        
        # Upload to object storage
        key = f"datasets/{dataset_id}/data.parquet"
        uri = self.object_store.put_bytes(
            key, 
            parquet_bytes, 
            content_type='application/octet-stream'
        )
        
        logger.info(f"Exported dataset {dataset_id} to {uri} ({len(parquet_bytes)} bytes)")
        return uri, len(parquet_bytes)
    
    def export_to_csv(
        self,
        dataset_id: UUID,
        rows: List[Dict[str, Any]],
        columns: List[Dict[str, str]]
    ) -> Tuple[str, int]:
        """
        Export rows to CSV format in object storage.
        
        Args:
            dataset_id: Dataset UUID for path
            rows: List of row dictionaries
            columns: Column metadata
            
        Returns:
            (storage_uri, size_bytes)
        """
        if not rows:
            raise ValueError("No data to export")
        
        # Convert to pandas DataFrame
        df = pd.DataFrame(rows)
        
        # Write to CSV in memory
        buffer = io.StringIO()
        df.to_csv(buffer, index=False)
        csv_bytes = buffer.getvalue().encode('utf-8')
        
        # Upload to object storage
        key = f"datasets/{dataset_id}/data.csv"
        uri = self.object_store.put_bytes(
            key,
            csv_bytes,
            content_type='text/csv'
        )
        
        logger.info(f"Exported dataset {dataset_id} to {uri} ({len(csv_bytes)} bytes)")
        return uri, len(csv_bytes)
    
    def get_download_url(self, storage_uri: str, expires_in: int = 3600) -> str:
        """
        Get a presigned download URL for a dataset.
        
        Args:
            storage_uri: Full s3:// URI
            expires_in: URL validity in seconds
            
        Returns:
            Presigned URL
        """
        return self.object_store.generate_presigned_url(storage_uri, expires_in)
    
    def read_dataset_sample(
        self,
        storage_uri: str,
        storage_format: str,
        limit: int = 100
    ) -> Tuple[List[Dict[str, Any]], List[str]]:
        """
        Read a sample of rows from a stored dataset.
        
        Args:
            storage_uri: Full s3:// URI
            storage_format: 'parquet' or 'csv'
            limit: Max rows to return
            
        Returns:
            (rows, columns)
        """
        data = self.object_store.get_bytes(storage_uri)
        
        if storage_format == 'parquet':
            buffer = io.BytesIO(data)
            table = pq.read_table(buffer)
            df = table.to_pandas()
        elif storage_format == 'csv':
            buffer = io.StringIO(data.decode('utf-8'))
            df = pd.read_csv(buffer)
        else:
            raise ValueError(f"Unsupported format: {storage_format}")
        
        # Limit rows
        df = df.head(limit)
        
        # Convert to JSON-safe format
        rows = df.to_dict(orient='records')
        columns = list(df.columns)
        
        # Make values JSON-safe
        for row in rows:
            for key, val in row.items():
                if pd.isna(val):
                    row[key] = None
                elif hasattr(val, 'isoformat'):
                    row[key] = val.isoformat()
        
        return rows, columns
    
    def delete_dataset(self, storage_uri: str) -> bool:
        """
        Delete a dataset from storage.
        
        Args:
            storage_uri: Full s3:// URI
            
        Returns:
            True if deleted
        """
        return self.object_store.delete(storage_uri)
