"""Create users table with authentication support.

Revision ID: 049_add_user_password
Revises: 048_add_personas_tables
Create Date: 2025-01-01
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP


revision = '049_add_user_password'
down_revision = '048_add_personas_tables'
branch_labels = None
depends_on = None


def upgrade():
    # Create the users table
    op.create_table(
        'users',
        sa.Column('id', UUID, primary_key=True),
        sa.Column('org_id', UUID),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('username', sa.String(255), nullable=True),
        sa.Column('password_hash', sa.Text(), nullable=True),
        sa.Column('full_name', sa.String(500), nullable=True),
        sa.Column('role', sa.String(50), nullable=False, server_default='user'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )

    # Create indexes
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    op.create_index('ix_users_username', 'users', ['username'], unique=True)
    op.create_index('ix_users_org_id', 'users', ['org_id'])


def downgrade():
    op.drop_index('ix_users_org_id', table_name='users')
    op.drop_index('ix_users_username', table_name='users')
    op.drop_index('ix_users_email', table_name='users')
    op.drop_table('users')
