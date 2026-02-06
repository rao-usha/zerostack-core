"""Add governance tables for policies, approvals, audit logs, and classifications.

Revision ID: 047_add_governance_tables
Revises: 046_add_query_workbench
Create Date: 2026-02-06
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB, TIMESTAMP

# revision identifiers
revision = '047_add_governance_tables'
down_revision = '046_add_query_workbench'
branch_labels = None
depends_on = None


def upgrade():
    # Governance policies
    op.create_table(
        'governance_policies',
        sa.Column('id', UUID, primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('policy_type', sa.String(64), nullable=False),  # data_access, data_usage, quality, privacy, retention
        sa.Column('status', sa.String(32), nullable=False, server_default='draft'),  # draft, active, archived
        sa.Column('rules', JSONB, server_default='{}'),
        sa.Column('metadata', JSONB, server_default='{}'),
        sa.Column('org_id', UUID),
        sa.Column('created_by', UUID),
        sa.Column('created_at', TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )

    op.create_index('ix_governance_policies_type', 'governance_policies', ['policy_type'])
    op.create_index('ix_governance_policies_status', 'governance_policies', ['status'])
    op.create_index('ix_governance_policies_org_id', 'governance_policies', ['org_id'])

    # Approval requests
    op.create_table(
        'governance_approvals',
        sa.Column('id', UUID, primary_key=True),
        sa.Column('resource_type', sa.String(64), nullable=False),
        sa.Column('resource_id', UUID, nullable=False),
        sa.Column('action', sa.String(64), nullable=False),
        sa.Column('requested_by', UUID, nullable=False),
        sa.Column('reason', sa.Text),
        sa.Column('metadata', JSONB, server_default='{}'),
        sa.Column('triggered_by_policy_id', UUID, sa.ForeignKey('governance_policies.id', ondelete='SET NULL')),
        sa.Column('status', sa.String(32), nullable=False, server_default='pending'),
        sa.Column('approver', UUID),
        sa.Column('review_reason', sa.Text),
        sa.Column('reviewed_at', TIMESTAMP(timezone=True)),
        sa.Column('expires_at', TIMESTAMP(timezone=True)),
        sa.Column('created_at', TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )

    op.create_index('ix_governance_approvals_status', 'governance_approvals', ['status'])
    op.create_index('ix_governance_approvals_requested_by', 'governance_approvals', ['requested_by'])
    op.create_index('ix_governance_approvals_resource', 'governance_approvals', ['resource_type', 'resource_id'])

    # Audit logs (immutable)
    op.create_table(
        'governance_audit_logs',
        sa.Column('id', UUID, primary_key=True),
        sa.Column('user_id', UUID),
        sa.Column('action', sa.String(128), nullable=False),
        sa.Column('resource_type', sa.String(64)),
        sa.Column('resource_id', UUID),
        sa.Column('resource_name', sa.String(255)),
        sa.Column('ip_address', sa.String(45)),  # IPv6 compatible
        sa.Column('user_agent', sa.Text),
        sa.Column('session_id', sa.String(128)),
        sa.Column('details', JSONB, server_default='{}'),
        sa.Column('status', sa.String(32), server_default='success'),
        sa.Column('error_message', sa.Text),
        sa.Column('compliance_tags', JSONB, server_default='[]'),
        sa.Column('created_at', TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )

    op.create_index('ix_governance_audit_logs_user_id', 'governance_audit_logs', ['user_id'])
    op.create_index('ix_governance_audit_logs_action', 'governance_audit_logs', ['action'])
    op.create_index('ix_governance_audit_logs_resource', 'governance_audit_logs', ['resource_type', 'resource_id'])
    op.create_index('ix_governance_audit_logs_created_at', 'governance_audit_logs', ['created_at'])

    # Data classifications
    op.create_table(
        'governance_data_classifications',
        sa.Column('id', UUID, primary_key=True),
        sa.Column('resource_type', sa.String(64), nullable=False),
        sa.Column('resource_id', UUID, nullable=False),
        sa.Column('resource_path', sa.String(512)),
        sa.Column('classification', sa.String(64), nullable=False),  # public, internal, confidential, restricted, pii
        sa.Column('sub_classification', sa.String(64)),
        sa.Column('compliance_tags', JSONB, server_default='[]'),
        sa.Column('retention_days', sa.Integer),
        sa.Column('retention_policy_id', UUID, sa.ForeignKey('governance_policies.id', ondelete='SET NULL')),
        sa.Column('classified_by', UUID),
        sa.Column('notes', sa.Text),
        sa.Column('created_at', TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )

    op.create_index('ix_governance_classifications_resource', 'governance_data_classifications', ['resource_type', 'resource_id'])
    op.create_index('ix_governance_classifications_classification', 'governance_data_classifications', ['classification'])


def downgrade():
    # Drop indexes first
    op.drop_index('ix_governance_classifications_classification')
    op.drop_index('ix_governance_classifications_resource')
    op.drop_table('governance_data_classifications')

    op.drop_index('ix_governance_audit_logs_created_at')
    op.drop_index('ix_governance_audit_logs_resource')
    op.drop_index('ix_governance_audit_logs_action')
    op.drop_index('ix_governance_audit_logs_user_id')
    op.drop_table('governance_audit_logs')

    op.drop_index('ix_governance_approvals_resource')
    op.drop_index('ix_governance_approvals_requested_by')
    op.drop_index('ix_governance_approvals_status')
    op.drop_table('governance_approvals')

    op.drop_index('ix_governance_policies_org_id')
    op.drop_index('ix_governance_policies_status')
    op.drop_index('ix_governance_policies_type')
    op.drop_table('governance_policies')
