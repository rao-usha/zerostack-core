"""Add ML Model Development tables for recipes, models, runs, and monitoring.

Revision ID: 009_ml_development
Revises: 008_dictionary
Create Date: 2025-12-14

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '009_ml_development'
down_revision = '008_dictionary'
branch_labels = None
depends_on = None


def upgrade():
    """Create ML model development tables."""
    
    # ml_recipe table
    op.create_table(
        'ml_recipe',
        sa.Column('id', sa.String(length=255), nullable=False),
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('model_family', sa.String(length=64), nullable=False),
        sa.Column('level', sa.String(length=32), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='draft'),
        sa.Column('parent_id', sa.String(length=255), nullable=True),
        sa.Column('tags', postgresql.JSON(astext_type=sa.Text()), nullable=False, server_default='[]'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_ml_recipe_model_family', 'ml_recipe', ['model_family'])
    op.create_index('ix_ml_recipe_level', 'ml_recipe', ['level'])
    op.create_index('ix_ml_recipe_status', 'ml_recipe', ['status'])
    
    # ml_recipe_version table
    op.create_table(
        'ml_recipe_version',
        sa.Column('version_id', sa.String(length=255), nullable=False),
        sa.Column('recipe_id', sa.String(length=255), nullable=False),
        sa.Column('version_number', sa.String(length=64), nullable=False),
        sa.Column('manifest_json', postgresql.JSON(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('diff_from_prev', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_by', sa.Text(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('change_note', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('version_id'),
        sa.ForeignKeyConstraint(['recipe_id'], ['ml_recipe.id'], ondelete='CASCADE')
    )
    op.create_index('ix_ml_recipe_version_recipe_id', 'ml_recipe_version', ['recipe_id'])
    
    # ml_model table
    op.create_table(
        'ml_model',
        sa.Column('id', sa.String(length=255), nullable=False),
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('model_family', sa.String(length=64), nullable=False),
        sa.Column('recipe_id', sa.String(length=255), nullable=False),
        sa.Column('recipe_version_id', sa.String(length=255), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='draft'),
        sa.Column('owner', sa.Text(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['recipe_id'], ['ml_recipe.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['recipe_version_id'], ['ml_recipe_version.version_id'], ondelete='CASCADE')
    )
    op.create_index('ix_ml_model_model_family', 'ml_model', ['model_family'])
    op.create_index('ix_ml_model_status', 'ml_model', ['status'])
    
    # ml_run table
    op.create_table(
        'ml_run',
        sa.Column('id', sa.String(length=255), nullable=False),
        sa.Column('model_id', sa.String(length=255), nullable=True),
        sa.Column('recipe_id', sa.String(length=255), nullable=False),
        sa.Column('recipe_version_id', sa.String(length=255), nullable=False),
        sa.Column('run_type', sa.String(length=32), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='queued'),
        sa.Column('started_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('finished_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('metrics_json', postgresql.JSON(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('artifacts_json', postgresql.JSON(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('logs_text', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['model_id'], ['ml_model.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['recipe_id'], ['ml_recipe.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['recipe_version_id'], ['ml_recipe_version.version_id'], ondelete='CASCADE')
    )
    op.create_index('ix_ml_run_status', 'ml_run', ['status'])
    op.create_index('ix_ml_run_run_type', 'ml_run', ['run_type'])
    
    # ml_monitor_snapshot table
    op.create_table(
        'ml_monitor_snapshot',
        sa.Column('id', sa.String(length=255), nullable=False),
        sa.Column('model_id', sa.String(length=255), nullable=False),
        sa.Column('captured_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('performance_metrics_json', postgresql.JSON(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('drift_metrics_json', postgresql.JSON(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('data_freshness_json', postgresql.JSON(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('alerts_json', postgresql.JSON(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['model_id'], ['ml_model.id'], ondelete='CASCADE')
    )
    op.create_index('ix_ml_monitor_snapshot_model_id', 'ml_monitor_snapshot', ['model_id'])
    op.create_index('ix_ml_monitor_snapshot_captured_at', 'ml_monitor_snapshot', ['captured_at'])
    
    # ml_synthetic_example table
    op.create_table(
        'ml_synthetic_example',
        sa.Column('id', sa.String(length=255), nullable=False),
        sa.Column('recipe_id', sa.String(length=255), nullable=False),
        sa.Column('dataset_schema_json', postgresql.JSON(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('sample_rows_json', postgresql.JSON(astext_type=sa.Text()), nullable=False, server_default='[]'),
        sa.Column('example_run_json', postgresql.JSON(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['recipe_id'], ['ml_recipe.id'], ondelete='CASCADE')
    )
    op.create_index('ix_ml_synthetic_example_recipe_id', 'ml_synthetic_example', ['recipe_id'])


def downgrade():
    """Drop ML model development tables."""
    
    op.drop_index('ix_ml_synthetic_example_recipe_id', table_name='ml_synthetic_example')
    op.drop_table('ml_synthetic_example')
    
    op.drop_index('ix_ml_monitor_snapshot_captured_at', table_name='ml_monitor_snapshot')
    op.drop_index('ix_ml_monitor_snapshot_model_id', table_name='ml_monitor_snapshot')
    op.drop_table('ml_monitor_snapshot')
    
    op.drop_index('ix_ml_run_run_type', table_name='ml_run')
    op.drop_index('ix_ml_run_status', table_name='ml_run')
    op.drop_table('ml_run')
    
    op.drop_index('ix_ml_model_status', table_name='ml_model')
    op.drop_index('ix_ml_model_model_family', table_name='ml_model')
    op.drop_table('ml_model')
    
    op.drop_index('ix_ml_recipe_version_recipe_id', table_name='ml_recipe_version')
    op.drop_table('ml_recipe_version')
    
    op.drop_index('ix_ml_recipe_status', table_name='ml_recipe')
    op.drop_index('ix_ml_recipe_level', table_name='ml_recipe')
    op.drop_index('ix_ml_recipe_model_family', table_name='ml_recipe')
    op.drop_table('ml_recipe')


