"""Add password_hash column to users table.

Revision ID: 049_add_user_password
Revises: 048_add_personas_tables
Create Date: 2025-01-01
"""
from alembic import op
import sqlalchemy as sa


revision = '049_add_user_password'
down_revision = '048_add_personas_tables'
branch_labels = None
depends_on = None


def upgrade():
    # Add password_hash column to users table
    op.add_column('users', sa.Column('password_hash', sa.Text(), nullable=True))

    # Add username column (referenced in auth models but missing from table)
    op.add_column('users', sa.Column('username', sa.String(255), nullable=True))

    # Add full_name column
    op.add_column('users', sa.Column('full_name', sa.String(500), nullable=True))

    # Add is_active column for account status
    op.add_column('users', sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'))

    # Add updated_at column
    op.add_column('users', sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()))

    # Create unique index on username
    op.create_index('ix_users_username', 'users', ['username'], unique=True)


def downgrade():
    op.drop_index('ix_users_username', table_name='users')
    op.drop_column('users', 'updated_at')
    op.drop_column('users', 'is_active')
    op.drop_column('users', 'full_name')
    op.drop_column('users', 'username')
    op.drop_column('users', 'password_hash')
