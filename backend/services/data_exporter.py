"""Data export service - exports data from PostgreSQL to MinIO for ML jobs."""
import os
import io
import logging
from typing import Optional
from datetime import datetime

import pandas as pd
import psycopg

from core.config import settings
from services.object_store import ObjectStoreClient

logger = logging.getLogger(__name__)


class DataExporter:
    """
    Export data from PostgreSQL to MinIO for ML processing.
    
    Supports exporting M5 data and other datasets to Parquet format.
    """
    
    def __init__(self):
        self.storage = ObjectStoreClient.get_instance()
    
    def _get_nexdata_connection(self):
        """Get connection to nexdata database."""
        return psycopg.connect(
            host=settings.explorer_db_host,
            port=settings.explorer_db_port,
            user=settings.explorer_db_user,
            password=settings.explorer_db_password,
            dbname=settings.explorer_db_name
        )
    
    def export_m5_data(self, job_id: str, limit: Optional[int] = None) -> dict:
        """
        Export M5 dataset to MinIO for forecasting.
        
        Args:
            job_id: Unique job identifier
            limit: Optional row limit for testing
            
        Returns:
            Dict with export details and S3 paths
        """
        logger.info(f"Exporting M5 data for job {job_id}")
        start_time = datetime.now()
        
        output_prefix = f"jobs/{job_id}/input"
        results = {'job_id': job_id, 'files': {}}
        
        try:
            conn = self._get_nexdata_connection()
            
            # Export sales data
            logger.info("Exporting m5_sales...")
            limit_clause = f"LIMIT {limit}" if limit else ""
            sales_query = f"""
                SELECT item_store_id, d, item_id, store_id, date, sales
                FROM m5_sales
                ORDER BY item_store_id, date
                {limit_clause}
            """
            sales_df = pd.read_sql(sales_query, conn)
            sales_path = self._upload_parquet(sales_df, f"{output_prefix}/sales.parquet")
            results['files']['sales'] = {'path': sales_path, 'rows': len(sales_df)}
            logger.info(f"  Exported {len(sales_df):,} rows")
            
            # Export calendar data
            logger.info("Exporting m5_calendar...")
            calendar_df = pd.read_sql("SELECT * FROM m5_calendar ORDER BY date", conn)
            calendar_path = self._upload_parquet(calendar_df, f"{output_prefix}/calendar.parquet")
            results['files']['calendar'] = {'path': calendar_path, 'rows': len(calendar_df)}
            logger.info(f"  Exported {len(calendar_df):,} rows")
            
            # Export prices data
            logger.info("Exporting m5_prices...")
            prices_df = pd.read_sql("SELECT * FROM m5_prices", conn)
            prices_path = self._upload_parquet(prices_df, f"{output_prefix}/prices.parquet")
            results['files']['prices'] = {'path': prices_path, 'rows': len(prices_df)}
            logger.info(f"  Exported {len(prices_df):,} rows")
            
            conn.close()
            
            elapsed = (datetime.now() - start_time).total_seconds()
            results['status'] = 'success'
            results['output_prefix'] = output_prefix
            results['elapsed_seconds'] = elapsed
            results['total_rows'] = sum(f['rows'] for f in results['files'].values())
            
            logger.info(f"M5 export complete: {results['total_rows']:,} total rows in {elapsed:.1f}s")
            
        except Exception as e:
            logger.error(f"M5 export failed: {e}")
            results['status'] = 'error'
            results['error'] = str(e)
        
        return results
    
    def _upload_parquet(self, df: pd.DataFrame, key: str) -> str:
        """Upload DataFrame as Parquet to MinIO."""
        buffer = io.BytesIO()
        df.to_parquet(buffer, index=False)
        buffer.seek(0)
        
        uri = self.storage.put_bytes(key, buffer.read(), content_type='application/octet-stream')
        return uri


# Singleton instance
_exporter = None

def get_data_exporter() -> DataExporter:
    """Get singleton DataExporter instance."""
    global _exporter
    if _exporter is None:
        _exporter = DataExporter()
    return _exporter
