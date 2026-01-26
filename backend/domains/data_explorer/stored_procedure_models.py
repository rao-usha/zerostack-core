"""Database models for managed stored procedures."""
from sqlalchemy import Table, Column, String, Text, Integer, BigInteger, Boolean, TIMESTAMP, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.sql import func

from db.models import METADATA


# Managed stored procedures tracking table
managed_procedures = Table(
    "managed_procedures",
    METADATA,
    Column("id", UUID, primary_key=True),
    Column("name", String(128), nullable=False),
    Column("schema_name", String(128), nullable=False, server_default="public"),
    Column("description", Text, nullable=True),

    # Procedure definition
    Column("language", String(32), server_default="plpgsql"),
    Column("source_code", Text, nullable=False),
    Column("parameters", JSON, server_default="[]"),
    Column("return_type", String(128), nullable=True),
    Column("returns_set", Boolean, server_default="false"),

    # Security
    Column("security_definer", Boolean, server_default="false"),
    Column("allowed_roles", JSON, server_default="[]"),

    # Configuration
    Column("connection_id", String(64), server_default="default"),
    Column("volatility", String(16), server_default="volatile"),
    Column("parallel_safety", String(16), server_default="unsafe"),

    # Status
    Column("status", String(32), server_default="active"),

    # Execution stats
    Column("execution_count", BigInteger, server_default="0"),
    Column("last_executed_at", TIMESTAMP(timezone=True), nullable=True),
    Column("avg_execution_ms", Integer, nullable=True),

    # Error handling
    Column("last_error", Text, nullable=True),
    Column("error_count", Integer, server_default="0"),

    # Audit
    Column("created_by", String(100), nullable=True),
    Column("conversation_id", UUID, nullable=True),
    Column("created_at", TIMESTAMP(timezone=True), server_default=func.now()),
    Column("updated_at", TIMESTAMP(timezone=True), server_default=func.now()),

    UniqueConstraint("schema_name", "name", name="uq_managed_proc_schema_name"),
)
