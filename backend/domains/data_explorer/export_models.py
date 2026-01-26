"""Database models for data exports."""
from sqlalchemy import Table, Column, String, Text, Integer, BigInteger, Numeric, TIMESTAMP, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.sql import func

from db.models import METADATA


# Data exports tracking table
data_exports = Table(
    "data_exports",
    METADATA,
    Column("id", UUID, primary_key=True),
    Column("name", String(255), nullable=False),
    Column("description", Text, nullable=True),

    # Source
    Column("source_type", String(32), nullable=False),  # 'query' or 'table'
    Column("source_query", Text, nullable=True),
    Column("source_schema", String(128), nullable=True),
    Column("source_table", String(128), nullable=True),
    Column("connection_id", String(64), nullable=True),

    # Destination
    Column("destination_uri", String(500), nullable=True),
    Column("destination_format", String(32), server_default="parquet"),
    Column("destination_options", JSON, server_default="{}"),

    # Status
    Column("status", String(32), server_default="pending"),
    Column("progress", Integer, server_default="0"),

    # Results
    Column("row_count", BigInteger, nullable=True),
    Column("file_size_bytes", BigInteger, nullable=True),
    Column("column_count", Integer, nullable=True),
    Column("columns", JSON, nullable=True),

    # Timing
    Column("started_at", TIMESTAMP(timezone=True), nullable=True),
    Column("completed_at", TIMESTAMP(timezone=True), nullable=True),
    Column("duration_seconds", Numeric(10, 2), nullable=True),

    # Error handling
    Column("error_message", Text, nullable=True),
    Column("error_details", JSON, nullable=True),

    # Audit
    Column("created_by", String(100), nullable=True),
    Column("conversation_id", UUID, nullable=True),
    Column("created_at", TIMESTAMP(timezone=True), server_default=func.now()),
    Column("updated_at", TIMESTAMP(timezone=True), server_default=func.now()),
)
