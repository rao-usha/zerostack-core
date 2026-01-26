"""Materialized View Service for creating and managing materialized views.

Provides functionality to:
- Create materialized views from SQL queries
- Refresh materialized views (with or without CONCURRENTLY)
- Drop materialized views
- Track view metadata and refresh history
"""

import logging
import re
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID, uuid4

import psycopg
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func

from .db_configs import get_database_config_by_id
from .service import QueryValidator

logger = logging.getLogger(__name__)


# Reserved names that cannot be used for materialized views
RESERVED_NAMES = {
    'pg_', 'sql_', 'information_schema', 'pg_catalog',
    'public', 'temp', 'temporary', 'system', 'admin',
}

# Schema whitelist - only allow creating views in these schemas
ALLOWED_SCHEMAS = {'public', 'analytics', 'reports', 'views'}


class MaterializedViewService:
    """Service for managing materialized views."""

    def __init__(self, session: AsyncSession):
        """Initialize materialized view service.

        Args:
            session: Async database session for tracking views
        """
        self.session = session

    @staticmethod
    def _get_write_connection(connection_id: str = "default"):
        """Get a database connection with write permissions.

        Args:
            connection_id: Database connection ID

        Returns:
            psycopg.Connection: Database connection with write access
        """
        db_config = get_database_config_by_id(connection_id)
        conn_string = (
            f"host={db_config.host} "
            f"port={db_config.port} "
            f"user={db_config.user} "
            f"password={db_config.password} "
            f"dbname={db_config.database}"
        )
        return psycopg.connect(conn_string)

    @staticmethod
    def validate_view_name(name: str) -> Tuple[bool, Optional[str]]:
        """Validate materialized view name.

        Args:
            name: Proposed view name

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not name:
            return False, "View name cannot be empty"

        # Check length
        if len(name) > 63:
            return False, "View name cannot exceed 63 characters"

        # Check format (alphanumeric and underscores only)
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', name):
            return False, "View name must start with a letter and contain only letters, numbers, and underscores"

        # Check reserved names
        name_lower = name.lower()
        for reserved in RESERVED_NAMES:
            if name_lower.startswith(reserved) or name_lower == reserved:
                return False, f"View name cannot start with or be '{reserved}'"

        return True, None

    @staticmethod
    def validate_schema(schema: str) -> Tuple[bool, Optional[str]]:
        """Validate schema name is allowed.

        Args:
            schema: Schema name

        Returns:
            Tuple of (is_valid, error_message)
        """
        if schema.lower() not in ALLOWED_SCHEMAS:
            return False, f"Schema '{schema}' is not allowed. Allowed schemas: {', '.join(sorted(ALLOWED_SCHEMAS))}"
        return True, None

    async def create_materialized_view(
        self,
        name: str,
        source_query: str,
        schema_name: str = "public",
        description: Optional[str] = None,
        connection_id: str = "default",
        with_data: bool = True,
        created_by: Optional[str] = None,
        conversation_id: Optional[UUID] = None,
    ) -> Dict[str, Any]:
        """Create a new materialized view.

        Args:
            name: Name for the materialized view
            source_query: SELECT query defining the view
            schema_name: Schema to create view in
            description: Optional description
            connection_id: Database connection to use
            with_data: Whether to populate view immediately
            created_by: User who created the view
            conversation_id: Optional link to chat conversation

        Returns:
            Dict with view creation results
        """
        from .materialized_view_models import managed_materialized_views

        # Validate view name
        is_valid, error = self.validate_view_name(name)
        if not is_valid:
            raise ValueError(error)

        # Validate schema
        is_valid, error = self.validate_schema(schema_name)
        if not is_valid:
            raise ValueError(error)

        # Validate query is safe (SELECT only)
        is_safe, error_msg = QueryValidator.is_safe_query(source_query)
        if not is_safe:
            raise ValueError(f"Query validation failed: {error_msg}")

        # Check if view already exists in tracking table
        existing = await self.session.execute(
            select(managed_materialized_views).where(
                managed_materialized_views.c.schema_name == schema_name,
                managed_materialized_views.c.name == name,
            )
        )
        if existing.fetchone():
            raise ValueError(f"Materialized view '{schema_name}.{name}' already exists in tracking")

        # Create tracking record
        view_id = uuid4()
        await self.session.execute(
            managed_materialized_views.insert().values(
                id=view_id,
                name=name,
                schema_name=schema_name,
                description=description,
                source_query=source_query,
                connection_id=connection_id,
                with_data=with_data,
                status="creating",
                created_by=created_by,
                conversation_id=conversation_id,
            )
        )
        await self.session.commit()

        try:
            start_time = time.time()

            # Build CREATE MATERIALIZED VIEW statement
            full_name = f'"{schema_name}"."{name}"'
            create_sql = f"CREATE MATERIALIZED VIEW {full_name} AS {source_query}"
            if not with_data:
                create_sql += " WITH NO DATA"

            # Execute DDL
            with self._get_write_connection(connection_id) as conn:
                with conn.cursor() as cur:
                    cur.execute(create_sql)
                conn.commit()

                # Get row count and size
                row_count = None
                size_bytes = None
                if with_data:
                    with conn.cursor() as cur:
                        cur.execute(f"SELECT COUNT(*) FROM {full_name}")
                        row_count = cur.fetchone()[0]

                        cur.execute(f"SELECT pg_relation_size('{schema_name}.{name}')")
                        size_bytes = cur.fetchone()[0]

            duration_ms = int((time.time() - start_time) * 1000)

            # Update tracking record with success
            await self.session.execute(
                update(managed_materialized_views)
                .where(managed_materialized_views.c.id == view_id)
                .values(
                    status="active",
                    row_count=row_count,
                    size_bytes=size_bytes,
                    last_refresh_at=datetime.utcnow() if with_data else None,
                    last_refresh_duration_ms=duration_ms if with_data else None,
                )
            )
            await self.session.commit()

            logger.info(f"Created materialized view {schema_name}.{name} ({row_count} rows)")

            return {
                "view_id": str(view_id),
                "name": name,
                "schema_name": schema_name,
                "status": "active",
                "row_count": row_count,
                "size_bytes": size_bytes,
                "duration_ms": duration_ms,
            }

        except Exception as e:
            # Update tracking record with failure
            await self.session.execute(
                update(managed_materialized_views)
                .where(managed_materialized_views.c.id == view_id)
                .values(
                    status="failed",
                    last_error=str(e),
                    error_count=1,
                )
            )
            await self.session.commit()

            logger.error(f"Failed to create materialized view {schema_name}.{name}: {e}")
            raise

    async def refresh_materialized_view(
        self,
        view_id: UUID,
        concurrently: bool = True,
    ) -> Dict[str, Any]:
        """Refresh a materialized view.

        Args:
            view_id: ID of the view to refresh
            concurrently: Whether to refresh concurrently (requires unique index)

        Returns:
            Dict with refresh results
        """
        from .materialized_view_models import managed_materialized_views

        # Get view record
        result = await self.session.execute(
            select(managed_materialized_views).where(
                managed_materialized_views.c.id == view_id
            )
        )
        row = result.fetchone()

        if not row:
            raise ValueError(f"Materialized view {view_id} not found")

        if row.status not in ("active", "failed"):
            raise ValueError(f"Cannot refresh view in status '{row.status}'")

        # Update status to refreshing
        await self.session.execute(
            update(managed_materialized_views)
            .where(managed_materialized_views.c.id == view_id)
            .values(status="refreshing")
        )
        await self.session.commit()

        try:
            start_time = time.time()

            full_name = f'"{row.schema_name}"."{row.name}"'
            refresh_sql = f"REFRESH MATERIALIZED VIEW"
            if concurrently:
                refresh_sql += " CONCURRENTLY"
            refresh_sql += f" {full_name}"

            # Execute refresh
            with self._get_write_connection(row.connection_id) as conn:
                with conn.cursor() as cur:
                    cur.execute(refresh_sql)
                conn.commit()

                # Get updated stats
                with conn.cursor() as cur:
                    cur.execute(f"SELECT COUNT(*) FROM {full_name}")
                    row_count = cur.fetchone()[0]

                    cur.execute(f"SELECT pg_relation_size('{row.schema_name}.{row.name}')")
                    size_bytes = cur.fetchone()[0]

            duration_ms = int((time.time() - start_time) * 1000)

            # Update tracking record
            await self.session.execute(
                update(managed_materialized_views)
                .where(managed_materialized_views.c.id == view_id)
                .values(
                    status="active",
                    row_count=row_count,
                    size_bytes=size_bytes,
                    last_refresh_at=datetime.utcnow(),
                    last_refresh_duration_ms=duration_ms,
                    last_error=None,
                )
            )
            await self.session.commit()

            logger.info(f"Refreshed materialized view {row.schema_name}.{row.name} ({row_count} rows, {duration_ms}ms)")

            return {
                "view_id": str(view_id),
                "name": row.name,
                "schema_name": row.schema_name,
                "status": "active",
                "row_count": row_count,
                "size_bytes": size_bytes,
                "duration_ms": duration_ms,
            }

        except Exception as e:
            # Update with error
            await self.session.execute(
                update(managed_materialized_views)
                .where(managed_materialized_views.c.id == view_id)
                .values(
                    status="failed",
                    last_error=str(e),
                    error_count=managed_materialized_views.c.error_count + 1,
                )
            )
            await self.session.commit()

            logger.error(f"Failed to refresh materialized view {view_id}: {e}")
            raise

    async def drop_materialized_view(
        self,
        view_id: UUID,
        if_exists: bool = True,
    ) -> Dict[str, Any]:
        """Drop a materialized view.

        Args:
            view_id: ID of the view to drop
            if_exists: Don't error if view doesn't exist in database

        Returns:
            Dict with drop results
        """
        from .materialized_view_models import managed_materialized_views

        # Get view record
        result = await self.session.execute(
            select(managed_materialized_views).where(
                managed_materialized_views.c.id == view_id
            )
        )
        row = result.fetchone()

        if not row:
            raise ValueError(f"Materialized view {view_id} not found in tracking")

        name = row.name
        schema_name = row.schema_name

        try:
            # Build DROP statement
            full_name = f'"{schema_name}"."{name}"'
            drop_sql = "DROP MATERIALIZED VIEW"
            if if_exists:
                drop_sql += " IF EXISTS"
            drop_sql += f" {full_name}"

            # Execute DDL
            with self._get_write_connection(row.connection_id) as conn:
                with conn.cursor() as cur:
                    cur.execute(drop_sql)
                conn.commit()

            # Delete tracking record
            await self.session.execute(
                delete(managed_materialized_views).where(
                    managed_materialized_views.c.id == view_id
                )
            )
            await self.session.commit()

            logger.info(f"Dropped materialized view {schema_name}.{name}")

            return {
                "view_id": str(view_id),
                "name": name,
                "schema_name": schema_name,
                "status": "dropped",
            }

        except Exception as e:
            logger.error(f"Failed to drop materialized view {view_id}: {e}")
            raise

    async def get_view(self, view_id: UUID) -> Optional[Dict[str, Any]]:
        """Get materialized view by ID.

        Args:
            view_id: View ID

        Returns:
            View dict or None
        """
        from .materialized_view_models import managed_materialized_views

        result = await self.session.execute(
            select(managed_materialized_views).where(
                managed_materialized_views.c.id == view_id
            )
        )
        row = result.fetchone()

        if not row:
            return None

        return {
            "id": str(row.id),
            "name": row.name,
            "schema_name": row.schema_name,
            "description": row.description,
            "source_query": row.source_query,
            "connection_id": row.connection_id,
            "status": row.status,
            "row_count": row.row_count,
            "size_bytes": row.size_bytes,
            "last_refresh_at": row.last_refresh_at.isoformat() if row.last_refresh_at else None,
            "last_refresh_duration_ms": row.last_refresh_duration_ms,
            "last_error": row.last_error,
            "error_count": row.error_count,
            "created_by": row.created_by,
            "created_at": row.created_at.isoformat() if row.created_at else None,
        }

    async def list_views(
        self,
        limit: int = 50,
        offset: int = 0,
        schema_name: Optional[str] = None,
        status: Optional[str] = None,
        created_by: Optional[str] = None,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """List materialized views with filtering.

        Args:
            limit: Max results
            offset: Pagination offset
            schema_name: Filter by schema
            status: Filter by status
            created_by: Filter by creator

        Returns:
            Tuple of (views list, total count)
        """
        from .materialized_view_models import managed_materialized_views

        # Build query
        query = select(managed_materialized_views)
        count_query = select(func.count(managed_materialized_views.c.id))

        if schema_name:
            query = query.where(managed_materialized_views.c.schema_name == schema_name)
            count_query = count_query.where(managed_materialized_views.c.schema_name == schema_name)

        if status:
            query = query.where(managed_materialized_views.c.status == status)
            count_query = count_query.where(managed_materialized_views.c.status == status)

        if created_by:
            query = query.where(managed_materialized_views.c.created_by == created_by)
            count_query = count_query.where(managed_materialized_views.c.created_by == created_by)

        query = query.order_by(managed_materialized_views.c.created_at.desc()).offset(offset).limit(limit)

        # Execute
        result = await self.session.execute(query)
        rows = result.fetchall()

        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0

        views = [
            {
                "id": str(row.id),
                "name": row.name,
                "schema_name": row.schema_name,
                "description": row.description,
                "status": row.status,
                "row_count": row.row_count,
                "size_bytes": row.size_bytes,
                "last_refresh_at": row.last_refresh_at.isoformat() if row.last_refresh_at else None,
                "created_by": row.created_by,
                "created_at": row.created_at.isoformat() if row.created_at else None,
            }
            for row in rows
        ]

        return views, total

    async def get_view_by_name(
        self,
        name: str,
        schema_name: str = "public",
    ) -> Optional[Dict[str, Any]]:
        """Get materialized view by name.

        Args:
            name: View name
            schema_name: Schema name

        Returns:
            View dict or None
        """
        from .materialized_view_models import managed_materialized_views

        result = await self.session.execute(
            select(managed_materialized_views).where(
                managed_materialized_views.c.schema_name == schema_name,
                managed_materialized_views.c.name == name,
            )
        )
        row = result.fetchone()

        if not row:
            return None

        return await self.get_view(row.id)
