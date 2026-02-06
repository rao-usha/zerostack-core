"""Database models for governance: policies, approvals, and audit logs."""
from sqlalchemy import Table, Column, ForeignKey, Index, Integer, String, JSON, Text, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from db.meta import METADATA


# Governance policies
policies = Table(
    "governance_policies",
    METADATA,
    Column("id", UUID, primary_key=True),
    Column("name", String(255), nullable=False),
    Column("description", Text),
    Column("policy_type", String(64), nullable=False),  # data_access, data_usage, quality, privacy, retention
    Column("status", String(32), nullable=False, server_default="draft"),  # draft, active, archived

    # Policy rules (JSON schema defining conditions)
    Column("rules", JSON, server_default="{}"),
    # Example rules structure:
    # {
    #   "conditions": [{"field": "classification", "operator": "eq", "value": "pii"}],
    #   "actions": ["require_approval", "log_access"],
    #   "applies_to": {"resource_types": ["dataset", "table"], "tags": ["sensitive"]}
    # }

    # Metadata
    Column("metadata", JSON, server_default="{}"),
    Column("org_id", UUID),
    Column("created_by", UUID),
    Column("created_at", TIMESTAMP(timezone=True), server_default=func.now()),
    Column("updated_at", TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now()),

    Index("ix_governance_policies_type", "policy_type"),
    Index("ix_governance_policies_status", "status"),
    Index("ix_governance_policies_org_id", "org_id"),
)


# Approval requests for data access/operations
approvals = Table(
    "governance_approvals",
    METADATA,
    Column("id", UUID, primary_key=True),
    Column("resource_type", String(64), nullable=False),  # dataset, model, table, persona, etc.
    Column("resource_id", UUID, nullable=False),
    Column("action", String(64), nullable=False),  # create, update, delete, access, export

    # Request details
    Column("requested_by", UUID, nullable=False),
    Column("reason", Text),
    Column("metadata", JSON, server_default="{}"),  # Additional context

    # Policy reference (if triggered by a policy)
    Column("triggered_by_policy_id", UUID, ForeignKey("governance_policies.id", ondelete="SET NULL")),

    # Review state
    Column("status", String(32), nullable=False, server_default="pending"),  # pending, approved, rejected, cancelled
    Column("approver", UUID),
    Column("review_reason", Text),  # Reason for approval/rejection
    Column("reviewed_at", TIMESTAMP(timezone=True)),

    # Auto-expiration
    Column("expires_at", TIMESTAMP(timezone=True)),

    # Timestamps
    Column("created_at", TIMESTAMP(timezone=True), server_default=func.now()),

    Index("ix_governance_approvals_status", "status"),
    Index("ix_governance_approvals_requested_by", "requested_by"),
    Index("ix_governance_approvals_resource", "resource_type", "resource_id"),
)


# Audit log - immutable record of all actions
audit_logs = Table(
    "governance_audit_logs",
    METADATA,
    Column("id", UUID, primary_key=True),
    Column("user_id", UUID),
    Column("action", String(128), nullable=False),  # e.g., "dataset.create", "model.access", "policy.update"
    Column("resource_type", String(64)),
    Column("resource_id", UUID),
    Column("resource_name", String(255)),  # Denormalized for readability

    # Request context
    Column("ip_address", String(45)),  # IPv6 compatible
    Column("user_agent", Text),
    Column("session_id", String(128)),

    # Details (JSON for flexibility)
    Column("details", JSON, server_default="{}"),
    # Example: {"old_value": {...}, "new_value": {...}, "query": "SELECT...", "rows_affected": 100}

    # Outcome
    Column("status", String(32), server_default="success"),  # success, failure, denied
    Column("error_message", Text),

    # Compliance tags
    Column("compliance_tags", JSON, server_default="[]"),  # ["gdpr", "hipaa", "pii_access"]

    # Timestamp (immutable)
    Column("created_at", TIMESTAMP(timezone=True), server_default=func.now()),

    Index("ix_governance_audit_logs_user_id", "user_id"),
    Index("ix_governance_audit_logs_action", "action"),
    Index("ix_governance_audit_logs_resource", "resource_type", "resource_id"),
    Index("ix_governance_audit_logs_created_at", "created_at"),
)


# Data classifications (for tagging datasets/columns)
data_classifications = Table(
    "governance_data_classifications",
    METADATA,
    Column("id", UUID, primary_key=True),
    Column("resource_type", String(64), nullable=False),  # dataset, table, column
    Column("resource_id", UUID, nullable=False),
    Column("resource_path", String(512)),  # e.g., "schema.table.column" for column-level

    # Classification
    Column("classification", String(64), nullable=False),  # public, internal, confidential, restricted, pii
    Column("sub_classification", String(64)),  # email, ssn, financial, health, etc.

    # Compliance tags
    Column("compliance_tags", JSON, server_default="[]"),  # ["gdpr_personal", "hipaa_phi", "ccpa_sensitive"]

    # Retention
    Column("retention_days", Integer),  # How long to keep
    Column("retention_policy_id", UUID, ForeignKey("governance_policies.id", ondelete="SET NULL")),

    # Metadata
    Column("classified_by", UUID),
    Column("notes", Text),
    Column("created_at", TIMESTAMP(timezone=True), server_default=func.now()),
    Column("updated_at", TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now()),

    Index("ix_governance_classifications_resource", "resource_type", "resource_id"),
    Index("ix_governance_classifications_classification", "classification"),
)
