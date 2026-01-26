"""Database models for managed materialized views."""
from sqlalchemy import Table, Column, String, Text, Integer, BigInteger, Boolean, TIMESTAMP, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.sql import func

from db.models import METADATA


# Managed materialized views tracking table
managed_materialized_views = Table(
    "managed_materialized_views",
    METADATA,
    Column("id", UUID, primary_key=True),
    Column("name", String(128), nullable=False),
    Column("schema_name", String(128), nullable=False, server_default="public"),
    Column("description", Text, nullable=True),

    # Source definition
    Column("source_query", Text, nullable=False),
    Column("connection_id", String(64), server_default="default"),

    # Configuration
    Column("with_data", Boolean, server_default="true"),
    Column("unique_indexes", JSON, server_default="[]"),
    Column("indexes", JSON, server_default="[]"),

    # Refresh settings
    Column("refresh_schedule", String(64), nullable=True),
    Column("refresh_concurrently", Boolean, server_default="true"),
    Column("last_refresh_at", TIMESTAMP(timezone=True), nullable=True),
    Column("last_refresh_duration_ms", Integer, nullable=True),
    Column("next_refresh_at", TIMESTAMP(timezone=True), nullable=True),

    # Status
    Column("status", String(32), server_default="active"),
    Column("row_count", BigInteger, nullable=True),
    Column("size_bytes", BigInteger, nullable=True),

    # Error handling
    Column("last_error", Text, nullable=True),
    Column("error_count", Integer, server_default="0"),

    # Audit
    Column("created_by", String(100), nullable=True),
    Column("conversation_id", UUID, nullable=True),
    Column("created_at", TIMESTAMP(timezone=True), server_default=func.now()),
    Column("updated_at", TIMESTAMP(timezone=True), server_default=func.now()),

    UniqueConstraint("schema_name", "name", name="uq_managed_mv_schema_name"),
)
