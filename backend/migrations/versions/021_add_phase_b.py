"""Add Phase B: Cost tracking, reuse engine, retries, RunPod support

Revision ID: 021_add_phase_b
Revises: 020_add_gpu_runner
Create Date: 2026-01-07

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers
revision = '021_add_phase_b'
down_revision = '020_add_gpu_runner'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ========================================
    # 1. Extend ml_run with cost tracking
    # ========================================
    op.add_column('ml_run', sa.Column('estimated_cost_usd', sa.Numeric(10, 4), nullable=True))
    op.add_column('ml_run', sa.Column('actual_cost_usd', sa.Numeric(10, 4), nullable=True))
    op.add_column('ml_run', sa.Column('gpu_type', sa.String(100), nullable=True))
    op.add_column('ml_run', sa.Column('runtime_seconds', sa.Integer(), nullable=True))
    
    # ========================================
    # 2. Extend ml_run with reuse tracking
    # ========================================
    op.add_column('ml_run', sa.Column('similarity_hash', sa.String(64), nullable=True))
    op.add_column('ml_run', sa.Column('reused_from_run_id', sa.String(255), nullable=True))
    
    # Create index for similarity hash lookups
    op.create_index('ix_ml_run_similarity_hash', 'ml_run', ['similarity_hash'])
    
    # ========================================
    # 3. Extend ml_run with retry tracking
    # ========================================
    op.add_column('ml_run', sa.Column('retry_count', sa.Integer(), server_default='0', nullable=False))
    op.add_column('ml_run', sa.Column('max_retries', sa.Integer(), server_default='2', nullable=False))
    op.add_column('ml_run', sa.Column('failure_reason', sa.Text(), nullable=True))
    op.add_column('ml_run', sa.Column('failure_type', sa.String(50), nullable=True))  # 'infra' or 'model'
    
    # ========================================
    # 4. Extend ml_run with lineage
    # ========================================
    op.add_column('ml_run', sa.Column('parent_run_id', sa.String(255), nullable=True))
    
    # ========================================
    # 5. Extend ml_derived_assets
    # ========================================
    op.add_column('ml_derived_assets', sa.Column('confidence_score', sa.Numeric(5, 4), nullable=True))
    op.add_column('ml_derived_assets', sa.Column('replaced_by_asset_id', sa.UUID(), nullable=True))
    op.add_column('ml_derived_assets', sa.Column('version_number', sa.Integer(), server_default='1', nullable=False))
    
    # ========================================
    # 6. Create gpu_pricing table
    # ========================================
    op.create_table(
        'gpu_pricing',
        sa.Column('id', sa.String(100), primary_key=True),
        sa.Column('provider', sa.String(50), nullable=False),
        sa.Column('gpu_type', sa.String(100), nullable=False),
        sa.Column('hourly_rate_usd', sa.Numeric(10, 4), nullable=False),
        sa.Column('memory_gb', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now())
    )
    
    # ========================================
    # 7. Create run_schedules table (Phase 2, but create now)
    # ========================================
    op.create_table(
        'run_schedules',
        sa.Column('id', sa.UUID(), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('recipe_id', sa.String(255), nullable=False),
        sa.Column('dataset_id', sa.String(100), nullable=True),
        sa.Column('parameters', JSONB, server_default='{}'),
        sa.Column('cron_expression', sa.String(100), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('last_run_id', sa.String(255), nullable=True),
        sa.Column('last_run_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('next_run_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now())
    )
    
    # ========================================
    # 8. Seed default GPU pricing
    # ========================================
    op.execute("""
        INSERT INTO gpu_pricing (id, provider, gpu_type, hourly_rate_usd, memory_gb) VALUES
        ('local_any', 'local', 'any', 0.00, NULL),
        ('runpod_rtx_a4000', 'runpod', 'NVIDIA RTX A4000', 0.20, 16),
        ('runpod_rtx_a5000', 'runpod', 'NVIDIA RTX A5000', 0.30, 24),
        ('runpod_rtx_3090', 'runpod', 'NVIDIA RTX 3090', 0.22, 24),
        ('runpod_rtx_4090', 'runpod', 'NVIDIA RTX 4090', 0.44, 24),
        ('runpod_a40', 'runpod', 'NVIDIA A40', 0.39, 48),
        ('runpod_a100_40gb', 'runpod', 'NVIDIA A100 40GB', 1.09, 40),
        ('runpod_a100_80gb', 'runpod', 'NVIDIA A100 80GB', 1.69, 80),
        ('runpod_h100_80gb', 'runpod', 'NVIDIA H100 80GB', 2.69, 80)
        ON CONFLICT (id) DO NOTHING
    """)


def downgrade() -> None:
    # Drop tables
    op.drop_table('run_schedules')
    op.drop_table('gpu_pricing')
    
    # Drop ml_derived_assets columns
    op.drop_column('ml_derived_assets', 'version_number')
    op.drop_column('ml_derived_assets', 'replaced_by_asset_id')
    op.drop_column('ml_derived_assets', 'confidence_score')
    
    # Drop ml_run columns
    op.drop_index('ix_ml_run_similarity_hash', 'ml_run')
    op.drop_column('ml_run', 'parent_run_id')
    op.drop_column('ml_run', 'failure_type')
    op.drop_column('ml_run', 'failure_reason')
    op.drop_column('ml_run', 'max_retries')
    op.drop_column('ml_run', 'retry_count')
    op.drop_column('ml_run', 'reused_from_run_id')
    op.drop_column('ml_run', 'similarity_hash')
    op.drop_column('ml_run', 'runtime_seconds')
    op.drop_column('ml_run', 'gpu_type')
    op.drop_column('ml_run', 'actual_cost_usd')
    op.drop_column('ml_run', 'estimated_cost_usd')
