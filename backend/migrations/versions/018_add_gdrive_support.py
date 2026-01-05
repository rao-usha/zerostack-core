"""Add Google Drive support to files domain

Revision ID: 018_add_gdrive_support
Revises: 017_add_files_domain
Create Date: 2026-01-05
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
import uuid

# revision identifiers
revision = '018_add_gdrive_support'
down_revision = '017_add_files_domain'
branch_labels = None
depends_on = None


def upgrade():
    # Create external_accounts table
    op.create_table(
        'external_accounts',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('provider', sa.String(), nullable=False),
        sa.Column('account_email', sa.String(), nullable=False, index=True),
        sa.Column('scopes', sa.Text(), nullable=False),
        sa.Column('access_token_encrypted', sa.Text(), nullable=True),
        sa.Column('refresh_token_encrypted', sa.Text(), nullable=True),
        sa.Column('token_expiry', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    
    # Add Google Drive columns to file_locations
    op.add_column('file_locations', sa.Column('gdrive_folder_id', sa.String(), nullable=True))
    op.add_column('file_locations', sa.Column('gdrive_include_shared_drives', sa.Boolean(), nullable=False, server_default='true'))
    op.add_column('file_locations', sa.Column('gdrive_account_email', sa.String(), nullable=True))
    op.add_column('file_locations', sa.Column('auth_provider', sa.String(), nullable=False, server_default='none'))
    op.add_column('file_locations', sa.Column('external_account_id', UUID(as_uuid=True), nullable=True))
    
    # Add foreign key for external_account_id
    op.create_foreign_key(
        'fk_file_locations_external_account',
        'file_locations',
        'external_accounts',
        ['external_account_id'],
        ['id']
    )
    op.create_index('ix_file_locations_external_account_id', 'file_locations', ['external_account_id'])


def downgrade():
    # Drop foreign key and index
    op.drop_index('ix_file_locations_external_account_id', table_name='file_locations')
    op.drop_constraint('fk_file_locations_external_account', 'file_locations', type_='foreignkey')
    
    # Drop Google Drive columns
    op.drop_column('file_locations', 'external_account_id')
    op.drop_column('file_locations', 'auth_provider')
    op.drop_column('file_locations', 'gdrive_account_email')
    op.drop_column('file_locations', 'gdrive_include_shared_drives')
    op.drop_column('file_locations', 'gdrive_folder_id')
    
    # Drop external_accounts table
    op.drop_table('external_accounts')
