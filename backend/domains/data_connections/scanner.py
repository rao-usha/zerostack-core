"""Data scanner service for discovering and analyzing data sources."""
import logging
import time
from datetime import datetime
from typing import Optional, List, Tuple, Any
from uuid import UUID, uuid4

import asyncpg
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from core.encryption import decrypt_password
from .db_models import data_connections, table_scans, recipe_compatibility
from .models import (
    ColumnScan, QualityIssue, TableScanSummary, TableScanDetail,
    ConnectionScanResponse, TableScanResponse, ScanStatus
)

logger = logging.getLogger(__name__)


class DataScanner:
    """
    Scans data sources to discover tables, columns, and data quality.
    
    Supports:
    - PostgreSQL (primary)
    - MySQL (planned)
    - Snowflake (planned)
    - S3/Files (planned)
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    # ========================================================================
    # CONNECTION TESTING
    # ========================================================================
    
    async def test_connection(self, connection_id: UUID) -> Tuple[bool, Optional[str]]:
        """
        Test if a connection is working.
        
        Returns:
            (success, error_message)
        """
        # Get connection details
        stmt = select(data_connections).where(data_connections.c.id == connection_id)
        result = await self.session.execute(stmt)
        conn = result.fetchone()
        
        if not conn:
            return False, "Connection not found"
        
        conn_type = conn.connection_type
        
        try:
            if conn_type == "postgresql":
                success, error = await self._test_postgres(conn)
            else:
                return False, f"Unsupported connection type: {conn_type}"
            
            # Update connection status
            await self.session.execute(
                update(data_connections)
                .where(data_connections.c.id == connection_id)
                .values(
                    status="connected" if success else "failed",
                    last_connected_at=datetime.utcnow() if success else None,
                    last_error=error
                )
            )
            await self.session.commit()
            
            return success, error
            
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            await self.session.execute(
                update(data_connections)
                .where(data_connections.c.id == connection_id)
                .values(status="failed", last_error=str(e))
            )
            await self.session.commit()
            return False, str(e)
    
    async def _test_postgres(self, conn) -> Tuple[bool, Optional[str]]:
        """Test PostgreSQL connection."""
        try:
            pg_conn = await asyncpg.connect(
                host=conn.host,
                port=conn.port or 5432,
                database=conn.database,
                user=conn.username,
                password=decrypt_password(conn.password_encrypted),
                timeout=10
            )
            await pg_conn.execute("SELECT 1")
            await pg_conn.close()
            return True, None
        except Exception as e:
            return False, str(e)
    
    # ========================================================================
    # FULL CONNECTION SCAN
    # ========================================================================
    
    async def scan_connection(
        self, 
        connection_id: UUID,
        full_scan: bool = False,
        sample_size: int = 1000
    ) -> ConnectionScanResponse:
        """
        Scan all tables in a connection.
        
        Args:
            connection_id: Connection to scan
            full_scan: If True, deeply analyze all columns
            sample_size: Number of rows to sample per table
            
        Returns:
            Scan results summary
        """
        start_time = time.time()
        
        # Get connection
        stmt = select(data_connections).where(data_connections.c.id == connection_id)
        result = await self.session.execute(stmt)
        conn = result.fetchone()
        
        if not conn:
            raise ValueError(f"Connection {connection_id} not found")
        
        # Update status
        await self.session.execute(
            update(data_connections)
            .where(data_connections.c.id == connection_id)
            .values(scan_status="scanning")
        )
        await self.session.commit()
        
        try:
            if conn.connection_type == "postgresql":
                tables = await self._scan_postgres_connection(conn, full_scan, sample_size)
            else:
                raise ValueError(f"Unsupported connection type: {conn.connection_type}")
            
            # Calculate totals
            total_rows = sum(t.row_count or 0 for t in tables)
            
            # Update connection
            await self.session.execute(
                update(data_connections)
                .where(data_connections.c.id == connection_id)
                .values(
                    scan_status="completed",
                    last_scan_at=datetime.utcnow(),
                    tables_count=len(tables),
                    total_rows=total_rows,
                    status="connected"
                )
            )
            await self.session.commit()
            
            duration = time.time() - start_time
            
            return ConnectionScanResponse(
                connection_id=connection_id,
                tables_found=len(tables),
                tables_scanned=len(tables),
                total_rows=total_rows,
                scan_duration_seconds=round(duration, 2),
                tables=tables
            )
            
        except Exception as e:
            logger.error(f"Scan failed for connection {connection_id}: {e}")
            await self.session.execute(
                update(data_connections)
                .where(data_connections.c.id == connection_id)
                .values(scan_status="failed", last_error=str(e))
            )
            await self.session.commit()
            raise
    
    async def _scan_postgres_connection(
        self, 
        conn, 
        full_scan: bool,
        sample_size: int
    ) -> List[TableScanSummary]:
        """Scan all tables in a PostgreSQL database."""
        pg_conn = await asyncpg.connect(
            host=conn.host,
            port=conn.port or 5432,
            database=conn.database,
            user=conn.username,
            password=decrypt_password(conn.password_encrypted),
            timeout=30
        )
        
        try:
            # Get all tables
            tables_query = """
                SELECT 
                    table_schema,
                    table_name,
                    pg_total_relation_size(quote_ident(table_schema) || '.' || quote_ident(table_name)) as size_bytes
                FROM information_schema.tables
                WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
                  AND table_type = 'BASE TABLE'
                ORDER BY table_schema, table_name
            """
            tables = await pg_conn.fetch(tables_query)
            
            results = []
            
            for table in tables:
                schema = table['table_schema']
                name = table['table_name']
                full_name = f"{schema}.{name}"
                
                try:
                    # Get row count
                    count_result = await pg_conn.fetchval(
                        f'SELECT COUNT(*) FROM "{schema}"."{name}"'
                    )
                    
                    # Get columns
                    columns_query = """
                        SELECT column_name, data_type, is_nullable
                        FROM information_schema.columns
                        WHERE table_schema = $1 AND table_name = $2
                        ORDER BY ordinal_position
                    """
                    columns = await pg_conn.fetch(columns_query, schema, name)
                    
                    # Detect date column
                    date_col = None
                    date_min = None
                    date_max = None
                    date_span = None
                    
                    for col in columns:
                        if col['data_type'] in ('date', 'timestamp', 'timestamp with time zone', 'timestamp without time zone'):
                            date_col = col['column_name']
                            try:
                                range_query = f'''
                                    SELECT MIN("{date_col}"), MAX("{date_col}")
                                    FROM "{schema}"."{name}"
                                    WHERE "{date_col}" IS NOT NULL
                                '''
                                range_result = await pg_conn.fetchrow(range_query)
                                if range_result and range_result[0]:
                                    date_min = range_result[0]
                                    date_max = range_result[1]
                                    if date_min and date_max:
                                        date_span = (date_max - date_min).days
                            except:
                                pass
                            break
                    
                    # Calculate completeness (rough estimate based on null counts)
                    completeness = 1.0
                    if full_scan and count_result > 0:
                        null_counts = []
                        for col in columns[:10]:  # Limit to first 10 columns
                            col_name = col['column_name']
                            try:
                                null_count = await pg_conn.fetchval(
                                    f'SELECT COUNT(*) FROM "{schema}"."{name}" WHERE "{col_name}" IS NULL'
                                )
                                null_counts.append(1 - (null_count / count_result))
                            except:
                                null_counts.append(1.0)
                        if null_counts:
                            completeness = sum(null_counts) / len(null_counts)
                    
                    # Store scan result
                    scan_id = uuid4()
                    await self.session.execute(
                        table_scans.insert().values(
                            id=scan_id,
                            connection_id=conn.id,
                            schema_name=schema,
                            table_name=name,
                            full_name=full_name,
                            row_count=count_result,
                            column_count=len(columns),
                            size_bytes=table['size_bytes'],
                            date_column=date_col,
                            date_min=date_min,
                            date_max=date_max,
                            date_span_days=date_span,
                            completeness_score=completeness,
                            columns=[{
                                'name': c['column_name'],
                                'data_type': c['data_type'],
                                'nullable': c['is_nullable'] == 'YES'
                            } for c in columns]
                        )
                    )
                    
                    results.append(TableScanSummary(
                        id=scan_id,
                        connection_id=conn.id,
                        schema_name=schema,
                        table_name=name,
                        full_name=full_name,
                        row_count=count_result,
                        column_count=len(columns),
                        date_column=date_col,
                        date_span_days=date_span,
                        completeness_score=completeness,
                        scanned_at=datetime.utcnow()
                    ))
                    
                except Exception as e:
                    logger.warning(f"Failed to scan table {full_name}: {e}")
                    continue
            
            await self.session.commit()
            return results
            
        finally:
            await pg_conn.close()
    
    # ========================================================================
    # SINGLE TABLE SCAN
    # ========================================================================
    
    async def scan_table(
        self,
        connection_id: UUID,
        table_name: str,
        sample_size: int = 1000,
        include_sample: bool = True
    ) -> TableScanResponse:
        """
        Deep scan a single table with full column analysis.
        
        Args:
            connection_id: Connection ID
            table_name: Full table name (schema.table)
            sample_size: Rows to sample
            include_sample: Include sample rows in response
            
        Returns:
            Detailed table scan
        """
        start_time = time.time()
        
        # Get connection
        stmt = select(data_connections).where(data_connections.c.id == connection_id)
        result = await self.session.execute(stmt)
        conn = result.fetchone()
        
        if not conn:
            raise ValueError(f"Connection {connection_id} not found")
        
        if conn.connection_type == "postgresql":
            detail = await self._deep_scan_postgres_table(
                conn, table_name, sample_size, include_sample
            )
        else:
            raise ValueError(f"Unsupported connection type: {conn.connection_type}")
        
        duration = time.time() - start_time
        
        return TableScanResponse(
            table=detail,
            scan_duration_seconds=round(duration, 2)
        )
    
    async def _deep_scan_postgres_table(
        self,
        conn,
        table_name: str,
        sample_size: int,
        include_sample: bool
    ) -> TableScanDetail:
        """Deep scan a PostgreSQL table."""
        # Parse schema.table
        parts = table_name.split('.')
        if len(parts) == 2:
            schema, name = parts
        else:
            schema, name = 'public', table_name
        
        pg_conn = await asyncpg.connect(
            host=conn.host,
            port=conn.port or 5432,
            database=conn.database,
            user=conn.username,
            password=decrypt_password(conn.password_encrypted),
            timeout=30
        )
        
        try:
            # Get row count
            row_count = await pg_conn.fetchval(
                f'SELECT COUNT(*) FROM "{schema}"."{name}"'
            )
            
            # Get table size
            size_bytes = await pg_conn.fetchval(
                f"SELECT pg_total_relation_size('{schema}.{name}')"
            )
            
            # Get columns with detailed analysis
            columns_query = """
                SELECT column_name, data_type, is_nullable, character_maximum_length
                FROM information_schema.columns
                WHERE table_schema = $1 AND table_name = $2
                ORDER BY ordinal_position
            """
            columns_raw = await pg_conn.fetch(columns_query, schema, name)
            
            columns: List[ColumnScan] = []
            quality_issues: List[QualityIssue] = []
            date_column = None
            date_min = None
            date_max = None
            
            for col in columns_raw:
                col_name = col['column_name']
                col_type = col['data_type']
                nullable = col['is_nullable'] == 'YES'
                
                # Determine type category
                is_date = col_type in ('date', 'timestamp', 'timestamp with time zone', 'timestamp without time zone')
                is_numeric = col_type in ('integer', 'bigint', 'smallint', 'decimal', 'numeric', 'real', 'double precision')
                is_boolean = col_type == 'boolean'
                is_text = col_type in ('text', 'character varying', 'varchar', 'char')
                
                # Get stats
                stats = await self._get_column_stats(pg_conn, schema, name, col_name, col_type, row_count)
                
                # Check for quality issues
                if stats['nulls_pct'] > 50:
                    quality_issues.append(QualityIssue(
                        severity="warning",
                        issue_type="high_nulls",
                        column=col_name,
                        message=f"Column {col_name} has {stats['nulls_pct']:.1f}% null values",
                        recommendation="Consider imputation or removal"
                    ))
                
                if is_numeric and stats.get('cardinality', 0) < 5 and row_count > 100:
                    quality_issues.append(QualityIssue(
                        severity="info",
                        issue_type="low_cardinality",
                        column=col_name,
                        message=f"Numeric column {col_name} has only {stats.get('cardinality', 0)} unique values",
                        recommendation="Consider treating as categorical"
                    ))
                
                # Track date column
                if is_date and not date_column:
                    date_column = col_name
                    date_min = stats.get('min_value')
                    date_max = stats.get('max_value')
                
                columns.append(ColumnScan(
                    name=col_name,
                    data_type=col_type,
                    nullable=nullable,
                    nulls_count=stats.get('nulls_count', 0),
                    nulls_pct=stats.get('nulls_pct', 0),
                    cardinality=stats.get('cardinality', 0),
                    min_value=stats.get('min_value'),
                    max_value=stats.get('max_value'),
                    mean_value=stats.get('mean_value'),
                    sample_values=stats.get('sample_values', []),
                    is_date=is_date,
                    is_numeric=is_numeric,
                    is_boolean=is_boolean,
                    is_text=is_text,
                    is_categorical=is_text and stats.get('cardinality', 0) < 100
                ))
            
            # Calculate date span
            date_span_days = None
            if date_min and date_max:
                try:
                    date_span_days = (date_max - date_min).days
                except:
                    pass
            
            # Get sample rows
            sample_rows = []
            if include_sample and row_count > 0:
                sample_query = f'SELECT * FROM "{schema}"."{name}" LIMIT {min(sample_size, 100)}'
                rows = await pg_conn.fetch(sample_query)
                sample_rows = [dict(r) for r in rows]
                # Convert non-serializable types
                for row in sample_rows:
                    for k, v in list(row.items()):
                        if v is None:
                            continue
                        elif isinstance(v, datetime):
                            row[k] = v.isoformat()
                        elif isinstance(v, (bytes, bytearray)):
                            row[k] = v.hex()
                        elif hasattr(v, 'isoformat'):  # Other date types
                            row[k] = str(v)
                        elif not isinstance(v, (str, int, float, bool)):
                            row[k] = str(v)
            
            # Calculate completeness
            total_nulls_pct = sum(c.nulls_pct for c in columns) / len(columns) if columns else 0
            completeness = 1 - (total_nulls_pct / 100)
            
            # Store/update scan
            scan_id = uuid4()
            
            # Delete old scan for this table
            await self.session.execute(
                delete(table_scans).where(
                    (table_scans.c.connection_id == conn.id) &
                    (table_scans.c.full_name == f"{schema}.{name}")
                )
            )
            
            # Serialize columns (convert datetime values)
            columns_json = []
            for c in columns:
                col_dict = c.model_dump()
                # Convert any datetime values in column stats
                if col_dict.get('min_value') and hasattr(col_dict['min_value'], 'isoformat'):
                    col_dict['min_value'] = col_dict['min_value'].isoformat()
                if col_dict.get('max_value') and hasattr(col_dict['max_value'], 'isoformat'):
                    col_dict['max_value'] = col_dict['max_value'].isoformat()
                # Convert sample values
                col_dict['sample_values'] = [
                    v.isoformat() if hasattr(v, 'isoformat') else str(v) if not isinstance(v, (str, int, float, bool, type(None))) else v
                    for v in col_dict.get('sample_values', [])
                ]
                columns_json.append(col_dict)
            
            # Insert new scan
            await self.session.execute(
                table_scans.insert().values(
                    id=scan_id,
                    connection_id=conn.id,
                    schema_name=schema,
                    table_name=name,
                    full_name=f"{schema}.{name}",
                    row_count=row_count,
                    column_count=len(columns),
                    size_bytes=size_bytes,
                    columns=columns_json,
                    date_column=date_column,
                    date_min=date_min,
                    date_max=date_max,
                    date_span_days=date_span_days,
                    completeness_score=completeness,
                    quality_issues=[q.model_dump() for q in quality_issues],
                    sample_rows=sample_rows[:20]  # Store max 20 sample rows
                )
            )
            await self.session.commit()
            
            return TableScanDetail(
                id=scan_id,
                connection_id=conn.id,
                schema_name=schema,
                table_name=name,
                full_name=f"{schema}.{name}",
                row_count=row_count,
                column_count=len(columns),
                size_bytes=size_bytes,
                columns=columns,
                date_column=date_column,
                date_min=date_min,
                date_max=date_max,
                date_span_days=date_span_days,
                completeness_score=completeness,
                quality_issues=quality_issues,
                sample_rows=sample_rows,
                scanned_at=datetime.utcnow()
            )
            
        finally:
            await pg_conn.close()
    
    async def _get_column_stats(
        self, 
        pg_conn, 
        schema: str, 
        table: str, 
        column: str, 
        col_type: str,
        total_rows: int
    ) -> dict:
        """Get statistics for a single column."""
        stats = {
            'nulls_count': 0,
            'nulls_pct': 0.0,
            'cardinality': 0,
            'sample_values': []
        }
        
        if total_rows == 0:
            return stats
        
        try:
            # Null count
            null_count = await pg_conn.fetchval(
                f'SELECT COUNT(*) FROM "{schema}"."{table}" WHERE "{column}" IS NULL'
            )
            stats['nulls_count'] = null_count
            stats['nulls_pct'] = (null_count / total_rows) * 100 if total_rows > 0 else 0
            
            # Cardinality
            cardinality = await pg_conn.fetchval(
                f'SELECT COUNT(DISTINCT "{column}") FROM "{schema}"."{table}"'
            )
            stats['cardinality'] = cardinality
            
            # Sample values
            sample_query = f'''
                SELECT DISTINCT "{column}" 
                FROM "{schema}"."{table}" 
                WHERE "{column}" IS NOT NULL 
                LIMIT 5
            '''
            samples = await pg_conn.fetch(sample_query)
            stats['sample_values'] = [str(s[column]) for s in samples]
            
            # Min/Max/Mean for numeric and date types
            is_numeric = col_type in ('integer', 'bigint', 'smallint', 'decimal', 'numeric', 'real', 'double precision')
            is_date = col_type in ('date', 'timestamp', 'timestamp with time zone', 'timestamp without time zone')
            
            if is_numeric:
                agg_query = f'''
                    SELECT MIN("{column}"), MAX("{column}"), AVG("{column}"::numeric)
                    FROM "{schema}"."{table}"
                '''
                agg = await pg_conn.fetchrow(agg_query)
                if agg:
                    stats['min_value'] = float(agg[0]) if agg[0] is not None else None
                    stats['max_value'] = float(agg[1]) if agg[1] is not None else None
                    stats['mean_value'] = float(agg[2]) if agg[2] is not None else None
            
            elif is_date:
                agg_query = f'''
                    SELECT MIN("{column}"), MAX("{column}")
                    FROM "{schema}"."{table}"
                '''
                agg = await pg_conn.fetchrow(agg_query)
                if agg:
                    stats['min_value'] = agg[0]
                    stats['max_value'] = agg[1]
                    
        except Exception as e:
            logger.warning(f"Failed to get stats for {schema}.{table}.{column}: {e}")
        
        return stats
    
    # ========================================================================
    # GET EXISTING SCANS
    # ========================================================================
    
    async def get_table_scans(self, connection_id: UUID) -> List[TableScanSummary]:
        """Get all table scans for a connection."""
        stmt = select(table_scans).where(
            table_scans.c.connection_id == connection_id
        ).order_by(table_scans.c.full_name)
        
        result = await self.session.execute(stmt)
        rows = result.fetchall()
        
        return [
            TableScanSummary(
                id=r.id,
                connection_id=r.connection_id,
                schema_name=r.schema_name,
                table_name=r.table_name,
                full_name=r.full_name,
                row_count=r.row_count,
                column_count=r.column_count,
                date_column=r.date_column,
                date_span_days=r.date_span_days,
                completeness_score=r.completeness_score,
                quality_issues=[QualityIssue(**q) for q in (r.quality_issues or [])],
                scanned_at=r.scanned_at
            )
            for r in rows
        ]
    
    async def get_table_scan_detail(self, scan_id: UUID) -> Optional[TableScanDetail]:
        """Get detailed scan for a specific table."""
        stmt = select(table_scans).where(table_scans.c.id == scan_id)
        result = await self.session.execute(stmt)
        r = result.fetchone()
        
        if not r:
            return None
        
        return TableScanDetail(
            id=r.id,
            connection_id=r.connection_id,
            schema_name=r.schema_name,
            table_name=r.table_name,
            full_name=r.full_name,
            row_count=r.row_count,
            column_count=r.column_count,
            size_bytes=r.size_bytes,
            columns=[ColumnScan(**c) for c in (r.columns or [])],
            date_column=r.date_column,
            date_min=r.date_min,
            date_max=r.date_max,
            date_span_days=r.date_span_days,
            completeness_score=r.completeness_score,
            quality_issues=[QualityIssue(**q) for q in (r.quality_issues or [])],
            sample_rows=r.sample_rows or [],
            scanned_at=r.scanned_at
        )
