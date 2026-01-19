"""Add synthetic data generation tables.

Revision ID: 027_add_synthetic_data
Revises: 026_add_notebooks
Create Date: 2026-01-15
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON, TIMESTAMP

# revision identifiers
revision = '027_add_synthetic_data'
down_revision = '026_add_notebooks'
branch_labels = None
depends_on = None


def upgrade():
    # Synthetic generation jobs
    op.create_table(
        'synthetic_jobs',
        sa.Column('id', UUID, primary_key=True),
        
        # Source
        sa.Column('source_dataset_id', UUID, nullable=True),
        sa.Column('source_table_ref', sa.String(255), nullable=True),
        sa.Column('source_connection_id', UUID, sa.ForeignKey('data_connections.id', ondelete='SET NULL'), nullable=True),
        
        # Config
        sa.Column('synthesizer_type', sa.String(50), nullable=False),
        sa.Column('config', JSON, server_default='{}'),
        sa.Column('privacy_config', JSON, server_default='{}'),
        sa.Column('column_configs', JSON, server_default='{}'),
        
        # Request
        sa.Column('num_rows_requested', sa.Integer, nullable=False),
        sa.Column('random_seed', sa.Integer, nullable=True),
        
        # Status
        sa.Column('status', sa.String(32), nullable=False, server_default='pending'),
        sa.Column('progress', sa.Integer, server_default='0'),
        sa.Column('status_message', sa.Text, nullable=True),
        
        # Results
        sa.Column('num_rows_generated', sa.Integer, nullable=True),
        sa.Column('synthetic_dataset_id', UUID, nullable=True),
        sa.Column('quality_report_id', UUID, nullable=True),
        
        # Timing
        sa.Column('started_at', TIMESTAMP(timezone=True), nullable=True),
        sa.Column('completed_at', TIMESTAMP(timezone=True), nullable=True),
        sa.Column('duration_seconds', sa.Numeric(10, 2), nullable=True),
        
        # Errors
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('error_details', JSON, nullable=True),
        
        # Metadata
        sa.Column('created_by', sa.String(100)),
        sa.Column('created_at', TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )
    
    # Synthetic datasets (output)
    op.create_table(
        'synthetic_datasets',
        sa.Column('id', UUID, primary_key=True),
        sa.Column('job_id', UUID, sa.ForeignKey('synthetic_jobs.id', ondelete='CASCADE'), nullable=False),
        
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        
        sa.Column('storage_uri', sa.String(500), nullable=True),
        sa.Column('storage_format', sa.String(32), server_default='parquet'),
        
        sa.Column('num_rows', sa.Integer, nullable=False),
        sa.Column('num_columns', sa.Integer, nullable=False),
        sa.Column('file_size_bytes', sa.Integer, nullable=True),
        sa.Column('columns', JSON, nullable=True),
        
        sa.Column('created_at', TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )
    
    # Quality reports
    op.create_table(
        'synthetic_quality_reports',
        sa.Column('id', UUID, primary_key=True),
        sa.Column('synthetic_dataset_id', UUID, sa.ForeignKey('synthetic_datasets.id', ondelete='CASCADE'), nullable=False),
        sa.Column('job_id', UUID, sa.ForeignKey('synthetic_jobs.id', ondelete='CASCADE'), nullable=False),
        
        sa.Column('overall_score', sa.Numeric(4, 3), nullable=True),
        sa.Column('statistical_fidelity_score', sa.Numeric(4, 3), nullable=True),
        sa.Column('correlation_score', sa.Numeric(4, 3), nullable=True),
        sa.Column('privacy_score', sa.Numeric(4, 3), nullable=True),
        
        sa.Column('column_scores', JSON, nullable=True),
        sa.Column('statistical_metrics', JSON, nullable=True),
        sa.Column('correlation_metrics', JSON, nullable=True),
        sa.Column('privacy_metrics', JSON, nullable=True),
        
        sa.Column('recommendations', JSON, nullable=True),
        sa.Column('warnings', JSON, nullable=True),
        
        sa.Column('created_at', TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )
    
    # Column configs
    op.create_table(
        'synthetic_column_configs',
        sa.Column('id', UUID, primary_key=True),
        sa.Column('job_id', UUID, sa.ForeignKey('synthetic_jobs.id', ondelete='CASCADE'), nullable=False),
        
        sa.Column('column_name', sa.String(255), nullable=False),
        sa.Column('column_dtype', sa.String(50), nullable=True),
        
        sa.Column('is_pii', sa.Integer, server_default='0'),
        sa.Column('pii_type', sa.String(50), nullable=True),
        sa.Column('faker_provider', sa.String(100), nullable=True),
        
        sa.Column('constraints', JSON, server_default='{}'),
        sa.Column('sdtype', sa.String(50), nullable=True),
        
        sa.Column('created_at', TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )
    
    # Indexes
    op.create_index('ix_synthetic_jobs_status', 'synthetic_jobs', ['status'])
    op.create_index('ix_synthetic_jobs_created_at', 'synthetic_jobs', ['created_at'])
    op.create_index('ix_synthetic_datasets_job_id', 'synthetic_datasets', ['job_id'])
    op.create_index('ix_synthetic_datasets_name', 'synthetic_datasets', ['name'])
    op.create_index('ix_synthetic_quality_reports_dataset', 'synthetic_quality_reports', ['synthetic_dataset_id'])


def downgrade():
    op.drop_table('synthetic_column_configs')
    op.drop_table('synthetic_quality_reports')
    op.drop_table('synthetic_datasets')
    op.drop_table('synthetic_jobs')
