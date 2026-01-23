"""Add lineage tracking and audit log for process discovery.

This migration adds:
1. Purpose/justification fields to banked items
2. Added reason/by fields to dataset items
3. Audit log table for tracking all actions
4. Lineage links table for fast graph traversal

Enables full transparency - no black boxes in the distillation pipeline.

Revision ID: 023_add_lineage_tracking
Revises: 022_add_phase_2
Create Date: 2026-01-11
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = '023_add_lineage_tracking'
down_revision = '022_add_phase_2'
branch_labels = None
depends_on = None


def upgrade():
    # Add lineage fields to distillation_banked
    op.add_column('distillation_banked', 
        sa.Column('purpose', sa.String(100), nullable=True))
    op.add_column('distillation_banked', 
        sa.Column('business_justification', sa.Text, nullable=True))
    op.add_column('distillation_banked', 
        sa.Column('intended_use', sa.String(255), nullable=True))
    op.add_column('distillation_banked', 
        sa.Column('source_context', sa.Text, nullable=True))
    
    # Add lineage fields to distillation_dataset_items
    op.add_column('distillation_dataset_items', 
        sa.Column('added_reason', sa.Text, nullable=True))
    op.add_column('distillation_dataset_items', 
        sa.Column('added_by', sa.String(100), nullable=True))
    
    # Create audit log table
    op.create_table(
        'distillation_audit_log',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('entity_type', sa.String(50), nullable=False),
        sa.Column('entity_id', UUID(as_uuid=True), nullable=False),
        sa.Column('action', sa.String(50), nullable=False),
        sa.Column('actor', sa.String(100), nullable=True),
        sa.Column('actor_type', sa.String(20), server_default='user'),
        sa.Column('details', JSONB, server_default='{}'),
        sa.Column('source_entity_type', sa.String(50), nullable=True),
        sa.Column('source_entity_id', UUID(as_uuid=True), nullable=True),
        sa.Column('target_entity_type', sa.String(50), nullable=True),
        sa.Column('target_entity_id', UUID(as_uuid=True), nullable=True),
        sa.Column('model_provider', sa.String(50), nullable=True),
        sa.Column('model_name', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('NOW()'))
    )
    
    # Create lineage links table
    op.create_table(
        'distillation_lineage_links',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('source_type', sa.String(50), nullable=False),
        sa.Column('source_id', UUID(as_uuid=True), nullable=False),
        sa.Column('target_type', sa.String(50), nullable=False),
        sa.Column('target_id', UUID(as_uuid=True), nullable=False),
        sa.Column('link_type', sa.String(50), nullable=False),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('NOW()'))
    )
    
    # Create indexes for efficient lineage queries
    op.create_index('idx_audit_log_entity', 'distillation_audit_log', ['entity_type', 'entity_id'])
    op.create_index('idx_audit_log_action', 'distillation_audit_log', ['action'])
    op.create_index('idx_audit_log_created_at', 'distillation_audit_log', ['created_at'])
    op.create_index('idx_audit_log_model', 'distillation_audit_log', ['model_provider', 'model_name'])
    
    op.create_index('idx_lineage_source', 'distillation_lineage_links', ['source_type', 'source_id'])
    op.create_index('idx_lineage_target', 'distillation_lineage_links', ['target_type', 'target_id'])
    op.create_index('idx_lineage_link_type', 'distillation_lineage_links', ['link_type'])
    
    # Index for purpose filtering on banked items
    op.create_index('idx_banked_purpose', 'distillation_banked', ['purpose'])


def downgrade():
    # Drop indexes
    op.drop_index('idx_banked_purpose')
    op.drop_index('idx_lineage_link_type')
    op.drop_index('idx_lineage_target')
    op.drop_index('idx_lineage_source')
    op.drop_index('idx_audit_log_model')
    op.drop_index('idx_audit_log_created_at')
    op.drop_index('idx_audit_log_action')
    op.drop_index('idx_audit_log_entity')
    
    # Drop tables
    op.drop_table('distillation_lineage_links')
    op.drop_table('distillation_audit_log')
    
    # Remove columns from distillation_dataset_items
    op.drop_column('distillation_dataset_items', 'added_by')
    op.drop_column('distillation_dataset_items', 'added_reason')
    
    # Remove columns from distillation_banked
    op.drop_column('distillation_banked', 'source_context')
    op.drop_column('distillation_banked', 'intended_use')
    op.drop_column('distillation_banked', 'business_justification')
    op.drop_column('distillation_banked', 'purpose')
