"""Add Files domain tables

Revision ID: 017_add_files_domain
Revises: 016_add_response_quality_rating
Create Date: 2026-01-05
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
import uuid

# revision identifiers
revision = '017_add_files_domain'
down_revision = '016_add_response_quality_rating'
branch_labels = None
depends_on = None


def upgrade():
    # Create file_locations table
    op.create_table(
        'file_locations',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('name', sa.String(), nullable=False, index=True),
        sa.Column('type', sa.String(), nullable=False, default='local'),
        sa.Column('local_path', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('last_scanned_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    
    # Create file_assets table
    op.create_table(
        'file_assets',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('location_id', UUID(as_uuid=True), sa.ForeignKey('file_locations.id'), nullable=False, index=True),
        sa.Column('provider_file_id', sa.String(), nullable=True),
        sa.Column('relative_path', sa.String(), nullable=False, index=True),
        sa.Column('file_name', sa.String(), nullable=False),
        sa.Column('ext', sa.String(), nullable=False),
        sa.Column('mime_type', sa.String(), nullable=True),
        sa.Column('last_seen_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    
    # Create file_versions table
    op.create_table(
        'file_versions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('file_asset_id', UUID(as_uuid=True), sa.ForeignKey('file_assets.id'), nullable=False, index=True),
        sa.Column('detected_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('modified_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('size_bytes', sa.BigInteger(), nullable=False),
        sa.Column('content_hash', sa.String(), nullable=False, index=True),
        sa.Column('row_count_estimate', sa.Integer(), nullable=True),
    )
    
    # Create file_tables table
    op.create_table(
        'file_tables',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('file_version_id', UUID(as_uuid=True), sa.ForeignKey('file_versions.id'), nullable=False, index=True),
        sa.Column('table_name', sa.String(), nullable=False),
        sa.Column('row_count', sa.Integer(), nullable=False, default=0),
        sa.Column('column_count', sa.Integer(), nullable=False, default=0),
        sa.Column('schema_json', sa.Text(), nullable=False),
        sa.Column('sample_data_json', sa.Text(), nullable=True),
        sa.Column('is_published', sa.Boolean(), nullable=False, default=False),
        sa.Column('published_dataset_id', UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )


def downgrade():
    op.drop_table('file_tables')
    op.drop_table('file_versions')
    op.drop_table('file_assets')
    op.drop_table('file_locations')
