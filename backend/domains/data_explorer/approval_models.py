"""Database models for approval requests."""
from sqlalchemy import Table, Column, String, Text, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.sql import func

from db.models import METADATA


# Approval requests tracking table
approval_requests = Table(
    "approval_requests",
    METADATA,
    Column("id", UUID, primary_key=True),

    # Request details
    Column("request_type", String(64), nullable=False),
    Column("title", String(255), nullable=False),
    Column("description", Text, nullable=True),

    # The operation to perform if approved
    Column("operation_type", String(64), nullable=False),
    Column("operation_params", JSON, nullable=False),
    Column("connection_id", String(64), server_default="default"),

    # Risk assessment
    Column("risk_level", String(16), server_default="medium"),
    Column("risk_reasons", JSON, server_default="[]"),

    # Status workflow
    Column("status", String(32), server_default="pending"),
    Column("decision_reason", Text, nullable=True),

    # People
    Column("requested_by", String(100), nullable=False),
    Column("decided_by", String(100), nullable=True),

    # Timing
    Column("expires_at", TIMESTAMP(timezone=True), nullable=False),
    Column("decided_at", TIMESTAMP(timezone=True), nullable=True),
    Column("executed_at", TIMESTAMP(timezone=True), nullable=True),

    # Result tracking
    Column("execution_result", JSON, nullable=True),
    Column("execution_error", Text, nullable=True),

    # Links
    Column("conversation_id", UUID, nullable=True),
    Column("result_resource_id", UUID, nullable=True),

    # Audit
    Column("created_at", TIMESTAMP(timezone=True), server_default=func.now()),
    Column("updated_at", TIMESTAMP(timezone=True), server_default=func.now()),
)
