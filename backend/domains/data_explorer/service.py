"""
Data Explorer service layer.

Handles business logic for schema browsing, table inspection, and safe query execution.
All queries are validated to ensure read-only access.
"""
import re
import time
from typing import List, Dict, Any, Optional, Tuple
from .connection import get_explorer_connection
from .models import (
    SchemaInfo, TableInfo, ColumnInfo, TableRowsResponse,
    QueryResponse, TableSummaryResponse, ErrorResponse
)


# Forbidden SQL keywords that indicate write operations
FORBIDDEN_KEYWORDS = {
    'INSERT', 'UPDATE', 'DELETE', 'DROP', 'CREATE', 'ALTER',
    'TRUNCATE', 'GRANT', 'REVOKE', 'EXECUTE', 'EXEC',
    'CALL', 'MERGE', 'REPLACE', 'RENAME', 'COMMENT'
}


class QueryValidator:
    """Validates SQL queries for read-only safety."""
    
    @staticmethod
    def is_safe_query(sql: str) -> Tuple[bool, Optional[str]]:
        """
        Check if a SQL query is safe (read-only).
        
        Args:
            sql: SQL query string
            
        Returns:
            Tuple of (is_safe, error_message)
        """
        sql_upper = sql.upper().strip()
        
        # Must start with SELECT (after removing comments and whitespace)
        # Remove SQL comments first
        sql_no_comments = re.sub(r'--.*?(\n|$)', '', sql_upper)
        sql_no_comments = re.sub(r'/\*.*?\*/', '', sql_no_comments, flags=re.DOTALL)
        sql_no_comments = sql_no_comments.strip()
        
        if not sql_no_comments.startswith('SELECT') and not sql_no_comments.startswith('WITH'):
            return False, "Only SELECT queries are allowed"
        
        # Check for forbidden keywords
        for keyword in FORBIDDEN_KEYWORDS:
            # Use word boundaries to avoid false positives (e.g., "INSERTED" column name)
            pattern = r'\b' + keyword + r'\b'
            if re.search(pattern, sql_upper):
                return False, f"Query contains forbidden keyword: {keyword}"
        
        # Additional safety: check for semicolon-separated multiple statements
        # This is a simple check; more sophisticated parsing would be better
        statements = sql.split(';')
        non_empty_statements = [s.strip() for s in statements if s.strip()]
        if len(non_empty_statements) > 1:
            return False, "Multiple statements are not allowed"
        
        return True, None


class DataExplorerService:
    """Service for exploring database schema and executing safe queries."""
    
    @staticmethod
    def get_schemas(db_id: str = "default") -> List[SchemaInfo]:
        """
        Get list of all schemas in the database.
        
        Args:
            db_id: Database configuration ID
        
        Returns:
            List of schema information
        """
        with get_explorer_connection(db_id) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT 
                        schema_name,
                        (SELECT COUNT(*) 
                         FROM information_schema.tables t 
                         WHERE t.table_schema = schema_name) as table_count
                    FROM information_schema.schemata
                    WHERE schema_name NOT IN ('information_schema', 'pg_catalog', 'pg_toast')
                    ORDER BY schema_name
                """)
                results = cur.fetchall()
                
        return [SchemaInfo(name=row[0], table_count=row[1]) for row in results]
    
    @staticmethod
    def get_tables(schema: str = "public", db_id: str = "default") -> List[TableInfo]:
        """
        Get list of tables and views in a schema.
        
        Args:
            schema: Schema name (default: public)
            db_id: Database configuration ID
            
        Returns:
            List of table information
        """
        with get_explorer_connection(db_id) as conn:
            with conn.cursor() as cur:
                # Get tables and views
                cur.execute("""
                    SELECT 
                        table_schema,
                        table_name,
                        table_type,
                        (SELECT reltuples::bigint 
                         FROM pg_class c 
                         JOIN pg_namespace n ON n.oid = c.relnamespace
                         WHERE n.nspname = table_schema 
                         AND c.relname = table_name) as row_estimate
                    FROM information_schema.tables
                    WHERE table_schema = %s
                    AND table_type IN ('BASE TABLE', 'VIEW')
                    ORDER BY table_name
                """, (schema,))
                results = cur.fetchall()
                
        return [
            TableInfo(
                schema=row[0],
                name=row[1],
                type='table' if row[2] == 'BASE TABLE' else 'view',
                row_estimate=row[3] if row[3] else None
            )
            for row in results
        ]
    
    @staticmethod
    def get_columns(schema: str, table: str, db_id: str = "default") -> List[ColumnInfo]:
        """
        Get column information for a table.
        
        Args:
            schema: Schema name
            table: Table name
            db_id: Database configuration ID
            
        Returns:
            List of column information
        """
        with get_explorer_connection(db_id) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT 
                        column_name,
                        data_type,
                        is_nullable,
                        column_default,
                        ordinal_position
                    FROM information_schema.columns
                    WHERE table_schema = %s AND table_name = %s
                    ORDER BY ordinal_position
                """, (schema, table))
                results = cur.fetchall()
                
        return [
            ColumnInfo(
                name=row[0],
                data_type=row[1],
                is_nullable=(row[2] == 'YES'),
                default=row[3],
                ordinal_position=row[4]
            )
            for row in results
        ]
    
    @staticmethod
    def get_table_rows(
        schema: str,
        table: str,
        page: int = 1,
        page_size: int = 50,
        db_id: str = "default"
    ) -> TableRowsResponse:
        """
        Get paginated rows from a table.
        
        Args:
            schema: Schema name
            table: Table name
            page: Page number (1-indexed)
            page_size: Number of rows per page
            db_id: Database configuration ID
            
        Returns:
            Table rows response with pagination info
        """
        offset = (page - 1) * page_size
        
        # Build safe query using identifier quoting
        with get_explorer_connection(db_id) as conn:
            with conn.cursor() as cur:
                # Get column names
                cur.execute("""
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_schema = %s AND table_name = %s
                    ORDER BY ordinal_position
                """, (schema, table))
                columns = [row[0] for row in cur.fetchall()]
                
                if not columns:
                    raise ValueError(f"Table {schema}.{table} not found or has no columns")
                
                # Get total row count estimate
                cur.execute("""
                    SELECT reltuples::bigint
                    FROM pg_class c
                    JOIN pg_namespace n ON n.oid = c.relnamespace
                    WHERE n.nspname = %s AND c.relname = %s
                """, (schema, table))
                result = cur.fetchone()
                total_rows = result[0] if result and result[0] else None
                
                # Get rows with pagination
                # Use parameterized query with quoted identifiers
                from psycopg import sql
                query = sql.SQL("SELECT * FROM {}.{} LIMIT %s OFFSET %s").format(
                    sql.Identifier(schema),
                    sql.Identifier(table)
                )
                cur.execute(query, (page_size, offset))
                rows = cur.fetchall()
                
        return TableRowsResponse(
            schema=schema,
            table=table,
            columns=columns,
            rows=[list(row) for row in rows],
            page=page,
            page_size=page_size,
            total_rows=total_rows
        )
    
    @staticmethod
    def execute_query(
        sql: str,
        page: int = 1,
        page_size: int = 100,
        db_id: str = "default"
    ) -> QueryResponse:
        """
        Execute a read-only SQL query with safety validation.
        
        Args:
            sql: SQL query to execute
            page: Page number (1-indexed)
            page_size: Number of rows per page
            db_id: Database configuration ID
            
        Returns:
            Query response with results or error
        """
        # Validate query safety
        is_safe, error_msg = QueryValidator.is_safe_query(sql)
        if not is_safe:
            return QueryResponse(
                columns=[],
                rows=[],
                total_rows_estimate=None,
                execution_time_ms=0,
                error={"message": error_msg, "code": "UNSAFE_QUERY"}
            )
        
        start_time = time.time()
        
        try:
            with get_explorer_connection(db_id) as conn:
                # Set statement timeout for safety (30 seconds)
                with conn.cursor() as cur:
                    cur.execute("SET statement_timeout = '30s'")
                    
                    # Execute the query
                    cur.execute(sql)
                    
                    # Get column names
                    columns = [desc[0] for desc in cur.description] if cur.description else []
                    
                    # Fetch all results (we'll apply pagination in memory for simplicity)
                    # For very large result sets, this could be optimized
                    all_rows = cur.fetchall()
                    
                    # Apply pagination
                    offset = (page - 1) * page_size
                    paginated_rows = all_rows[offset:offset + page_size]
                    
                    execution_time = (time.time() - start_time) * 1000  # ms
                    
            return QueryResponse(
                columns=columns,
                rows=[list(row) for row in paginated_rows],
                total_rows_estimate=len(all_rows),
                execution_time_ms=round(execution_time, 2),
                error=None
            )
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            
            # Extract error code if available
            error_code = getattr(e, 'pgcode', None) or 'DB_ERROR'
            
            return QueryResponse(
                columns=[],
                rows=[],
                total_rows_estimate=None,
                execution_time_ms=round(execution_time, 2),
                error={"message": str(e), "code": error_code}
            )
    
    @staticmethod
    def get_table_summary(schema: str, table: str, db_id: str = "default") -> TableSummaryResponse:
        """
        Get summary statistics for a table.
        
        Args:
            schema: Schema name
            table: Table name
            db_id: Database configuration ID
            
        Returns:
            Table summary with column statistics
        """
        with get_explorer_connection(db_id) as conn:
            with conn.cursor() as cur:
                # Get column info
                cur.execute("""
                    SELECT 
                        column_name,
                        data_type
                    FROM information_schema.columns
                    WHERE table_schema = %s AND table_name = %s
                    ORDER BY ordinal_position
                """, (schema, table))
                columns = cur.fetchall()
                
                column_stats = {}
                
                for col_name, data_type in columns:
                    stats = {"data_type": data_type}
                    
                    from psycopg import sql
                    
                    # Get distinct count (limited for performance)
                    try:
                        query = sql.SQL("""
                            SELECT COUNT(DISTINCT {col}) 
                            FROM (SELECT {col} FROM {schema}.{table} LIMIT 10000) sub
                        """).format(
                            col=sql.Identifier(col_name),
                            schema=sql.Identifier(schema),
                            table=sql.Identifier(table)
                        )
                        cur.execute(query)
                        stats['distinct_count'] = cur.fetchone()[0]
                    except:
                        stats['distinct_count'] = None
                    
                    # For numeric types, get min/max/avg
                    if data_type in ('integer', 'bigint', 'smallint', 'numeric', 'decimal', 'real', 'double precision'):
                        try:
                            query = sql.SQL("""
                                SELECT 
                                    MIN({col}),
                                    MAX({col}),
                                    AVG({col}),
                                    COUNT({col})
                                FROM {schema}.{table}
                            """).format(
                                col=sql.Identifier(col_name),
                                schema=sql.Identifier(schema),
                                table=sql.Identifier(table)
                            )
                            cur.execute(query)
                            min_val, max_val, avg_val, count_val = cur.fetchone()
                            stats['min'] = float(min_val) if min_val is not None else None
                            stats['max'] = float(max_val) if max_val is not None else None
                            stats['avg'] = float(avg_val) if avg_val is not None else None
                            stats['count'] = count_val
                        except:
                            pass
                    
                    column_stats[col_name] = stats
                
        return TableSummaryResponse(
            schema=schema,
            table=table,
            column_stats=column_stats
        )
    
    @staticmethod
    def profile_table(
        schema: str,
        table: str,
        max_distinct: int = 50,
        db_id: str = "default"
    ) -> Dict[str, Any]:
        """
        Generate detailed profile for a table with enhanced statistics.
        
        Args:
            schema: Schema name
            table: Table name
            max_distinct: Maximum number of distinct values to return for categorical columns
            db_id: Database configuration ID
            
        Returns:
            Dict with comprehensive per-column profile
        """
        with get_explorer_connection(db_id) as conn:
            with conn.cursor() as cur:
                # Get column info
                cur.execute("""
                    SELECT 
                        column_name,
                        data_type,
                        is_nullable
                    FROM information_schema.columns
                    WHERE table_schema = %s AND table_name = %s
                    ORDER BY ordinal_position
                """, (schema, table))
                columns = cur.fetchall()
                
                # Get total row count
                from psycopg import sql
                count_query = sql.SQL("SELECT COUNT(*) FROM {}.{}").format(
                    sql.Identifier(schema),
                    sql.Identifier(table)
                )
                cur.execute(count_query)
                total_rows = cur.fetchone()[0]
                
                column_profiles = {}
                
                for col_name, data_type, is_nullable in columns:
                    profile = {
                        "data_type": data_type,
                        "nullable": is_nullable == "YES"
                    }
                    
                    # Get null count and null fraction
                    try:
                        null_query = sql.SQL("""
                            SELECT 
                                COUNT(*) - COUNT({col}) as null_count,
                                CASE WHEN COUNT(*) > 0 
                                     THEN (COUNT(*) - COUNT({col}))::float / COUNT(*) 
                                     ELSE 0 
                                END as null_fraction
                            FROM {schema}.{table}
                        """).format(
                            col=sql.Identifier(col_name),
                            schema=sql.Identifier(schema),
                            table=sql.Identifier(table)
                        )
                        cur.execute(null_query)
                        null_count, null_fraction = cur.fetchone()
                        profile['null_count'] = null_count
                        profile['null_fraction'] = round(float(null_fraction), 4) if null_fraction else 0.0
                    except:
                        profile['null_count'] = None
                        profile['null_fraction'] = None
                    
                    # Get distinct count (approximate)
                    try:
                        distinct_query = sql.SQL("""
                            SELECT COUNT(DISTINCT {col})
                            FROM {schema}.{table}
                        """).format(
                            col=sql.Identifier(col_name),
                            schema=sql.Identifier(schema),
                            table=sql.Identifier(table)
                        )
                        cur.execute(distinct_query)
                        profile['approx_distinct_count'] = cur.fetchone()[0]
                    except:
                        profile['approx_distinct_count'] = None
                    
                    # Numeric column statistics
                    if data_type in ('integer', 'bigint', 'smallint', 'numeric', 'decimal', 'real', 'double precision', 'money'):
                        try:
                            stats_query = sql.SQL("""
                                SELECT 
                                    MIN({col}),
                                    MAX({col}),
                                    AVG({col})
                                FROM {schema}.{table}
                                WHERE {col} IS NOT NULL
                            """).format(
                                col=sql.Identifier(col_name),
                                schema=sql.Identifier(schema),
                                table=sql.Identifier(table)
                            )
                            cur.execute(stats_query)
                            min_val, max_val, avg_val = cur.fetchone()
                            profile['min'] = float(min_val) if min_val is not None else None
                            profile['max'] = float(max_val) if max_val is not None else None
                            profile['avg'] = float(avg_val) if avg_val is not None else None
                        except:
                            pass
                    
                    # Categorical/text column - get top values
                    if data_type in ('character varying', 'varchar', 'char', 'character', 'text', 'bpchar'):
                        try:
                            # Only get top values if distinct count is reasonable
                            if profile.get('approx_distinct_count', 0) <= max_distinct * 2:
                                topk_query = sql.SQL("""
                                    SELECT {col}, COUNT(*) as count
                                    FROM {schema}.{table}
                                    WHERE {col} IS NOT NULL
                                    GROUP BY {col}
                                    ORDER BY count DESC
                                    LIMIT %s
                                """).format(
                                    col=sql.Identifier(col_name),
                                    schema=sql.Identifier(schema),
                                    table=sql.Identifier(table)
                                )
                                cur.execute(topk_query, (max_distinct,))
                                top_values = [{"value": str(row[0]), "count": row[1]} for row in cur.fetchall()]
                                profile['top_values'] = top_values
                        except:
                            pass
                    
                    column_profiles[col_name] = profile
                
                return {
                    "schema": schema,
                    "table": table,
                    "total_rows": total_rows,
                    "column_profiles": column_profiles
                }

