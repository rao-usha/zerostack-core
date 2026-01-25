"""Add TabDiT models table for diffusion-based synthetic data generation.

Revision ID: 039_add_tabdit_models
Revises: 038_add_codat_tables
Create Date: 2026-01-25
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON, TIMESTAMP

# revision identifiers
revision = '039_add_tabdit_models'
down_revision = '038_add_codat_tables'
branch_labels = None
depends_on = None


def upgrade():
    # TabDiT models for diffusion-based synthetic data
    op.create_table(
        'tabdit_models',
        sa.Column('id', UUID, primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=True),

        # Source data
        sa.Column('source_dataset_id', UUID, nullable=True),
        sa.Column('source_table_ref', sa.String(255), nullable=True),

        # Configuration (JSON)
        sa.Column('vae_config', JSON, nullable=False, server_default='{}'),
        sa.Column('diffusion_config', JSON, nullable=False, server_default='{}'),
        sa.Column('tokenizer_config', JSON, server_default='{}'),

        # Status
        sa.Column('status', sa.String(32), server_default='pending'),  # pending/training_vae/training_diffusion/completed/failed
        sa.Column('current_phase', sa.String(32), nullable=True),

        # VAE training
        sa.Column('vae_run_id', sa.String(64), nullable=True),
        sa.Column('vae_checkpoint_uri', sa.String(500), nullable=True),
        sa.Column('vae_metrics', JSON, nullable=True),
        sa.Column('vae_epochs_completed', sa.Integer, server_default='0'),

        # Diffusion training
        sa.Column('diffusion_run_id', sa.String(64), nullable=True),
        sa.Column('diffusion_checkpoint_uri', sa.String(500), nullable=True),
        sa.Column('diffusion_metrics', JSON, nullable=True),
        sa.Column('diffusion_epochs_completed', sa.Integer, server_default='0'),

        # Quality
        sa.Column('overall_quality_score', sa.Numeric(4, 3), nullable=True),

        # Timing
        sa.Column('started_at', TIMESTAMP(timezone=True), nullable=True),
        sa.Column('completed_at', TIMESTAMP(timezone=True), nullable=True),

        # Metadata
        sa.Column('created_by', sa.String(100), nullable=True),
        sa.Column('created_at', TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )

    # Indexes
    op.create_index('ix_tabdit_models_status', 'tabdit_models', ['status'])
    op.create_index('ix_tabdit_models_name', 'tabdit_models', ['name'])
    op.create_index('ix_tabdit_models_created_at', 'tabdit_models', ['created_at'])


def downgrade():
    op.drop_index('ix_tabdit_models_created_at')
    op.drop_index('ix_tabdit_models_name')
    op.drop_index('ix_tabdit_models_status')
    op.drop_table('tabdit_models')
