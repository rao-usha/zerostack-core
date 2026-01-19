"""Add datasets tables for file uploads.

Revision ID: 028_add_datasets
Revises: 027_add_synthetic_data
Create Date: 2026-01-19
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '028_add_datasets'
down_revision = '027_add_synthetic_data'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create datasets table
    op.create_table(
        'datasets',
        sa.Column('id', postgresql.UUID(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),

        # Organization
        sa.Column('org_id', sa.String(100), server_default='default', nullable=True),
        sa.Column('tags', postgresql.JSON(), server_default='[]', nullable=True),

        # Source info
        sa.Column('source_type', sa.String(32), nullable=False),
        sa.Column('source_id', postgresql.UUID(), nullable=True),

        # Current version info
        sa.Column('current_version_id', postgresql.UUID(), nullable=True),
        sa.Column('current_version_number', sa.Integer(), server_default='0', nullable=True),

        # Storage
        sa.Column('storage_uri', sa.String(500), nullable=True),
        sa.Column('storage_format', sa.String(32), server_default='parquet', nullable=True),

        # Schema and stats
        sa.Column('schema', postgresql.JSON(), server_default='{}', nullable=True),
        sa.Column('row_count', sa.BigInteger(), nullable=True),
        sa.Column('column_count', sa.Integer(), nullable=True),
        sa.Column('size_bytes', sa.BigInteger(), nullable=True),

        # Status
        sa.Column('status', sa.String(32), server_default='active', nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),

        # Metadata
        sa.Column('created_by', sa.String(100), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),

        sa.PrimaryKeyConstraint('id')
    )

    # Create dataset_versions table
    op.create_table(
        'dataset_versions',
        sa.Column('id', postgresql.UUID(), nullable=False),
        sa.Column('dataset_id', postgresql.UUID(), nullable=False),

        # Version info
        sa.Column('version_number', sa.Integer(), nullable=False),
        sa.Column('sha256', sa.String(64), nullable=False),

        # Storage
        sa.Column('storage_uri', sa.String(500), nullable=False),
        sa.Column('storage_format', sa.String(32), nullable=False),
        sa.Column('original_filename', sa.String(255), nullable=True),

        # Stats
        sa.Column('row_count', sa.BigInteger(), nullable=True),
        sa.Column('column_count', sa.Integer(), nullable=True),
        sa.Column('size_bytes', sa.BigInteger(), nullable=True),

        # Schema
        sa.Column('schema', postgresql.JSON(), server_default='{}', nullable=True),

        # Quality
        sa.Column('quality_profile', postgresql.JSON(), server_default='{}', nullable=True),

        # Metadata
        sa.Column('created_by', sa.String(100), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),

        sa.ForeignKeyConstraint(['dataset_id'], ['datasets.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes
    op.create_index('idx_datasets_org_id', 'datasets', ['org_id'])
    op.create_index('idx_datasets_status', 'datasets', ['status'])
    op.create_index('idx_datasets_source_type', 'datasets', ['source_type'])
    op.create_index('idx_dataset_versions_dataset_id', 'dataset_versions', ['dataset_id'])
    op.create_index('idx_dataset_versions_sha256', 'dataset_versions', ['sha256'])


def downgrade() -> None:
    op.drop_index('idx_dataset_versions_sha256', 'dataset_versions')
    op.drop_index('idx_dataset_versions_dataset_id', 'dataset_versions')
    op.drop_index('idx_datasets_source_type', 'datasets')
    op.drop_index('idx_datasets_status', 'datasets')
    op.drop_index('idx_datasets_org_id', 'datasets')
    op.drop_table('dataset_versions')
    op.drop_table('datasets')
