"""Data Export Service for exporting query results to S3.

Provides functionality to:
- Export SQL query results to S3 as parquet/csv
- Export entire tables to S3
- Track export jobs with status and metadata
"""

import io
import logging
import time
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID, uuid4

import pandas as pd
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func

from .connection import get_explorer_connection
from .service import QueryValidator

logger = logging.getLogger(__name__)


class DataExportService:
    """Service for exporting data to S3."""

    def __init__(self, session: AsyncSession):
        """Initialize export service.

        Args:
            session: Async database session for tracking exports
        """
        self.session = session

    async def export_query(
        self,
        sql: str,
        name: str,
        output_path: str,
        format: str = "parquet",
        connection_id: str = "default",
        description: Optional[str] = None,
        created_by: Optional[str] = None,
        conversation_id: Optional[UUID] = None,
        compression: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Export SQL query results to S3.

        Args:
            sql: SELECT query to execute
            name: Name for the export
            output_path: S3 path (e.g., "exports/my_export.parquet")
            format: Output format ("parquet" or "csv")
            connection_id: Database connection to use
            description: Optional description
            created_by: User who initiated the export
            conversation_id: Optional link to chat conversation
            compression: Optional compression (gzip, snappy, etc.)

        Returns:
            Dict with export results including S3 URI, row count, etc.
        """
        from .export_models import data_exports

        # Validate query is safe (SELECT only)
        is_safe, error_msg = QueryValidator.is_safe_query(sql)
        if not is_safe:
            raise ValueError(f"Query validation failed: {error_msg}")

        # Create export record
        export_id = uuid4()
        await self.session.execute(
            data_exports.insert().values(
                id=export_id,
                name=name,
                description=description,
                source_type="query",
                source_query=sql,
                connection_id=connection_id,
                destination_format=format,
                destination_options={"compression": compression} if compression else {},
                status="running",
                created_by=created_by,
                conversation_id=conversation_id,
                started_at=datetime.utcnow(),
            )
        )
        await self.session.commit()

        try:
            start_time = time.time()

            # Execute query and get results
            df, columns = self._execute_query(sql, connection_id)

            # Upload to S3
            s3_uri, file_size = self._upload_dataframe(
                df=df,
                path=output_path,
                format=format,
                compression=compression,
            )

            duration = time.time() - start_time

            # Update export record with success
            await self.session.execute(
                update(data_exports)
                .where(data_exports.c.id == export_id)
                .values(
                    status="completed",
                    progress=100,
                    destination_uri=s3_uri,
                    row_count=len(df),
                    column_count=len(df.columns),
                    file_size_bytes=file_size,
                    columns=[{"name": c, "dtype": str(df[c].dtype)} for c in df.columns],
                    completed_at=datetime.utcnow(),
                    duration_seconds=Decimal(str(round(duration, 2))),
                )
            )
            await self.session.commit()

            logger.info(f"Export {export_id} completed: {len(df)} rows to {s3_uri}")

            return {
                "export_id": str(export_id),
                "status": "completed",
                "destination_uri": s3_uri,
                "row_count": len(df),
                "column_count": len(df.columns),
                "file_size_bytes": file_size,
                "format": format,
                "duration_seconds": round(duration, 2),
            }

        except Exception as e:
            # Update export record with failure
            await self.session.execute(
                update(data_exports)
                .where(data_exports.c.id == export_id)
                .values(
                    status="failed",
                    error_message=str(e),
                    completed_at=datetime.utcnow(),
                )
            )
            await self.session.commit()

            logger.error(f"Export {export_id} failed: {e}")
            raise

    async def export_table(
        self,
        schema: str,
        table: str,
        name: str,
        output_path: str,
        format: str = "parquet",
        connection_id: str = "default",
        description: Optional[str] = None,
        created_by: Optional[str] = None,
        conversation_id: Optional[UUID] = None,
        compression: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Export an entire table to S3.

        Args:
            schema: Schema name
            table: Table name
            name: Name for the export
            output_path: S3 path
            format: Output format ("parquet" or "csv")
            connection_id: Database connection
            description: Optional description
            created_by: User who initiated
            conversation_id: Link to chat conversation
            compression: Compression type
            limit: Optional row limit

        Returns:
            Dict with export results
        """
        # Build query with proper identifier quoting
        sql = f'SELECT * FROM "{schema}"."{table}"'
        if limit:
            sql += f" LIMIT {int(limit)}"

        return await self.export_query(
            sql=sql,
            name=name,
            output_path=output_path,
            format=format,
            connection_id=connection_id,
            description=description or f"Export of {schema}.{table}",
            created_by=created_by,
            conversation_id=conversation_id,
            compression=compression,
        )

    def _execute_query(
        self,
        sql: str,
        connection_id: str,
    ) -> Tuple[pd.DataFrame, List[str]]:
        """Execute query and return DataFrame.

        Args:
            sql: SQL query
            connection_id: Database connection

        Returns:
            Tuple of (DataFrame, column_names)
        """
        with get_explorer_connection(connection_id) as conn:
            with conn.cursor() as cur:
                # Set reasonable timeout for large exports (5 minutes)
                cur.execute("SET statement_timeout = '300s'")
                cur.execute(sql)

                columns = [desc[0] for desc in cur.description] if cur.description else []
                rows = cur.fetchall()

        df = pd.DataFrame(rows, columns=columns)
        return df, columns

    def _upload_dataframe(
        self,
        df: pd.DataFrame,
        path: str,
        format: str,
        compression: Optional[str] = None,
    ) -> Tuple[str, int]:
        """Upload DataFrame to S3.

        Args:
            df: DataFrame to upload
            path: S3 path
            format: File format
            compression: Compression type

        Returns:
            Tuple of (s3_uri, file_size_bytes)
        """
        from services.object_store.client import get_object_store

        store = get_object_store()
        buffer = io.BytesIO()

        if format == "parquet":
            # Default to snappy compression for parquet
            parquet_compression = compression or "snappy"
            df.to_parquet(buffer, index=False, compression=parquet_compression)
            content_type = "application/octet-stream"
        elif format == "csv":
            if compression == "gzip":
                df.to_csv(buffer, index=False, compression="gzip")
                content_type = "application/gzip"
            else:
                df.to_csv(buffer, index=False)
                content_type = "text/csv"
        else:
            raise ValueError(f"Unsupported format: {format}")

        buffer.seek(0)
        file_size = len(buffer.getvalue())

        # Upload to S3
        s3_uri = store.upload_file(path, buffer, content_type)

        return s3_uri, file_size

    async def get_export(self, export_id: UUID) -> Optional[Dict[str, Any]]:
        """Get export by ID.

        Args:
            export_id: Export ID

        Returns:
            Export dict or None
        """
        from .export_models import data_exports

        result = await self.session.execute(
            select(data_exports).where(data_exports.c.id == export_id)
        )
        row = result.fetchone()

        if not row:
            return None

        return {
            "id": str(row.id),
            "name": row.name,
            "description": row.description,
            "source_type": row.source_type,
            "source_query": row.source_query,
            "source_schema": row.source_schema,
            "source_table": row.source_table,
            "connection_id": row.connection_id,
            "destination_uri": row.destination_uri,
            "destination_format": row.destination_format,
            "status": row.status,
            "progress": row.progress,
            "row_count": row.row_count,
            "column_count": row.column_count,
            "file_size_bytes": row.file_size_bytes,
            "columns": row.columns,
            "started_at": row.started_at.isoformat() if row.started_at else None,
            "completed_at": row.completed_at.isoformat() if row.completed_at else None,
            "duration_seconds": float(row.duration_seconds) if row.duration_seconds else None,
            "error_message": row.error_message,
            "created_by": row.created_by,
            "created_at": row.created_at.isoformat() if row.created_at else None,
        }

    async def list_exports(
        self,
        limit: int = 50,
        offset: int = 0,
        status: Optional[str] = None,
        created_by: Optional[str] = None,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """List exports with filtering.

        Args:
            limit: Max results
            offset: Pagination offset
            status: Filter by status
            created_by: Filter by creator

        Returns:
            Tuple of (exports list, total count)
        """
        from .export_models import data_exports

        # Build query
        query = select(data_exports)
        count_query = select(func.count(data_exports.c.id))

        if status:
            query = query.where(data_exports.c.status == status)
            count_query = count_query.where(data_exports.c.status == status)

        if created_by:
            query = query.where(data_exports.c.created_by == created_by)
            count_query = count_query.where(data_exports.c.created_by == created_by)

        query = query.order_by(data_exports.c.created_at.desc()).offset(offset).limit(limit)

        # Execute
        result = await self.session.execute(query)
        rows = result.fetchall()

        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0

        exports = [
            {
                "id": str(row.id),
                "name": row.name,
                "source_type": row.source_type,
                "destination_uri": row.destination_uri,
                "destination_format": row.destination_format,
                "status": row.status,
                "row_count": row.row_count,
                "file_size_bytes": row.file_size_bytes,
                "created_at": row.created_at.isoformat() if row.created_at else None,
                "created_by": row.created_by,
            }
            for row in rows
        ]

        return exports, total

    async def delete_export(self, export_id: UUID, delete_file: bool = False) -> bool:
        """Delete an export record.

        Args:
            export_id: Export ID
            delete_file: Also delete the S3 file

        Returns:
            True if deleted
        """
        from .export_models import data_exports
        from services.object_store.client import get_object_store

        # Get export first
        export = await self.get_export(export_id)
        if not export:
            return False

        # Delete S3 file if requested
        if delete_file and export.get("destination_uri"):
            try:
                store = get_object_store()
                store.delete(export["destination_uri"])
                logger.info(f"Deleted S3 file: {export['destination_uri']}")
            except Exception as e:
                logger.warning(f"Failed to delete S3 file: {e}")

        # Delete record
        await self.session.execute(
            data_exports.delete().where(data_exports.c.id == export_id)
        )
        await self.session.commit()

        logger.info(f"Deleted export {export_id}")
        return True

    async def generate_download_url(
        self,
        export_id: UUID,
        expires_in: int = 3600,
    ) -> Optional[str]:
        """Generate presigned download URL for an export.

        Args:
            export_id: Export ID
            expires_in: URL expiry in seconds

        Returns:
            Presigned URL or None
        """
        from services.object_store.client import get_object_store

        export = await self.get_export(export_id)
        if not export or not export.get("destination_uri"):
            return None

        store = get_object_store()
        return store.generate_presigned_url(export["destination_uri"], expires_in)
