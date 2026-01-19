"""SQL execution service for notebooks."""
import logging
import time
from datetime import datetime
from typing import List, Dict, Any, Tuple, Optional
from uuid import UUID

import asyncpg
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.encryption import decrypt_password
from domains.data_connections.db_models import data_connections

logger = logging.getLogger(__name__)


class SQLExecutor:
    """Executes SQL queries against connected data sources."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def execute_sql(
        self,
        connection_id: UUID,
        sql: str,
        limit: int = 1000,
        timeout_seconds: int = 60
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], int, Optional[str]]:
        """
        Execute SQL query against a data connection.
        
        Args:
            connection_id: Data connection to use
            sql: SQL query to execute
            limit: Max rows to return
            timeout_seconds: Query timeout
            
        Returns:
            (rows, columns, total_count, error)
        """
        # Get connection details
        stmt = select(data_connections).where(data_connections.c.id == connection_id)
        result = await self.session.execute(stmt)
        conn = result.fetchone()
        
        if not conn:
            return [], [], 0, f"Connection {connection_id} not found"
        
        if conn.connection_type == "postgresql":
            return await self._execute_postgres(conn, sql, limit, timeout_seconds)
        else:
            return [], [], 0, f"Unsupported connection type: {conn.connection_type}"
    
    async def _execute_postgres(
        self,
        conn,
        sql: str,
        limit: int,
        timeout_seconds: int
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], int, Optional[str]]:
        """Execute SQL on PostgreSQL."""
        try:
            pg_conn = await asyncpg.connect(
                host=conn.host,
                port=conn.port or 5432,
                database=conn.database,
                user=conn.username,
                password=decrypt_password(conn.password_encrypted),
                timeout=timeout_seconds,
                command_timeout=timeout_seconds
            )
            
            try:
                # Check if query is a SELECT (read-only for now)
                sql_upper = sql.strip().upper()
                if not sql_upper.startswith('SELECT') and not sql_upper.startswith('WITH'):
                    return [], [], 0, "Only SELECT queries are allowed in notebooks"
                
                # Add LIMIT if not present
                sql_limited = sql.strip().rstrip(';')
                if 'LIMIT' not in sql_upper:
                    sql_limited = f"SELECT * FROM ({sql_limited}) AS _subq LIMIT {limit + 1}"
                
                # Execute query
                rows = await pg_conn.fetch(sql_limited)
                
                # Check if results were truncated
                total_count = len(rows)
                truncated = total_count > limit
                if truncated:
                    rows = rows[:limit]
                    total_count = limit  # Approximate
                
                # Extract columns from first row
                columns = []
                if rows:
                    # Get column info from the result
                    for key in rows[0].keys():
                        val = rows[0][key]
                        col_type = self._get_type_name(val)
                        columns.append({"name": key, "type": col_type})
                
                # Convert rows to dicts with JSON-safe values
                row_dicts = []
                for row in rows:
                    row_dict = {}
                    for key, val in row.items():
                        row_dict[key] = self._to_json_safe(val)
                    row_dicts.append(row_dict)
                
                return row_dicts, columns, total_count, None
                
            finally:
                await pg_conn.close()
                
        except asyncpg.exceptions.QueryCanceledError:
            return [], [], 0, f"Query timed out after {timeout_seconds} seconds"
        except asyncpg.exceptions.PostgresSyntaxError as e:
            return [], [], 0, f"SQL syntax error: {e}"
        except Exception as e:
            logger.error(f"SQL execution error: {e}")
            return [], [], 0, str(e)
    
    def _get_type_name(self, value: Any) -> str:
        """Get a simple type name for a Python value."""
        if value is None:
            return "unknown"
        elif isinstance(value, bool):
            return "boolean"
        elif isinstance(value, int):
            return "integer"
        elif isinstance(value, float):
            return "float"
        elif isinstance(value, str):
            return "string"
        elif isinstance(value, datetime):
            return "timestamp"
        elif isinstance(value, (bytes, bytearray)):
            return "bytes"
        elif isinstance(value, (list, tuple)):
            return "array"
        elif isinstance(value, dict):
            return "json"
        else:
            return type(value).__name__
    
    def _to_json_safe(self, value: Any) -> Any:
        """Convert a value to JSON-safe format."""
        if value is None:
            return None
        elif isinstance(value, (bool, int, float, str)):
            return value
        elif isinstance(value, datetime):
            return value.isoformat()
        elif isinstance(value, (bytes, bytearray)):
            return value.hex()
        elif isinstance(value, (list, tuple)):
            return [self._to_json_safe(v) for v in value]
        elif isinstance(value, dict):
            return {k: self._to_json_safe(v) for k, v in value.items()}
        elif hasattr(value, 'isoformat'):
            return value.isoformat()
        else:
            return str(value)
