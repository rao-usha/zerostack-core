"""Add investor (FO/LP) data ingestion tables.

Revision ID: 037_add_investor_ingestion
Revises: 036_add_ingestion_tables
Create Date: 2026-01-23

Adds tables for FO/LP investor data ingestion:
- investor_ingestion_jobs: Track ingestion job status and results
- investor_mapping_templates: Saved field mapping templates for reuse
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB


# revision identifiers
revision = '037_add_investor_ingestion'
down_revision = '036_add_ingestion_tables'
branch_labels = None
depends_on = None


def upgrade():
    # Investor Ingestion Jobs - track FO/LP data ingestion
    op.create_table(
        'investor_ingestion_jobs',
        sa.Column('id', UUID, primary_key=True, server_default=sa.text('gen_random_uuid()')),

        # File info
        sa.Column('filename', sa.String(255), nullable=False),
        sa.Column('original_filename', sa.String(255), nullable=False),
        sa.Column('file_type', sa.String(100), nullable=False),
        sa.Column('file_size_bytes', sa.BigInteger, nullable=False),
        sa.Column('storage_path', sa.String(500), nullable=True),

        # Target
        sa.Column('target_entity', sa.String(50), nullable=False),
        sa.Column('parent_id', sa.Integer, nullable=True),

        # Mapping
        sa.Column('field_mappings', JSONB, nullable=True),

        # Status
        sa.Column('status', sa.String(50), nullable=False, server_default='pending'),
        sa.Column('error_message', sa.Text, nullable=True),

        # Row counts
        sa.Column('total_rows', sa.Integer, nullable=False, server_default='0'),
        sa.Column('rows_processed', sa.Integer, nullable=False, server_default='0'),
        sa.Column('rows_inserted', sa.Integer, nullable=False, server_default='0'),
        sa.Column('rows_updated', sa.Integer, nullable=False, server_default='0'),
        sa.Column('rows_failed', sa.Integer, nullable=False, server_default='0'),

        # Errors (stored as JSON array)
        sa.Column('errors', JSONB, nullable=True),

        # Options
        sa.Column('options', JSONB, nullable=True),

        # Audit
        sa.Column('created_by', sa.String(255), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('started_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('completed_at', sa.TIMESTAMP(timezone=True), nullable=True),
    )

    # Mapping Templates - saved field mapping templates
    op.create_table(
        'investor_mapping_templates',
        sa.Column('id', UUID, primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('target_entity', sa.String(50), nullable=False),
        sa.Column('field_mappings', JSONB, nullable=True),

        # Audit
        sa.Column('created_by', sa.String(255), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )

    # Indexes
    op.create_index('idx_investor_jobs_status', 'investor_ingestion_jobs', ['status'])
    op.create_index('idx_investor_jobs_entity', 'investor_ingestion_jobs', ['target_entity'])
    op.create_index('idx_investor_jobs_created', 'investor_ingestion_jobs', ['created_at'])

    op.create_index('idx_investor_templates_name', 'investor_mapping_templates', ['name'])
    op.create_index('idx_investor_templates_entity', 'investor_mapping_templates', ['target_entity'])


def downgrade():
    # Drop indexes
    op.drop_index('idx_investor_templates_entity')
    op.drop_index('idx_investor_templates_name')

    op.drop_index('idx_investor_jobs_created')
    op.drop_index('idx_investor_jobs_entity')
    op.drop_index('idx_investor_jobs_status')

    # Drop tables
    op.drop_table('investor_mapping_templates')
    op.drop_table('investor_ingestion_jobs')
