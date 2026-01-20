"""Add feature store tables.

Revision ID: 030
Revises: 029
Create Date: 2026-01-19

Phase 1: Foundation - Core tables for feature store functionality.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB


# revision identifiers
revision = '030_add_feature_store'
down_revision = '029_add_app_settings'
branch_labels = None
depends_on = None


def upgrade():
    # Feature entities - business objects that features are computed for
    op.create_table(
        'feature_entities',
        sa.Column('id', UUID, primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(100), unique=True, nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('join_keys', JSONB, nullable=False),  # ["user_id"] or ["user_id", "product_id"]
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('created_by', sa.String(100)),
    )

    # Feature definitions - individual feature specifications with versioning
    op.create_table(
        'feature_definitions',
        sa.Column('id', UUID, primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('entity_id', UUID, sa.ForeignKey('feature_entities.id', ondelete='CASCADE')),
        sa.Column('version', sa.Integer, nullable=False, server_default='1'),

        # Data type
        sa.Column('dtype', sa.String(50), nullable=False),  # int64, float64, string, bool, datetime

        # Transformation
        sa.Column('transformation_type', sa.String(20), nullable=False),  # sql, python
        sa.Column('transformation_code', sa.Text, nullable=False),

        # Source (optional - for SQL transformations)
        sa.Column('source_table', sa.String(255)),

        # Metadata
        sa.Column('description', sa.Text),
        sa.Column('owner', sa.String(100)),
        sa.Column('tags', JSONB, server_default='[]'),

        # Computation settings
        sa.Column('computation_mode', sa.String(20), server_default='on_demand'),  # on_demand, scheduled
        sa.Column('refresh_schedule', sa.String(100)),  # cron expression
        sa.Column('ttl_seconds', sa.Integer),  # time-to-live for cached values

        # Status
        sa.Column('status', sa.String(20), server_default='draft'),  # draft, active, deprecated

        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),

        sa.UniqueConstraint('name', 'version', name='uq_feature_definitions_name_version'),
    )

    # Feature sets - groups of related features
    op.create_table(
        'feature_sets',
        sa.Column('id', UUID, primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(255), unique=True, nullable=False),
        sa.Column('entity_id', UUID, sa.ForeignKey('feature_entities.id', ondelete='SET NULL')),
        sa.Column('description', sa.Text),
        sa.Column('owner', sa.String(100)),
        sa.Column('tags', JSONB, server_default='[]'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )

    # Feature set membership - join table
    op.create_table(
        'feature_set_features',
        sa.Column('id', UUID, primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('feature_set_id', UUID, sa.ForeignKey('feature_sets.id', ondelete='CASCADE'), nullable=False),
        sa.Column('feature_definition_id', UUID, sa.ForeignKey('feature_definitions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('added_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),

        sa.UniqueConstraint('feature_set_id', 'feature_definition_id', name='uq_feature_set_features'),
    )

    # Create indexes for common queries
    op.create_index('idx_feature_definitions_entity', 'feature_definitions', ['entity_id'])
    op.create_index('idx_feature_definitions_status', 'feature_definitions', ['status'])
    op.create_index('idx_feature_definitions_name', 'feature_definitions', ['name'])
    op.create_index('idx_feature_sets_entity', 'feature_sets', ['entity_id'])


def downgrade():
    op.drop_index('idx_feature_sets_entity')
    op.drop_index('idx_feature_definitions_name')
    op.drop_index('idx_feature_definitions_status')
    op.drop_index('idx_feature_definitions_entity')
    op.drop_table('feature_set_features')
    op.drop_table('feature_sets')
    op.drop_table('feature_definitions')
    op.drop_table('feature_entities')
