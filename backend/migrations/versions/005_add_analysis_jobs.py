"""Add analysis jobs table for async job queue

Revision ID: 005_jobs
Revises: 004_metadata
Create Date: 2024-11-30

Tables:
- analysis_jobs: Job queue and status tracking for async analyses
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB, TIMESTAMP

# revision identifiers, used by Alembic.
revision = '005_jobs'
down_revision = '004_metadata'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create analysis_jobs table
    op.create_table(
        'analysis_jobs',
        sa.Column('id', UUID, primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', UUID, nullable=True, comment='User who created the job'),
        sa.Column('name', sa.String(255), nullable=False, comment='User-provided job name'),
        sa.Column('description', sa.Text, nullable=True),
        
        # Job configuration
        sa.Column('tables', JSONB, nullable=False, comment='Tables to analyze'),
        sa.Column('analysis_types', sa.ARRAY(sa.String), nullable=False),
        sa.Column('provider', sa.String(50), nullable=False),
        sa.Column('model', sa.String(100), nullable=False),
        sa.Column('context', sa.Text, nullable=True, comment='Business context'),
        sa.Column('db_id', sa.String(100), nullable=False, server_default='default'),
        
        # Job status
        sa.Column('status', sa.String(50), nullable=False, server_default='pending',
                  comment='pending, running, completed, failed, cancelled'),
        sa.Column('progress', sa.Integer, nullable=False, server_default='0',
                  comment='Progress percentage 0-100'),
        sa.Column('current_stage', sa.String(255), nullable=True,
                  comment='Current processing stage description'),
        
        # Results
        sa.Column('result_id', UUID, nullable=True, 
                  comment='Foreign key to ai_analysis_results when completed'),
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('error_details', JSONB, nullable=True),
        
        # Timing
        sa.Column('created_at', TIMESTAMP(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('started_at', TIMESTAMP(timezone=True), nullable=True),
        sa.Column('completed_at', TIMESTAMP(timezone=True), nullable=True),
        sa.Column('cancelled_at', TIMESTAMP(timezone=True), nullable=True),
        
        # Metadata
        sa.Column('job_metadata', JSONB, nullable=True, comment='Additional job metadata'),
        sa.Column('tags', sa.ARRAY(sa.String), nullable=True),
    )
    
    # Create indexes
    op.create_index('ix_analysis_jobs_status', 'analysis_jobs', ['status'])
    op.create_index('ix_analysis_jobs_user_id', 'analysis_jobs', ['user_id'])
    op.create_index('ix_analysis_jobs_created_at', 'analysis_jobs', ['created_at'], postgresql_using='btree')
    op.create_index('ix_analysis_jobs_db_id', 'analysis_jobs', ['db_id'])
    # Composite index for user's active jobs
    op.create_index('ix_analysis_jobs_user_status', 'analysis_jobs', ['user_id', 'status'])
    # Index for result lookup
    op.create_index('ix_analysis_jobs_result_id', 'analysis_jobs', ['result_id'])
    
    # Add foreign key constraint to ai_analysis_results
    op.create_foreign_key(
        'fk_analysis_jobs_result',
        'analysis_jobs', 'ai_analysis_results',
        ['result_id'], ['id'],
        ondelete='SET NULL'
    )


def downgrade() -> None:
    # Drop foreign key
    op.drop_constraint('fk_analysis_jobs_result', 'analysis_jobs', type_='foreignkey')
    
    # Drop indexes
    op.drop_index('ix_analysis_jobs_result_id', table_name='analysis_jobs')
    op.drop_index('ix_analysis_jobs_user_status', table_name='analysis_jobs')
    op.drop_index('ix_analysis_jobs_db_id', table_name='analysis_jobs')
    op.drop_index('ix_analysis_jobs_created_at', table_name='analysis_jobs')
    op.drop_index('ix_analysis_jobs_user_id', table_name='analysis_jobs')
    op.drop_index('ix_analysis_jobs_status', table_name='analysis_jobs')
    
    # Drop table
    op.drop_table('analysis_jobs')

