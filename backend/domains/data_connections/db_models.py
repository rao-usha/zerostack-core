"""Database models for data connections and scans."""
from sqlalchemy import Table, Column, ForeignKey, Boolean, Integer, String, JSON, Text, TIMESTAMP, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from db.meta import METADATA


# Data connections (extends the existing connectors concept)
data_connections = Table(
    "data_connections",
    METADATA,
    Column("id", UUID, primary_key=True),
    Column("name", String(255), nullable=False),
    Column("description", Text),
    Column("connection_type", String(64), nullable=False),  # postgresql, mysql, snowflake, bigquery, s3, file
    
    # Connection config (encrypted in practice)
    Column("host", String(512)),
    Column("port", Integer),
    Column("database", String(255)),
    Column("username", String(255)),
    Column("password_encrypted", Text),  # encrypted password
    Column("extra_config", JSON, server_default="{}"),  # additional connection params
    
    # Status
    Column("status", String(32), nullable=False, server_default="pending"),  # pending, connected, failed, scanning
    Column("last_connected_at", TIMESTAMP(timezone=True)),
    Column("last_error", Text),
    
    # Scan state
    Column("last_scan_at", TIMESTAMP(timezone=True)),
    Column("scan_status", String(32), server_default="never"),  # never, scanning, completed, failed
    Column("tables_count", Integer, server_default="0"),
    Column("total_rows", Integer, server_default="0"),
    
    # Metadata
    Column("created_at", TIMESTAMP(timezone=True), server_default=func.now()),
    Column("updated_at", TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now()),
)


# Table-level scan results
table_scans = Table(
    "table_scans",
    METADATA,
    Column("id", UUID, primary_key=True),
    Column("connection_id", UUID, ForeignKey("data_connections.id", ondelete="CASCADE"), nullable=False),
    
    # Table identification
    Column("schema_name", String(255)),
    Column("table_name", String(255), nullable=False),
    Column("full_name", String(512), nullable=False),  # schema.table
    
    # Basic stats
    Column("row_count", Integer),
    Column("column_count", Integer),
    Column("size_bytes", Integer),
    
    # Column details (JSON array)
    Column("columns", JSON, server_default="[]"),
    # Each column: {name, type, nullable, nulls_pct, cardinality, min, max, mean, sample_values}
    
    # Time series detection
    Column("date_column", String(255)),  # Detected primary date column
    Column("date_min", TIMESTAMP(timezone=True)),
    Column("date_max", TIMESTAMP(timezone=True)),
    Column("date_span_days", Integer),
    
    # Quality metrics
    Column("completeness_score", Float),  # 0-1, how complete is the data
    Column("quality_issues", JSON, server_default="[]"),  # List of detected issues
    
    # Sample data
    Column("sample_rows", JSON, server_default="[]"),  # First N rows as JSON
    
    # Timestamps
    Column("scanned_at", TIMESTAMP(timezone=True), server_default=func.now()),
    Column("created_at", TIMESTAMP(timezone=True), server_default=func.now()),
)


# Recipe compatibility assessments
recipe_compatibility = Table(
    "recipe_compatibility",
    METADATA,
    Column("id", UUID, primary_key=True),
    Column("table_scan_id", UUID, ForeignKey("table_scans.id", ondelete="CASCADE"), nullable=False),
    Column("recipe_id", String(255), nullable=False),
    
    # Compatibility assessment
    Column("compatibility_score", Float),  # 0-100
    Column("status", String(32), nullable=False),  # ready, partial, incompatible
    
    # Requirements check
    Column("requirements_met", JSON, server_default="[]"),  # [{requirement, status, column, notes}]
    Column("requirements_missing", JSON, server_default="[]"),
    Column("requirements_partial", JSON, server_default="[]"),
    
    # Recommendations
    Column("recommendations", JSON, server_default="[]"),  # Suggested fixes
    
    Column("assessed_at", TIMESTAMP(timezone=True), server_default=func.now()),
)
