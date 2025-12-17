"""add evaluation packs

Revision ID: 010_add_evaluation_packs
Revises: 297d473edc6b
Create Date: 2025-12-16

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON, UUID

# revision identifiers, used by Alembic.
revision = '010_add_evaluation_packs'
down_revision = '297d473edc6b'
branch_labels = None
depends_on = None


def upgrade():
    # Create evaluation_pack table
    op.create_table(
        'evaluation_pack',
        sa.Column('id', sa.String(255), primary_key=True),
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('model_family', sa.String(64), nullable=False),
        sa.Column('status', sa.String(32), nullable=False, server_default='draft'),
        sa.Column('tags', JSON, nullable=False, server_default='[]'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    # Create evaluation_pack_version table
    op.create_table(
        'evaluation_pack_version',
        sa.Column('version_id', sa.String(255), primary_key=True),
        sa.Column('pack_id', sa.String(255), sa.ForeignKey('evaluation_pack.id'), nullable=False),
        sa.Column('version_number', sa.String(64), nullable=False),
        sa.Column('pack_json', JSON, nullable=False, server_default='{}'),
        sa.Column('diff_from_prev', JSON, nullable=True),
        sa.Column('created_by', sa.String(255), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('change_note', sa.Text(), nullable=True),
    )
    
    # Create recipe_evaluation_pack join table
    op.create_table(
        'recipe_evaluation_pack',
        sa.Column('recipe_id', sa.String(255), sa.ForeignKey('ml_recipe.id'), nullable=False),
        sa.Column('pack_id', sa.String(255), sa.ForeignKey('evaluation_pack.id'), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('recipe_id', 'pack_id'),
    )
    
    # Create evaluation_result table
    op.create_table(
        'evaluation_result',
        sa.Column('id', sa.String(255), primary_key=True),
        sa.Column('run_id', sa.String(255), sa.ForeignKey('ml_run.id'), nullable=False),
        sa.Column('pack_id', sa.String(255), sa.ForeignKey('evaluation_pack.id'), nullable=False),
        sa.Column('pack_version_id', sa.String(255), sa.ForeignKey('evaluation_pack_version.version_id'), nullable=False),
        sa.Column('executed_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('status', sa.String(32), nullable=False),
        sa.Column('results_json', JSON, nullable=False, server_default='{}'),
        sa.Column('summary_text', sa.Text(), nullable=True),
    )
    
    # Create monitor_evaluation_snapshot table
    op.create_table(
        'monitor_evaluation_snapshot',
        sa.Column('id', sa.String(255), primary_key=True),
        sa.Column('model_id', sa.String(255), sa.ForeignKey('ml_model.id'), nullable=False),
        sa.Column('captured_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('pack_id', sa.String(255), sa.ForeignKey('evaluation_pack.id'), nullable=False),
        sa.Column('pack_version_id', sa.String(255), sa.ForeignKey('evaluation_pack_version.version_id'), nullable=False),
        sa.Column('status', sa.String(32), nullable=False),
        sa.Column('results_json', JSON, nullable=False, server_default='{}'),
    )


def downgrade():
    op.drop_table('monitor_evaluation_snapshot')
    op.drop_table('evaluation_result')
    op.drop_table('recipe_evaluation_pack')
    op.drop_table('evaluation_pack_version')
    op.drop_table('evaluation_pack')

