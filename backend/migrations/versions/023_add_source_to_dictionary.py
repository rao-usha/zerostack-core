"""Add source column to data dictionary for grouping

Revision ID: 023_add_source_to_dictionary
Revises: 022_add_phase_2
Create Date: 2026-01-14

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '023_add_source_to_dictionary'
down_revision = '022_add_phase_2'
branch_labels = None
depends_on = None


def upgrade():
    """
    Add data_source column to data_dictionary_entries for logical grouping.
    
    data_source identifies the origin of the data (e.g., 'Census ACS', 'M5 Dataset', etc.)
    This enables card-view grouping and marketing display of data sources.
    """
    # Add data_source column
    op.add_column(
        'data_dictionary_entries',
        sa.Column('data_source', sa.String(length=100), nullable=True)
    )
    
    # Add index on data_source for faster grouping queries
    op.create_index(
        'ix_data_dictionary_entries_data_source',
        'data_dictionary_entries',
        ['data_source']
    )
    
    # Auto-populate data_source based on table naming patterns
    # ACS Census data
    op.execute("""
        UPDATE data_dictionary_entries 
        SET data_source = 'Census ACS'
        WHERE table_name LIKE 'acs%'
    """)
    
    # M5 dataset
    op.execute("""
        UPDATE data_dictionary_entries 
        SET data_source = 'M5 Competition'
        WHERE table_name LIKE 'm5_%'
    """)
    
    # Default for others
    op.execute("""
        UPDATE data_dictionary_entries 
        SET data_source = 'Other'
        WHERE data_source IS NULL
    """)


def downgrade():
    """Remove data_source column."""
    op.drop_index('ix_data_dictionary_entries_data_source', table_name='data_dictionary_entries')
    op.drop_column('data_dictionary_entries', 'data_source')
