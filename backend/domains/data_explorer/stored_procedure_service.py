"""Stored Procedure Service for creating and managing stored procedures.

Provides functionality to:
- Create stored procedures/functions from user definitions
- Execute stored procedures with parameters
- Drop stored procedures
- Track procedure metadata and execution history

SECURITY NOTE: This service allows creating executable code in the database.
Strong validation is applied to prevent dangerous operations.
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

logger = logging.getLogger(__name__)


# Allowed languages for stored procedures
ALLOWED_LANGUAGES = {'plpgsql', 'sql'}

# Schema whitelist - only allow creating procedures in these schemas
ALLOWED_SCHEMAS = {'public', 'analytics', 'reports', 'procedures'}

# Reserved names that cannot be used
RESERVED_PREFIXES = {'pg_', 'sql_', 'information_schema', 'system', 'admin'}

# Dangerous patterns that are blocked in procedure body
DANGEROUS_PATTERNS = [
    # System modification
    r'\bALTER\s+SYSTEM\b',
    r'\bCREATE\s+ROLE\b',
    r'\bDROP\s+ROLE\b',
    r'\bALTER\s+ROLE\b',
    r'\bCREATE\s+USER\b',
    r'\bDROP\s+USER\b',
    r'\bGRANT\b',
    r'\bREVOKE\b',
    # Extension management
    r'\bCREATE\s+EXTENSION\b',
    r'\bDROP\s+EXTENSION\b',
    # Dangerous functions
    r'\bpg_read_file\b',
    r'\bpg_write_file\b',
    r'\bpg_file_',
    r'\blo_import\b',
    r'\blo_export\b',
    # Shell commands
    r'\bCOPY\s+.*\s+TO\s+PROGRAM\b',
    r'\bCOPY\s+.*\s+FROM\s+PROGRAM\b',
    # Database management
    r'\bCREATE\s+DATABASE\b',
    r'\bDROP\s+DATABASE\b',
    r'\bALTER\s+DATABASE\b',
    # Tablespace
    r'\bCREATE\s+TABLESPACE\b',
    r'\bDROP\s+TABLESPACE\b',
]


class StoredProcedureService:
    """Service for managing stored procedures."""

    def __init__(self, session: AsyncSession):
        """Initialize stored procedure service.

        Args:
            session: Async database session for tracking procedures
        """
        self.session = session

    @staticmethod
    def _get_write_connection(connection_id: str = "default"):
        """Get a database connection with write permissions."""
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
    def validate_procedure_name(name: str) -> Tuple[bool, Optional[str]]:
        """Validate procedure name.

        Args:
            name: Proposed procedure name

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not name:
            return False, "Procedure name cannot be empty"

        if len(name) > 63:
            return False, "Procedure name cannot exceed 63 characters"

        if not re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', name):
            return False, "Procedure name must start with a letter and contain only letters, numbers, and underscores"

        name_lower = name.lower()
        for reserved in RESERVED_PREFIXES:
            if name_lower.startswith(reserved):
                return False, f"Procedure name cannot start with '{reserved}'"

        return True, None

    @staticmethod
    def validate_schema(schema: str) -> Tuple[bool, Optional[str]]:
        """Validate schema name is allowed."""
        if schema.lower() not in ALLOWED_SCHEMAS:
            return False, f"Schema '{schema}' is not allowed. Allowed schemas: {', '.join(sorted(ALLOWED_SCHEMAS))}"
        return True, None

    @staticmethod
    def validate_language(language: str) -> Tuple[bool, Optional[str]]:
        """Validate procedure language."""
        if language.lower() not in ALLOWED_LANGUAGES:
            return False, f"Language '{language}' is not allowed. Allowed: {', '.join(sorted(ALLOWED_LANGUAGES))}"
        return True, None

    @staticmethod
    def validate_procedure_body(body: str) -> Tuple[bool, Optional[str]]:
        """Validate procedure body for dangerous patterns.

        Args:
            body: Procedure source code

        Returns:
            Tuple of (is_safe, error_message)
        """
        body_upper = body.upper()

        for pattern in DANGEROUS_PATTERNS:
            if re.search(pattern, body_upper, re.IGNORECASE):
                return False, f"Procedure body contains disallowed pattern: {pattern}"

        return True, None

    @staticmethod
    def _build_parameter_string(parameters: List[Dict[str, Any]]) -> str:
        """Build parameter string for CREATE FUNCTION.

        Args:
            parameters: List of parameter definitions

        Returns:
            Parameter string like "p_id INTEGER, p_name TEXT DEFAULT 'test'"
        """
        if not parameters:
            return ""

        parts = []
        for param in parameters:
            name = param.get("name", "")
            ptype = param.get("type", "TEXT")
            mode = param.get("mode", "IN").upper()
            default = param.get("default")

            part = f"{mode} {name} {ptype}" if mode != "IN" else f"{name} {ptype}"
            if default is not None:
                part += f" DEFAULT {default}"
            parts.append(part)

        return ", ".join(parts)

    async def create_procedure(
        self,
        name: str,
        source_code: str,
        schema_name: str = "public",
        description: Optional[str] = None,
        language: str = "plpgsql",
        parameters: Optional[List[Dict[str, Any]]] = None,
        return_type: Optional[str] = None,
        returns_set: bool = False,
        volatility: str = "volatile",
        connection_id: str = "default",
        created_by: Optional[str] = None,
        conversation_id: Optional[UUID] = None,
    ) -> Dict[str, Any]:
        """Create a new stored procedure/function.

        Args:
            name: Name for the procedure
            source_code: Function body (without CREATE FUNCTION wrapper)
            schema_name: Schema to create procedure in
            description: Optional description
            language: Procedure language (plpgsql, sql)
            parameters: List of parameter definitions
            return_type: Return type (null for void)
            returns_set: Whether function returns a set
            volatility: volatile, stable, or immutable
            connection_id: Database connection to use
            created_by: User who created the procedure
            conversation_id: Optional link to chat conversation

        Returns:
            Dict with procedure creation results
        """
        from .stored_procedure_models import managed_procedures

        # Validate inputs
        is_valid, error = self.validate_procedure_name(name)
        if not is_valid:
            raise ValueError(error)

        is_valid, error = self.validate_schema(schema_name)
        if not is_valid:
            raise ValueError(error)

        is_valid, error = self.validate_language(language)
        if not is_valid:
            raise ValueError(error)

        is_valid, error = self.validate_procedure_body(source_code)
        if not is_valid:
            raise ValueError(error)

        if volatility not in ('volatile', 'stable', 'immutable'):
            raise ValueError(f"Invalid volatility: {volatility}")

        parameters = parameters or []

        # Check if procedure already exists in tracking
        existing = await self.session.execute(
            select(managed_procedures).where(
                managed_procedures.c.schema_name == schema_name,
                managed_procedures.c.name == name,
            )
        )
        if existing.fetchone():
            raise ValueError(f"Procedure '{schema_name}.{name}' already exists in tracking")

        # Create tracking record
        proc_id = uuid4()
        await self.session.execute(
            managed_procedures.insert().values(
                id=proc_id,
                name=name,
                schema_name=schema_name,
                description=description,
                language=language,
                source_code=source_code,
                parameters=parameters,
                return_type=return_type,
                returns_set=returns_set,
                volatility=volatility,
                connection_id=connection_id,
                status="creating",
                created_by=created_by,
                conversation_id=conversation_id,
            )
        )
        await self.session.commit()

        try:
            # Build CREATE FUNCTION statement
            full_name = f'"{schema_name}"."{name}"'
            param_str = self._build_parameter_string(parameters)

            # Determine return clause
            if return_type:
                return_clause = f"RETURNS {'SETOF ' if returns_set else ''}{return_type}"
            else:
                return_clause = "RETURNS void"

            create_sql = f"""
            CREATE OR REPLACE FUNCTION {full_name}({param_str})
            {return_clause}
            LANGUAGE {language}
            {volatility.upper()}
            AS $func$
            {source_code}
            $func$
            """

            # Execute DDL
            with self._get_write_connection(connection_id) as conn:
                with conn.cursor() as cur:
                    cur.execute(create_sql)
                conn.commit()

            # Update tracking record with success
            await self.session.execute(
                update(managed_procedures)
                .where(managed_procedures.c.id == proc_id)
                .values(status="active")
            )
            await self.session.commit()

            logger.info(f"Created procedure {schema_name}.{name}")

            return {
                "procedure_id": str(proc_id),
                "name": name,
                "schema_name": schema_name,
                "status": "active",
                "language": language,
                "return_type": return_type or "void",
            }

        except Exception as e:
            # Update tracking record with failure
            await self.session.execute(
                update(managed_procedures)
                .where(managed_procedures.c.id == proc_id)
                .values(
                    status="failed",
                    last_error=str(e),
                    error_count=1,
                )
            )
            await self.session.commit()

            logger.error(f"Failed to create procedure {schema_name}.{name}: {e}")
            raise

    async def execute_procedure(
        self,
        proc_id: UUID,
        arguments: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Execute a stored procedure.

        Args:
            proc_id: ID of the procedure to execute
            arguments: Named arguments to pass

        Returns:
            Dict with execution results
        """
        from .stored_procedure_models import managed_procedures

        # Get procedure record
        result = await self.session.execute(
            select(managed_procedures).where(
                managed_procedures.c.id == proc_id
            )
        )
        row = result.fetchone()

        if not row:
            raise ValueError(f"Procedure {proc_id} not found")

        if row.status != "active":
            raise ValueError(f"Cannot execute procedure in status '{row.status}'")

        arguments = arguments or {}

        try:
            start_time = time.time()

            full_name = f'"{row.schema_name}"."{row.name}"'

            # Build argument string
            if arguments:
                # Use named parameters for safety
                arg_parts = [f"{k} => %s" for k in arguments.keys()]
                arg_str = ", ".join(arg_parts)
                arg_values = list(arguments.values())
            else:
                arg_str = ""
                arg_values = []

            execute_sql = f"SELECT * FROM {full_name}({arg_str})"

            # Execute procedure
            with self._get_write_connection(row.connection_id) as conn:
                with conn.cursor() as cur:
                    cur.execute(execute_sql, arg_values)

                    # Fetch results if any
                    if cur.description:
                        columns = [desc[0] for desc in cur.description]
                        rows = cur.fetchall()
                        result_data = [dict(zip(columns, r)) for r in rows]
                    else:
                        columns = []
                        result_data = []

                conn.commit()

            duration_ms = int((time.time() - start_time) * 1000)

            # Update execution stats
            current_count = row.execution_count or 0
            current_avg = row.avg_execution_ms or 0
            new_count = current_count + 1
            new_avg = int((current_avg * current_count + duration_ms) / new_count)

            await self.session.execute(
                update(managed_procedures)
                .where(managed_procedures.c.id == proc_id)
                .values(
                    execution_count=new_count,
                    last_executed_at=datetime.utcnow(),
                    avg_execution_ms=new_avg,
                    last_error=None,
                )
            )
            await self.session.commit()

            logger.info(f"Executed procedure {row.schema_name}.{row.name} in {duration_ms}ms")

            return {
                "procedure_id": str(proc_id),
                "name": row.name,
                "schema_name": row.schema_name,
                "columns": columns,
                "rows": result_data,
                "row_count": len(result_data),
                "duration_ms": duration_ms,
            }

        except Exception as e:
            # Update error stats
            await self.session.execute(
                update(managed_procedures)
                .where(managed_procedures.c.id == proc_id)
                .values(
                    last_error=str(e),
                    error_count=managed_procedures.c.error_count + 1,
                )
            )
            await self.session.commit()

            logger.error(f"Failed to execute procedure {proc_id}: {e}")
            raise

    async def drop_procedure(
        self,
        proc_id: UUID,
        if_exists: bool = True,
    ) -> Dict[str, Any]:
        """Drop a stored procedure.

        Args:
            proc_id: ID of the procedure to drop
            if_exists: Don't error if procedure doesn't exist

        Returns:
            Dict with drop results
        """
        from .stored_procedure_models import managed_procedures

        # Get procedure record
        result = await self.session.execute(
            select(managed_procedures).where(
                managed_procedures.c.id == proc_id
            )
        )
        row = result.fetchone()

        if not row:
            raise ValueError(f"Procedure {proc_id} not found in tracking")

        name = row.name
        schema_name = row.schema_name

        try:
            # Build parameter types for DROP (needed for overloaded functions)
            param_types = []
            for param in row.parameters or []:
                param_types.append(param.get("type", "TEXT"))

            full_name = f'"{schema_name}"."{name}"'
            type_str = ", ".join(param_types) if param_types else ""

            drop_sql = "DROP FUNCTION"
            if if_exists:
                drop_sql += " IF EXISTS"
            drop_sql += f" {full_name}({type_str})"

            # Execute DDL
            with self._get_write_connection(row.connection_id) as conn:
                with conn.cursor() as cur:
                    cur.execute(drop_sql)
                conn.commit()

            # Delete tracking record
            await self.session.execute(
                delete(managed_procedures).where(
                    managed_procedures.c.id == proc_id
                )
            )
            await self.session.commit()

            logger.info(f"Dropped procedure {schema_name}.{name}")

            return {
                "procedure_id": str(proc_id),
                "name": name,
                "schema_name": schema_name,
                "status": "dropped",
            }

        except Exception as e:
            logger.error(f"Failed to drop procedure {proc_id}: {e}")
            raise

    async def get_procedure(self, proc_id: UUID) -> Optional[Dict[str, Any]]:
        """Get procedure by ID."""
        from .stored_procedure_models import managed_procedures

        result = await self.session.execute(
            select(managed_procedures).where(
                managed_procedures.c.id == proc_id
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
            "language": row.language,
            "source_code": row.source_code,
            "parameters": row.parameters,
            "return_type": row.return_type,
            "returns_set": row.returns_set,
            "volatility": row.volatility,
            "connection_id": row.connection_id,
            "status": row.status,
            "execution_count": row.execution_count,
            "last_executed_at": row.last_executed_at.isoformat() if row.last_executed_at else None,
            "avg_execution_ms": row.avg_execution_ms,
            "last_error": row.last_error,
            "error_count": row.error_count,
            "created_by": row.created_by,
            "created_at": row.created_at.isoformat() if row.created_at else None,
        }

    async def list_procedures(
        self,
        limit: int = 50,
        offset: int = 0,
        schema_name: Optional[str] = None,
        status: Optional[str] = None,
        language: Optional[str] = None,
        created_by: Optional[str] = None,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """List procedures with filtering."""
        from .stored_procedure_models import managed_procedures

        query = select(managed_procedures)
        count_query = select(func.count(managed_procedures.c.id))

        if schema_name:
            query = query.where(managed_procedures.c.schema_name == schema_name)
            count_query = count_query.where(managed_procedures.c.schema_name == schema_name)

        if status:
            query = query.where(managed_procedures.c.status == status)
            count_query = count_query.where(managed_procedures.c.status == status)

        if language:
            query = query.where(managed_procedures.c.language == language)
            count_query = count_query.where(managed_procedures.c.language == language)

        if created_by:
            query = query.where(managed_procedures.c.created_by == created_by)
            count_query = count_query.where(managed_procedures.c.created_by == created_by)

        query = query.order_by(managed_procedures.c.created_at.desc()).offset(offset).limit(limit)

        result = await self.session.execute(query)
        rows = result.fetchall()

        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0

        procedures = [
            {
                "id": str(row.id),
                "name": row.name,
                "schema_name": row.schema_name,
                "description": row.description,
                "language": row.language,
                "return_type": row.return_type or "void",
                "status": row.status,
                "execution_count": row.execution_count,
                "last_executed_at": row.last_executed_at.isoformat() if row.last_executed_at else None,
                "created_by": row.created_by,
                "created_at": row.created_at.isoformat() if row.created_at else None,
            }
            for row in rows
        ]

        return procedures, total

    async def get_procedure_by_name(
        self,
        name: str,
        schema_name: str = "public",
    ) -> Optional[Dict[str, Any]]:
        """Get procedure by name."""
        from .stored_procedure_models import managed_procedures

        result = await self.session.execute(
            select(managed_procedures).where(
                managed_procedures.c.schema_name == schema_name,
                managed_procedures.c.name == name,
            )
        )
        row = result.fetchone()

        if not row:
            return None

        return await self.get_procedure(row.id)
