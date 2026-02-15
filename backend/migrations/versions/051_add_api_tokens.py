"""Add api_tokens table for programmatic API access.

Revision ID: 051_add_api_tokens
Revises: 050_add_refresh_tokens
Create Date: 2026-02-11
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '051_add_api_tokens'
down_revision = '050_add_refresh_tokens'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'api_tokens',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('org_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('orgs.id', ondelete='CASCADE'), nullable=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('token_hash', sa.String(255), nullable=False, unique=True),
        sa.Column('token_prefix', sa.String(12), nullable=False),
        sa.Column('expires_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('last_used_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('revoked_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )

    # Index for faster lookups
    op.create_index('ix_api_tokens_user_id', 'api_tokens', ['user_id'])
    op.create_index('ix_api_tokens_token_hash', 'api_tokens', ['token_hash'])


def downgrade() -> None:
    op.drop_index('ix_api_tokens_token_hash', table_name='api_tokens')
    op.drop_index('ix_api_tokens_user_id', table_name='api_tokens')
    op.drop_table('api_tokens')
