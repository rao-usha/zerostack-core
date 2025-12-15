"""Add versioning to data dictionary entries.

Revision ID: 009_versioning
Revises: 008_dictionary
Create Date: 2025-12-14

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '009_versioning'
down_revision = '008_dictionary'
branch_labels = None
depends_on = None


def upgrade():
    """Add version and active status fields."""
    # Add version_number column (defaults to 1 for existing entries)
    op.add_column('data_dictionary_entries', 
        sa.Column('version_number', sa.Integer(), nullable=False, server_default='1'))
    
    # Add is_active column (defaults to True for existing entries)
    op.add_column('data_dictionary_entries', 
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'))
    
    # Add version_notes column for tracking what changed
    op.add_column('data_dictionary_entries', 
        sa.Column('version_notes', sa.Text(), nullable=True))
    
    # Drop the old unique constraint (database, schema, table, column)
    op.drop_constraint('uq_dictionary_entry', 'data_dictionary_entries', type_='unique')
    
    # Create new unique constraint that includes version_number
    # (database, schema, table, column, version) must be unique
    op.create_unique_constraint(
        'uq_dictionary_entry_version',
        'data_dictionary_entries',
        ['database_name', 'schema_name', 'table_name', 'column_name', 'version_number']
    )
    
    # Create index on is_active for fast queries of active entries
    op.create_index('ix_data_dictionary_entries_is_active', 'data_dictionary_entries', ['is_active'])
    
    # Create composite index for fast active-only queries
    op.create_index(
        'ix_data_dictionary_active_lookup',
        'data_dictionary_entries',
        ['database_name', 'schema_name', 'table_name', 'is_active']
    )


def downgrade():
    """Remove versioning fields."""
    # Drop new indexes
    op.drop_index('ix_data_dictionary_active_lookup', table_name='data_dictionary_entries')
    op.drop_index('ix_data_dictionary_entries_is_active', table_name='data_dictionary_entries')
    
    # Drop new unique constraint
    op.drop_constraint('uq_dictionary_entry_version', 'data_dictionary_entries', type_='unique')
    
    # Restore old unique constraint
    op.create_unique_constraint(
        'uq_dictionary_entry',
        'data_dictionary_entries',
        ['database_name', 'schema_name', 'table_name', 'column_name']
    )
    
    # Drop columns
    op.drop_column('data_dictionary_entries', 'version_notes')
    op.drop_column('data_dictionary_entries', 'is_active')
    op.drop_column('data_dictionary_entries', 'version_number')

