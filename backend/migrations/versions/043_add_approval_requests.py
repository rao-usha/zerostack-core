"""Add approval_requests table for tracking pending approvals.

Revision ID: 043_add_approval_requests
Revises: 042_add_managed_procedures
Create Date: 2026-01-25
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON, TIMESTAMP

# revision identifiers
revision = '043_add_approval_requests'
down_revision = '042_add_managed_procedures'
branch_labels = None
depends_on = None


def upgrade():
    # Approval requests tracking table
    op.create_table(
        'approval_requests',
        sa.Column('id', UUID, primary_key=True),

        # Request details
        sa.Column('request_type', sa.String(64), nullable=False),  # create_materialized_view, create_procedure, etc.
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=True),

        # The operation to perform if approved
        sa.Column('operation_type', sa.String(64), nullable=False),  # materialized_view, stored_procedure, export
        sa.Column('operation_params', JSON, nullable=False),  # Full parameters for the operation
        sa.Column('connection_id', sa.String(64), server_default='default'),

        # Risk assessment
        sa.Column('risk_level', sa.String(16), server_default='medium'),  # low, medium, high, critical
        sa.Column('risk_reasons', JSON, server_default='[]'),  # List of reasons for the risk level

        # Status workflow
        sa.Column('status', sa.String(32), server_default='pending'),  # pending, approved, rejected, expired, executed
        sa.Column('decision_reason', sa.Text, nullable=True),  # Reason for approval/rejection

        # People
        sa.Column('requested_by', sa.String(100), nullable=False),
        sa.Column('decided_by', sa.String(100), nullable=True),

        # Timing
        sa.Column('expires_at', TIMESTAMP(timezone=True), nullable=False),
        sa.Column('decided_at', TIMESTAMP(timezone=True), nullable=True),
        sa.Column('executed_at', TIMESTAMP(timezone=True), nullable=True),

        # Result tracking
        sa.Column('execution_result', JSON, nullable=True),  # Result of executing the operation
        sa.Column('execution_error', sa.Text, nullable=True),

        # Links
        sa.Column('conversation_id', UUID, nullable=True),
        sa.Column('result_resource_id', UUID, nullable=True),  # ID of created resource (view, procedure, etc.)

        # Audit
        sa.Column('created_at', TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )

    # Indexes
    op.create_index('ix_approval_req_status', 'approval_requests', ['status'])
    op.create_index('ix_approval_req_requested_by', 'approval_requests', ['requested_by'])
    op.create_index('ix_approval_req_decided_by', 'approval_requests', ['decided_by'])
    op.create_index('ix_approval_req_expires_at', 'approval_requests', ['expires_at'])
    op.create_index('ix_approval_req_request_type', 'approval_requests', ['request_type'])
    op.create_index('ix_approval_req_risk_level', 'approval_requests', ['risk_level'])


def downgrade():
    op.drop_index('ix_approval_req_risk_level')
    op.drop_index('ix_approval_req_request_type')
    op.drop_index('ix_approval_req_expires_at')
    op.drop_index('ix_approval_req_decided_by')
    op.drop_index('ix_approval_req_requested_by')
    op.drop_index('ix_approval_req_status')
    op.drop_table('approval_requests')
