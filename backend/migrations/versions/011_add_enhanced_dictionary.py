"""Add enhanced data dictionary tables for semantics, relationships, and profiling.

Revision ID: 011_enhanced_dict
Revises: 297d473edc6b
Create Date: 2025-12-16

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '011_enhanced_dict'
down_revision = '297d473edc6b'
branch_labels = None
depends_on = None


def upgrade():
    """Create enhanced dictionary tables."""
    
    # 1. dictionary_assets (table-level metadata)
    op.create_table(
        'dictionary_assets',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('connection_id', sa.String(length=100), nullable=False),
        sa.Column('schema_name', sa.String(length=255), nullable=False),
        sa.Column('table_name', sa.String(length=255), nullable=False),
        sa.Column('asset_type', sa.String(length=50), nullable=False, server_default='table'),
        
        # Business semantics
        sa.Column('business_name', sa.String(length=255), nullable=True),
        sa.Column('business_definition', sa.Text(), nullable=True),
        sa.Column('business_domain', sa.String(length=100), nullable=True),
        sa.Column('grain', sa.Text(), nullable=True),
        sa.Column('row_meaning', sa.Text(), nullable=True),
        
        # Ownership
        sa.Column('owner', sa.String(length=255), nullable=True),
        sa.Column('steward', sa.String(length=255), nullable=True),
        sa.Column('tags', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        
        # Trust & quality
        sa.Column('trust_tier', sa.String(length=50), nullable=False, server_default='experimental'),
        sa.Column('trust_score', sa.Integer(), nullable=False, server_default='50'),
        sa.Column('approved_for_reporting', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('approved_for_ml', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('known_issues', sa.Text(), nullable=True),
        sa.Column('issue_tags', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        
        # Usage metrics
        sa.Column('query_count_30d', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_queried_at', sa.DateTime(), nullable=True),
        
        # Technical metadata
        sa.Column('row_count_estimate', sa.Integer(), nullable=True),
        sa.Column('size_bytes', sa.Integer(), nullable=True),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        
        sa.PrimaryKeyConstraint('id')
    )
    
    # Indexes for dictionary_assets
    op.create_index('ix_dict_assets_connection_id', 'dictionary_assets', ['connection_id'])
    op.create_index('ix_dict_assets_schema', 'dictionary_assets', ['schema_name'])
    op.create_index('ix_dict_assets_table', 'dictionary_assets', ['table_name'])
    op.create_index('ix_dict_assets_trust_tier', 'dictionary_assets', ['trust_tier'])
    op.create_index('ix_dict_assets_domain', 'dictionary_assets', ['business_domain'])
    
    # Unique constraint on (connection_id, schema_name, table_name)
    op.create_unique_constraint(
        'uq_dict_asset',
        'dictionary_assets',
        ['connection_id', 'schema_name', 'table_name']
    )
    
    # 2. dictionary_fields (column-level metadata)
    op.create_table(
        'dictionary_fields',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('asset_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('column_name', sa.String(length=255), nullable=False),
        sa.Column('ordinal_position', sa.Integer(), nullable=True),
        
        # Technical details
        sa.Column('data_type', sa.String(length=100), nullable=True),
        sa.Column('is_nullable', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('default_value', sa.Text(), nullable=True),
        
        # Business semantics
        sa.Column('business_name', sa.String(length=255), nullable=True),
        sa.Column('business_definition', sa.Text(), nullable=True),
        sa.Column('entity_role', sa.String(length=50), nullable=False, server_default='other'),
        sa.Column('tags', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        
        # Trust & quality
        sa.Column('trust_tier', sa.String(length=50), nullable=False, server_default='experimental'),
        sa.Column('trust_score', sa.Integer(), nullable=False, server_default='50'),
        sa.Column('approved_for_reporting', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('approved_for_ml', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('known_issues', sa.Text(), nullable=True),
        sa.Column('issue_tags', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        
        # Usage metrics
        sa.Column('query_count_30d', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_queried_at', sa.DateTime(), nullable=True),
        sa.Column('top_filters', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('top_group_bys', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        
        sa.PrimaryKeyConstraint('id')
    )
    
    # Indexes for dictionary_fields
    op.create_index('ix_dict_fields_asset_id', 'dictionary_fields', ['asset_id'])
    op.create_index('ix_dict_fields_column', 'dictionary_fields', ['column_name'])
    op.create_index('ix_dict_fields_role', 'dictionary_fields', ['entity_role'])
    
    # Unique constraint on (asset_id, column_name)
    op.create_unique_constraint(
        'uq_dict_field',
        'dictionary_fields',
        ['asset_id', 'column_name']
    )
    
    # 3. dictionary_relationships (join intelligence)
    op.create_table(
        'dictionary_relationships',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('connection_id', sa.String(length=100), nullable=False),
        
        # Source (FK side)
        sa.Column('source_schema', sa.String(length=255), nullable=False),
        sa.Column('source_table', sa.String(length=255), nullable=False),
        sa.Column('source_column', sa.String(length=255), nullable=False),
        
        # Target (PK side)
        sa.Column('target_schema', sa.String(length=255), nullable=False),
        sa.Column('target_table', sa.String(length=255), nullable=False),
        sa.Column('target_column', sa.String(length=255), nullable=False),
        
        # Relationship metadata
        sa.Column('cardinality', sa.String(length=50), nullable=False, server_default='unknown'),
        sa.Column('confidence', sa.String(length=50), nullable=False, server_default='assumed'),
        sa.Column('notes', sa.Text(), nullable=True),
        
        # Usage
        sa.Column('join_count_30d', sa.Integer(), nullable=False, server_default='0'),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        
        sa.PrimaryKeyConstraint('id')
    )
    
    # Indexes for dictionary_relationships
    op.create_index('ix_dict_rels_connection_id', 'dictionary_relationships', ['connection_id'])
    op.create_index('ix_dict_rels_source', 'dictionary_relationships', ['source_schema', 'source_table'])
    op.create_index('ix_dict_rels_target', 'dictionary_relationships', ['target_schema', 'target_table'])
    
    # 4. dictionary_profiles (profiling snapshots)
    op.create_table(
        'dictionary_profiles',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('connection_id', sa.String(length=100), nullable=False),
        sa.Column('schema_name', sa.String(length=255), nullable=False),
        sa.Column('table_name', sa.String(length=255), nullable=False),
        sa.Column('column_name', sa.String(length=255), nullable=False),
        
        # Table-level context
        sa.Column('row_count_estimate', sa.Integer(), nullable=True),
        
        # Completeness
        sa.Column('null_count', sa.Integer(), nullable=True),
        sa.Column('null_fraction', sa.Float(), nullable=True),
        
        # Cardinality
        sa.Column('distinct_count', sa.Integer(), nullable=True),
        sa.Column('distinct_count_estimate', sa.Integer(), nullable=True),
        sa.Column('uniqueness_fraction', sa.Float(), nullable=True),
        
        # Numeric stats
        sa.Column('numeric_min', sa.Float(), nullable=True),
        sa.Column('numeric_max', sa.Float(), nullable=True),
        sa.Column('numeric_avg', sa.Float(), nullable=True),
        sa.Column('numeric_stddev', sa.Float(), nullable=True),
        sa.Column('numeric_median', sa.Float(), nullable=True),
        
        # Categorical stats
        sa.Column('top_values', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        
        # String stats
        sa.Column('min_length', sa.Integer(), nullable=True),
        sa.Column('max_length', sa.Integer(), nullable=True),
        sa.Column('avg_length', sa.Float(), nullable=True),
        
        # Temporal stats
        sa.Column('earliest_value', sa.DateTime(), nullable=True),
        sa.Column('latest_value', sa.DateTime(), nullable=True),
        
        # Profiling metadata
        sa.Column('sample_size', sa.Integer(), nullable=True),
        sa.Column('sample_method', sa.String(length=50), nullable=True),
        sa.Column('profile_version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('computed_at', sa.DateTime(), nullable=False),
        
        sa.PrimaryKeyConstraint('id')
    )
    
    # Indexes for dictionary_profiles
    op.create_index('ix_dict_profiles_connection_id', 'dictionary_profiles', ['connection_id'])
    op.create_index('ix_dict_profiles_schema', 'dictionary_profiles', ['schema_name'])
    op.create_index('ix_dict_profiles_table', 'dictionary_profiles', ['table_name'])
    op.create_index('ix_dict_profiles_column', 'dictionary_profiles', ['column_name'])
    op.create_index('ix_dict_profiles_computed_at', 'dictionary_profiles', ['computed_at'])
    
    # Composite index for fast "latest profile" queries
    op.create_index(
        'ix_dict_profiles_latest',
        'dictionary_profiles',
        ['connection_id', 'schema_name', 'table_name', 'column_name', 'computed_at']
    )
    
    # 5. dictionary_usage_logs (optional detailed tracking)
    op.create_table(
        'dictionary_usage_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('connection_id', sa.String(length=100), nullable=False),
        sa.Column('event_type', sa.String(length=50), nullable=False),
        
        # Referenced objects
        sa.Column('schemas_used', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('tables_used', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('columns_used', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        
        # Query context
        sa.Column('query_text', sa.Text(), nullable=True),
        sa.Column('query_hash', sa.String(length=64), nullable=True),
        
        # User context
        sa.Column('user_id', sa.String(length=100), nullable=True),
        sa.Column('session_id', sa.String(length=100), nullable=True),
        
        # Timestamps
        sa.Column('event_at', sa.DateTime(), nullable=False),
        
        sa.PrimaryKeyConstraint('id')
    )
    
    # Indexes for dictionary_usage_logs
    op.create_index('ix_dict_usage_connection_id', 'dictionary_usage_logs', ['connection_id'])
    op.create_index('ix_dict_usage_event_at', 'dictionary_usage_logs', ['event_at'])
    op.create_index('ix_dict_usage_query_hash', 'dictionary_usage_logs', ['query_hash'])


def downgrade():
    """Drop enhanced dictionary tables."""
    op.drop_table('dictionary_usage_logs')
    op.drop_table('dictionary_profiles')
    op.drop_table('dictionary_relationships')
    op.drop_table('dictionary_fields')
    op.drop_table('dictionary_assets')


