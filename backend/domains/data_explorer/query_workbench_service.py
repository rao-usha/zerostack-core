"""Query Workbench service layer."""
import re
import logging
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from uuid import UUID
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from core.config import settings
from domains.data_explorer.service import DataExplorerService

logger = logging.getLogger(__name__)


class QueryWorkbenchService:
    """Service for managing saved queries and execution history."""

    def __init__(self, engine: Optional[Engine] = None):
        self.engine = engine or create_engine(settings.database_url)
        self.explorer_service = DataExplorerService()

    # ========================================
    # Saved Query CRUD
    # ========================================

    def create_query(
        self,
        name: str,
        sql: str,
        db_id: str = "default",
        description: Optional[str] = None,
        folder: Optional[str] = None,
        tags: Optional[List[str]] = None,
        parameters: Optional[List[Dict]] = None,
        is_public: bool = False,
        created_by: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new saved query."""
        query = """
            INSERT INTO saved_queries (
                name, description, sql, db_id, folder, tags,
                parameters, is_public, created_by
            )
            VALUES (
                :name, :description, :sql, :db_id, :folder, :tags,
                :parameters, :is_public, :created_by
            )
            RETURNING *
        """

        with self.engine.begin() as conn:
            result = conn.execute(text(query), {
                'name': name,
                'description': description,
                'sql': sql,
                'db_id': db_id,
                'folder': folder,
                'tags': tags,
                'parameters': parameters,
                'is_public': is_public,
                'created_by': created_by
            }).fetchone()

        return dict(result._mapping)

    def get_query(self, query_id: str) -> Optional[Dict[str, Any]]:
        """Get a saved query by ID."""
        query = "SELECT * FROM saved_queries WHERE id = :query_id"

        with self.engine.connect() as conn:
            result = conn.execute(text(query), {'query_id': query_id}).fetchone()

        if result:
            return dict(result._mapping)
        return None

    def update_query(
        self,
        query_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        sql: Optional[str] = None,
        folder: Optional[str] = None,
        tags: Optional[List[str]] = None,
        parameters: Optional[List[Dict]] = None,
        is_public: Optional[bool] = None,
        schedule_cron: Optional[str] = None,
        schedule_enabled: Optional[bool] = None,
        cache_ttl_seconds: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """Update a saved query."""
        updates = []
        params = {'query_id': query_id}

        if name is not None:
            updates.append("name = :name")
            params['name'] = name

        if description is not None:
            updates.append("description = :description")
            params['description'] = description

        if sql is not None:
            updates.append("sql = :sql")
            params['sql'] = sql

        if folder is not None:
            updates.append("folder = :folder")
            params['folder'] = folder

        if tags is not None:
            updates.append("tags = :tags")
            params['tags'] = tags

        if parameters is not None:
            updates.append("parameters = :parameters")
            params['parameters'] = parameters

        if is_public is not None:
            updates.append("is_public = :is_public")
            params['is_public'] = is_public

        if schedule_cron is not None:
            updates.append("schedule_cron = :schedule_cron")
            params['schedule_cron'] = schedule_cron

        if schedule_enabled is not None:
            updates.append("schedule_enabled = :schedule_enabled")
            params['schedule_enabled'] = schedule_enabled

        if cache_ttl_seconds is not None:
            updates.append("cache_ttl_seconds = :cache_ttl_seconds")
            params['cache_ttl_seconds'] = cache_ttl_seconds

        if not updates:
            return self.get_query(query_id)

        updates.append("updated_at = NOW()")

        query = f"""
            UPDATE saved_queries
            SET {', '.join(updates)}
            WHERE id = :query_id
            RETURNING *
        """

        with self.engine.begin() as conn:
            result = conn.execute(text(query), params).fetchone()

        if result:
            return dict(result._mapping)
        return None

    def delete_query(self, query_id: str) -> bool:
        """Delete a saved query."""
        query = "DELETE FROM saved_queries WHERE id = :query_id"

        with self.engine.begin() as conn:
            result = conn.execute(text(query), {'query_id': query_id})

        return result.rowcount > 0

    def list_queries(
        self,
        db_id: Optional[str] = None,
        folder: Optional[str] = None,
        tags: Optional[List[str]] = None,
        search: Optional[str] = None,
        created_by: Optional[str] = None,
        is_public: Optional[bool] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[Dict[str, Any]], int]:
        """List saved queries with filtering and pagination."""
        conditions = ["1=1"]
        params = {}

        if db_id:
            conditions.append("db_id = :db_id")
            params['db_id'] = db_id

        if folder:
            conditions.append("folder = :folder")
            params['folder'] = folder

        if tags:
            conditions.append("tags && :tags")  # Array overlap
            params['tags'] = tags

        if search:
            conditions.append("""
                (name ILIKE :search OR description ILIKE :search OR sql ILIKE :search)
            """)
            params['search'] = f"%{search}%"

        if created_by:
            conditions.append("created_by = :created_by")
            params['created_by'] = created_by

        if is_public is not None:
            conditions.append("is_public = :is_public")
            params['is_public'] = is_public

        where_clause = " AND ".join(conditions)

        # Get total count
        count_query = f"SELECT COUNT(*) FROM saved_queries WHERE {where_clause}"

        with self.engine.connect() as conn:
            total = conn.execute(text(count_query), params).scalar()

        # Get paginated results
        offset = (page - 1) * page_size
        params['limit'] = page_size
        params['offset'] = offset

        list_query = f"""
            SELECT id, name, description, db_id, folder, tags, is_public,
                   created_by, run_count, last_run_at, avg_execution_time_ms, created_at
            FROM saved_queries
            WHERE {where_clause}
            ORDER BY updated_at DESC
            LIMIT :limit OFFSET :offset
        """

        with self.engine.connect() as conn:
            results = conn.execute(text(list_query), params)
            queries = [dict(row._mapping) for row in results]

        return queries, total

    def get_folders(self, db_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get list of folders with query counts."""
        query = """
            SELECT folder, COUNT(*) as query_count
            FROM saved_queries
            WHERE folder IS NOT NULL
        """
        params = {}

        if db_id:
            query += " AND db_id = :db_id"
            params['db_id'] = db_id

        query += " GROUP BY folder ORDER BY folder"

        with self.engine.connect() as conn:
            results = conn.execute(text(query), params)
            return [{'name': row[0], 'query_count': row[1]} for row in results]

    # ========================================
    # Query Execution
    # ========================================

    def execute_query(
        self,
        query_id: str,
        parameters: Optional[Dict[str, Any]] = None,
        page: int = 1,
        page_size: int = 100,
        executed_by: Optional[str] = None,
        source: str = 'manual'
    ) -> Dict[str, Any]:
        """Execute a saved query and record the execution."""
        # Get the saved query
        saved_query = self.get_query(query_id)
        if not saved_query:
            raise ValueError(f"Query {query_id} not found")

        sql = saved_query['sql']
        db_id = saved_query['db_id']

        # Substitute parameters if provided
        if parameters:
            sql = self._substitute_parameters(sql, parameters)

        # Create execution record
        execution_id = self._create_execution(
            saved_query_id=query_id,
            sql_snapshot=sql,
            db_id=db_id,
            parameters_used=parameters,
            executed_by=executed_by,
            source=source
        )

        try:
            # Execute the query using the explorer service
            result = self.explorer_service.execute_query(
                sql=sql,
                page=page,
                page_size=page_size,
                db_id=db_id
            )

            # Update execution record with results
            self._update_execution_success(
                execution_id=execution_id,
                row_count=result.get('total_rows_estimate', len(result.get('rows', []))),
                column_count=len(result.get('columns', [])),
                execution_time_ms=result.get('execution_time_ms', 0),
                result_preview={
                    'columns': result.get('columns', []),
                    'rows': result.get('rows', [])[:10]  # Store first 10 rows as preview
                }
            )

            # Update saved query stats
            self._update_query_stats(query_id, result.get('execution_time_ms', 0))

            return {
                'execution_id': execution_id,
                'columns': result.get('columns', []),
                'rows': result.get('rows', []),
                'total_rows': result.get('total_rows_estimate', len(result.get('rows', []))),
                'execution_time_ms': result.get('execution_time_ms', 0),
                'page': page,
                'page_size': page_size
            }

        except Exception as e:
            # Update execution record with error
            self._update_execution_error(
                execution_id=execution_id,
                error_message=str(e),
                error_code=getattr(e, 'pgcode', 'UNKNOWN')
            )
            raise

    def execute_adhoc_query(
        self,
        sql: str,
        db_id: str = "default",
        parameters: Optional[Dict[str, Any]] = None,
        page: int = 1,
        page_size: int = 100,
        executed_by: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute an ad-hoc query (not saved) and record it."""
        # Substitute parameters if provided
        if parameters:
            sql = self._substitute_parameters(sql, parameters)

        # Create execution record (no saved_query_id)
        execution_id = self._create_execution(
            saved_query_id=None,
            sql_snapshot=sql,
            db_id=db_id,
            parameters_used=parameters,
            executed_by=executed_by,
            source='adhoc'
        )

        try:
            result = self.explorer_service.execute_query(
                sql=sql,
                page=page,
                page_size=page_size,
                db_id=db_id
            )

            self._update_execution_success(
                execution_id=execution_id,
                row_count=result.get('total_rows_estimate', len(result.get('rows', []))),
                column_count=len(result.get('columns', [])),
                execution_time_ms=result.get('execution_time_ms', 0),
                result_preview={
                    'columns': result.get('columns', []),
                    'rows': result.get('rows', [])[:10]
                }
            )

            return {
                'execution_id': execution_id,
                'columns': result.get('columns', []),
                'rows': result.get('rows', []),
                'total_rows': result.get('total_rows_estimate', len(result.get('rows', []))),
                'execution_time_ms': result.get('execution_time_ms', 0),
                'page': page,
                'page_size': page_size
            }

        except Exception as e:
            self._update_execution_error(
                execution_id=execution_id,
                error_message=str(e),
                error_code=getattr(e, 'pgcode', 'UNKNOWN')
            )
            raise

    def _substitute_parameters(self, sql: str, parameters: Dict[str, Any]) -> str:
        """Substitute {{param}} placeholders with values."""
        for name, value in parameters.items():
            placeholder = f"{{{{{name}}}}}"
            # Escape single quotes in string values
            if isinstance(value, str):
                value = value.replace("'", "''")
                replacement = f"'{value}'"
            elif value is None:
                replacement = "NULL"
            elif isinstance(value, bool):
                replacement = "TRUE" if value else "FALSE"
            else:
                replacement = str(value)

            sql = sql.replace(placeholder, replacement)

        return sql

    def _create_execution(
        self,
        sql_snapshot: str,
        db_id: str,
        saved_query_id: Optional[str] = None,
        parameters_used: Optional[Dict] = None,
        executed_by: Optional[str] = None,
        source: str = 'manual'
    ) -> str:
        """Create an execution record."""
        query = """
            INSERT INTO query_executions (
                saved_query_id, sql_snapshot, db_id, parameters_used,
                status, executed_by, source
            )
            VALUES (
                :saved_query_id, :sql_snapshot, :db_id, :parameters_used,
                'running', :executed_by, :source
            )
            RETURNING id
        """

        with self.engine.begin() as conn:
            result = conn.execute(text(query), {
                'saved_query_id': saved_query_id,
                'sql_snapshot': sql_snapshot,
                'db_id': db_id,
                'parameters_used': parameters_used,
                'executed_by': executed_by,
                'source': source
            }).fetchone()

        return str(result[0])

    def _update_execution_success(
        self,
        execution_id: str,
        row_count: int,
        column_count: int,
        execution_time_ms: float,
        result_preview: Dict
    ):
        """Update execution record with success results."""
        query = """
            UPDATE query_executions
            SET status = 'success',
                finished_at = NOW(),
                execution_time_ms = :execution_time_ms,
                row_count = :row_count,
                column_count = :column_count,
                result_preview = :result_preview
            WHERE id = :execution_id
        """

        with self.engine.begin() as conn:
            conn.execute(text(query), {
                'execution_id': execution_id,
                'execution_time_ms': execution_time_ms,
                'row_count': row_count,
                'column_count': column_count,
                'result_preview': result_preview
            })

    def _update_execution_error(
        self,
        execution_id: str,
        error_message: str,
        error_code: str
    ):
        """Update execution record with error details."""
        query = """
            UPDATE query_executions
            SET status = 'error',
                finished_at = NOW(),
                error_message = :error_message,
                error_code = :error_code
            WHERE id = :execution_id
        """

        with self.engine.begin() as conn:
            conn.execute(text(query), {
                'execution_id': execution_id,
                'error_message': error_message,
                'error_code': error_code
            })

    def _update_query_stats(self, query_id: str, execution_time_ms: float):
        """Update saved query execution statistics."""
        query = """
            UPDATE saved_queries
            SET run_count = run_count + 1,
                last_run_at = NOW(),
                avg_execution_time_ms = CASE
                    WHEN avg_execution_time_ms IS NULL THEN :execution_time_ms
                    ELSE (avg_execution_time_ms * run_count + :execution_time_ms) / (run_count + 1)
                END,
                updated_at = NOW()
            WHERE id = :query_id
        """

        with self.engine.begin() as conn:
            conn.execute(text(query), {
                'query_id': query_id,
                'execution_time_ms': execution_time_ms
            })

    # ========================================
    # Execution History
    # ========================================

    def get_execution(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get an execution record by ID."""
        query = "SELECT * FROM query_executions WHERE id = :execution_id"

        with self.engine.connect() as conn:
            result = conn.execute(text(query), {'execution_id': execution_id}).fetchone()

        if result:
            return dict(result._mapping)
        return None

    def get_query_executions(
        self,
        query_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get execution history for a saved query."""
        query = """
            SELECT * FROM query_executions
            WHERE saved_query_id = :query_id
            ORDER BY started_at DESC
            LIMIT :limit
        """

        with self.engine.connect() as conn:
            results = conn.execute(text(query), {
                'query_id': query_id,
                'limit': limit
            })
            return [dict(row._mapping) for row in results]

    def get_recent_executions(
        self,
        db_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get recent executions across all queries."""
        conditions = ["1=1"]
        params = {'limit': limit}

        if db_id:
            conditions.append("db_id = :db_id")
            params['db_id'] = db_id

        if status:
            conditions.append("status = :status")
            params['status'] = status

        where_clause = " AND ".join(conditions)

        query = f"""
            SELECT * FROM query_executions
            WHERE {where_clause}
            ORDER BY started_at DESC
            LIMIT :limit
        """

        with self.engine.connect() as conn:
            results = conn.execute(text(query), params)
            return [dict(row._mapping) for row in results]

    # ========================================
    # Clone Query
    # ========================================

    def clone_query(
        self,
        query_id: str,
        new_name: str,
        created_by: Optional[str] = None
    ) -> Dict[str, Any]:
        """Clone a saved query."""
        original = self.get_query(query_id)
        if not original:
            raise ValueError(f"Query {query_id} not found")

        return self.create_query(
            name=new_name,
            sql=original['sql'],
            db_id=original['db_id'],
            description=original.get('description'),
            folder=original.get('folder'),
            tags=original.get('tags'),
            parameters=original.get('parameters'),
            is_public=False,  # Clones start as private
            created_by=created_by
        )


# Singleton instance
_service_instance: Optional[QueryWorkbenchService] = None


def get_query_workbench_service() -> QueryWorkbenchService:
    """Get singleton query workbench service instance."""
    global _service_instance
    if _service_instance is None:
        _service_instance = QueryWorkbenchService()
    return _service_instance
