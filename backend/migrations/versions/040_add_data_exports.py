"""Add data_exports table for tracking query exports to S3.

Revision ID: 040_add_data_exports
Revises: 039_add_tabdit_models
Create Date: 2026-01-25
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON, TIMESTAMP

# revision identifiers
revision = '040_add_data_exports'
down_revision = '039_add_tabdit_models'
branch_labels = None
depends_on = None


def upgrade():
    # Data exports tracking table
    op.create_table(
        'data_exports',
        sa.Column('id', UUID, primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=True),

        # Source
        sa.Column('source_type', sa.String(32), nullable=False),  # 'query' or 'table'
        sa.Column('source_query', sa.Text, nullable=True),  # SQL query if source_type='query'
        sa.Column('source_schema', sa.String(128), nullable=True),  # Schema if source_type='table'
        sa.Column('source_table', sa.String(128), nullable=True),  # Table if source_type='table'
        sa.Column('connection_id', sa.String(64), nullable=True),  # Database connection used

        # Destination
        sa.Column('destination_uri', sa.String(500), nullable=True),  # s3://bucket/path/file.parquet
        sa.Column('destination_format', sa.String(32), server_default='parquet'),  # parquet, csv
        sa.Column('destination_options', JSON, server_default='{}'),  # compression, partitioning, etc.

        # Status
        sa.Column('status', sa.String(32), server_default='pending'),  # pending, running, completed, failed
        sa.Column('progress', sa.Integer, server_default='0'),  # 0-100

        # Results
        sa.Column('row_count', sa.BigInteger, nullable=True),
        sa.Column('file_size_bytes', sa.BigInteger, nullable=True),
        sa.Column('column_count', sa.Integer, nullable=True),
        sa.Column('columns', JSON, nullable=True),  # Column metadata

        # Timing
        sa.Column('started_at', TIMESTAMP(timezone=True), nullable=True),
        sa.Column('completed_at', TIMESTAMP(timezone=True), nullable=True),
        sa.Column('duration_seconds', sa.Numeric(10, 2), nullable=True),

        # Error handling
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('error_details', JSON, nullable=True),

        # Audit
        sa.Column('created_by', sa.String(100), nullable=True),
        sa.Column('conversation_id', UUID, nullable=True),  # Link to chat conversation
        sa.Column('created_at', TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )

    # Indexes
    op.create_index('ix_data_exports_status', 'data_exports', ['status'])
    op.create_index('ix_data_exports_created_at', 'data_exports', ['created_at'])
    op.create_index('ix_data_exports_created_by', 'data_exports', ['created_by'])
    op.create_index('ix_data_exports_conversation_id', 'data_exports', ['conversation_id'])


def downgrade():
    op.drop_index('ix_data_exports_conversation_id')
    op.drop_index('ix_data_exports_created_by')
    op.drop_index('ix_data_exports_created_at')
    op.drop_index('ix_data_exports_status')
    op.drop_table('data_exports')
