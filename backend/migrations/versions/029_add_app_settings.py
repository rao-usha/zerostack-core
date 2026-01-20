"""Add app_settings table for database-backed configuration.

Revision ID: 029_add_app_settings
Revises: 028_add_datasets
Create Date: 2026-01-19
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '029_add_app_settings'
down_revision = '028_add_datasets'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create app_settings table
    op.create_table(
        'app_settings',
        sa.Column('id', postgresql.UUID(), nullable=False),

        # Organization (NULL = global setting)
        sa.Column('org_id', sa.String(100), nullable=True),

        # Categorization
        sa.Column('category', sa.String(64), nullable=False),  # 'llm', 'compute', 'storage', 'oauth', 'feature'
        sa.Column('key', sa.String(255), nullable=False),

        # Value (always encrypted for secrets)
        sa.Column('value_encrypted', sa.Text(), nullable=True),
        sa.Column('is_secret', sa.Boolean(), server_default='true', nullable=False),

        # Metadata
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('display_name', sa.String(255), nullable=True),
        sa.Column('validation_pattern', sa.String(255), nullable=True),  # Regex for validation

        # Audit
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_by', sa.String(100), nullable=True),

        sa.PrimaryKeyConstraint('id')
    )

    # Unique constraint on org_id + category + key
    op.create_index(
        'ix_app_settings_unique_key',
        'app_settings',
        ['org_id', 'category', 'key'],
        unique=True
    )

    # Index for fast category lookups
    op.create_index('ix_app_settings_category', 'app_settings', ['category'])


def downgrade() -> None:
    op.drop_index('ix_app_settings_category', 'app_settings')
    op.drop_index('ix_app_settings_unique_key', 'app_settings')
    op.drop_table('app_settings')
