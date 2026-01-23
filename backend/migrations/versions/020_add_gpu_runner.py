"""Add GPU Runner support to ml_development

Revision ID: 020_add_gpu_runner
Revises: 019_add_batch_generation
Create Date: 2026-01-06

This migration:
1. Extends ml_recipe with container execution fields
2. Extends ml_run with remote compute execution fields
3. Creates highlighted_datasets domain tables
4. Creates ml_derived_assets table for results banking
5. Creates interaction_logs table for audit trail
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY

# revision identifiers, used by Alembic.
revision = '020_add_gpu_runner'
down_revision = '019_add_batch_generation'
branch_labels = None
depends_on = None


def upgrade():
    # ========================================
    # 1. Extend ml_recipe with container support
    # ========================================
    op.add_column('ml_recipe', sa.Column('container_image', sa.String(500), nullable=True))
    op.add_column('ml_recipe', sa.Column('container_entrypoint', ARRAY(sa.String), nullable=True))
    op.add_column('ml_recipe', sa.Column('default_compute_target', sa.String(50), nullable=True, server_default='local'))
    op.add_column('ml_recipe', sa.Column('gpu_required', sa.Boolean(), nullable=False, server_default='false'))
    
    # ========================================
    # 2. Extend ml_run with remote execution support
    # ========================================
    op.add_column('ml_run', sa.Column('compute_target', sa.String(50), nullable=True, server_default='local'))
    op.add_column('ml_run', sa.Column('remote_job_id', sa.String(255), nullable=True))
    op.add_column('ml_run', sa.Column('input_dataset_version_id', UUID(as_uuid=True), nullable=True))
    op.add_column('ml_run', sa.Column('parameters', JSONB, nullable=False, server_default='{}'))
    op.add_column('ml_run', sa.Column('logs_uri', sa.String(500), nullable=True))
    op.add_column('ml_run', sa.Column('output_manifest_uri', sa.String(500), nullable=True))
    op.add_column('ml_run', sa.Column('status_reason', sa.Text(), nullable=True))
    op.add_column('ml_run', sa.Column('created_by', sa.String(100), nullable=True))
    op.add_column('ml_run', sa.Column('chat_session_id', sa.String(100), nullable=True))
    
    # Add indexes for polling active runs
    op.create_index('ix_ml_run_compute_status', 'ml_run', ['compute_target', 'status'])
    op.create_index('ix_ml_run_remote_job', 'ml_run', ['remote_job_id'])
    
    # ========================================
    # 3. NEW: Highlighted Datasets Domain
    # ========================================
    
    op.create_table(
        'highlighted_datasets',
        sa.Column('id', sa.String(100), primary_key=True),
        sa.Column('display_name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('tags', ARRAY(sa.String), nullable=False, server_default='{}'),
        sa.Column('source_type', sa.String(50), nullable=False),  # manual_upload, http_download, kaggle
        sa.Column('default_location_uri', sa.String(500), nullable=True),
        sa.Column('availability_state', sa.String(30), nullable=False, server_default='NOT_PRESENT'),
        sa.Column('resolver_config', JSONB, nullable=False, server_default='{}'),
        sa.Column('license_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )
    
    op.create_table(
        'highlighted_dataset_versions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('highlighted_dataset_id', sa.String(100), 
                  sa.ForeignKey('highlighted_datasets.id', ondelete='CASCADE'), nullable=False),
        sa.Column('version_label', sa.String(64), nullable=False),
        sa.Column('manifest_uri', sa.String(500), nullable=False),
        sa.Column('storage_uri', sa.String(500), nullable=False),
        sa.Column('file_count', sa.Integer(), nullable=True),
        sa.Column('total_bytes', sa.BigInteger(), nullable=True),
        sa.Column('schema_json', JSONB, nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('created_by', sa.String(100), nullable=True),
        sa.UniqueConstraint('highlighted_dataset_id', 'version_label', name='uq_highlighted_dataset_version'),
    )
    
    op.create_index('ix_highlighted_datasets_state', 'highlighted_datasets', ['availability_state'])
    op.create_index('ix_highlighted_dataset_versions_dataset', 'highlighted_dataset_versions', ['highlighted_dataset_id'])
    
    # Add FK from ml_run to highlighted_dataset_versions
    op.create_foreign_key(
        'fk_ml_run_input_dataset',
        'ml_run', 'highlighted_dataset_versions',
        ['input_dataset_version_id'], ['id'],
        ondelete='SET NULL'
    )
    
    # ========================================
    # 4. NEW: ML Derived Assets (Results Banking)
    # ========================================
    
    op.create_table(
        'ml_derived_assets',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('source_run_id', sa.String(255), 
                  sa.ForeignKey('ml_run.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(255), nullable=True),
        sa.Column('asset_type', sa.String(20), nullable=False, server_default='temporal'),
        sa.Column('storage_uri', sa.String(500), nullable=False),
        sa.Column('manifest_uri', sa.String(500), nullable=False),
        sa.Column('ttl_expires_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('schema_json', JSONB, nullable=True),
        sa.Column('metrics_json', JSONB, nullable=False, server_default='{}'),
        sa.Column('tags', ARRAY(sa.String), nullable=False, server_default='{}'),
        sa.Column('approval_state', sa.String(20), nullable=False, server_default='draft'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('created_by', sa.String(100), nullable=True),
        sa.Column('promoted_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('promoted_by', sa.String(100), nullable=True),
    )
    
    op.create_index('ix_ml_derived_assets_type', 'ml_derived_assets', ['asset_type'])
    op.create_index('ix_ml_derived_assets_ttl', 'ml_derived_assets', ['ttl_expires_at'])
    op.create_index('ix_ml_derived_assets_run', 'ml_derived_assets', ['source_run_id'])
    op.create_index('ix_ml_derived_assets_approval', 'ml_derived_assets', ['approval_state'])
    
    # ========================================
    # 5. NEW: Interaction Logs (Audit Trail)
    # ========================================
    
    op.create_table(
        'interaction_logs',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('chat_session_id', sa.String(100), nullable=True),
        sa.Column('actor', sa.String(50), nullable=False),  # user, assistant, system
        sa.Column('event_type', sa.String(50), nullable=False),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('refs', JSONB, nullable=False, server_default='{}'),
        sa.Column('metadata', JSONB, nullable=False, server_default='{}'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )
    
    # Event types:
    # - CHAT_MESSAGE: User or assistant chat message
    # - DATASET_RESOLVE: Resolved a highlighted dataset
    # - INGEST_START: Started dataset ingestion
    # - INGEST_COMPLETE: Completed dataset ingestion
    # - RUN_SUBMITTED: Submitted a model run
    # - RUN_STARTED: Remote job started
    # - RUN_COMPLETED: Run succeeded
    # - RUN_FAILED: Run failed
    # - ASSET_CREATED: Derived asset auto-created
    # - ASSET_PROMOTED: Asset promoted to permanent
    # - VIEW_STATUS: User viewed run status
    # - VIEW_LOGS: User viewed run logs
    
    op.create_index('ix_interaction_logs_session', 'interaction_logs', ['chat_session_id'])
    op.create_index('ix_interaction_logs_event', 'interaction_logs', ['event_type'])
    op.create_index('ix_interaction_logs_created', 'interaction_logs', ['created_at'])


def downgrade():
    # Drop interaction_logs
    op.drop_index('ix_interaction_logs_created', 'interaction_logs')
    op.drop_index('ix_interaction_logs_event', 'interaction_logs')
    op.drop_index('ix_interaction_logs_session', 'interaction_logs')
    op.drop_table('interaction_logs')
    
    # Drop ml_derived_assets
    op.drop_index('ix_ml_derived_assets_approval', 'ml_derived_assets')
    op.drop_index('ix_ml_derived_assets_run', 'ml_derived_assets')
    op.drop_index('ix_ml_derived_assets_ttl', 'ml_derived_assets')
    op.drop_index('ix_ml_derived_assets_type', 'ml_derived_assets')
    op.drop_table('ml_derived_assets')
    
    # Drop FK from ml_run
    op.drop_constraint('fk_ml_run_input_dataset', 'ml_run', type_='foreignkey')
    
    # Drop highlighted_dataset_versions
    op.drop_index('ix_highlighted_dataset_versions_dataset', 'highlighted_dataset_versions')
    op.drop_table('highlighted_dataset_versions')
    
    # Drop highlighted_datasets
    op.drop_index('ix_highlighted_datasets_state', 'highlighted_datasets')
    op.drop_table('highlighted_datasets')
    
    # Remove indexes from ml_run
    op.drop_index('ix_ml_run_remote_job', 'ml_run')
    op.drop_index('ix_ml_run_compute_status', 'ml_run')
    
    # Remove columns from ml_run
    op.drop_column('ml_run', 'chat_session_id')
    op.drop_column('ml_run', 'created_by')
    op.drop_column('ml_run', 'status_reason')
    op.drop_column('ml_run', 'output_manifest_uri')
    op.drop_column('ml_run', 'logs_uri')
    op.drop_column('ml_run', 'parameters')
    op.drop_column('ml_run', 'input_dataset_version_id')
    op.drop_column('ml_run', 'remote_job_id')
    op.drop_column('ml_run', 'compute_target')
    
    # Remove columns from ml_recipe
    op.drop_column('ml_recipe', 'gpu_required')
    op.drop_column('ml_recipe', 'default_compute_target')
    op.drop_column('ml_recipe', 'container_entrypoint')
    op.drop_column('ml_recipe', 'container_image')
