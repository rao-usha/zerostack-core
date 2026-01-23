"""Add PE due diligence ingestion tables.

Revision ID: 036_add_ingestion_tables
Revises: 035_add_monitoring_metrics
Create Date: 2026-01-23

Adds tables for PE due diligence data ingestion:
- pe_deals: Track PE deal/target companies
- ingested_files: Uploaded files with analysis results
- ingestion_issues: Quality issues and red flags detected
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB


# revision identifiers
revision = '036_add_ingestion_tables'
down_revision = '035_add_monitoring_metrics'
branch_labels = None
depends_on = None


def upgrade():
    # PE Deals - group files by target company/deal
    op.create_table(
        'pe_deals',
        sa.Column('id', UUID, primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('target_company', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='active'),
        sa.Column('deal_stage', sa.String(100), nullable=True),
        sa.Column('deal_owner', sa.String(255), nullable=True),
        sa.Column('target_close_date', sa.Date, nullable=True),
        sa.Column('metadata', JSONB, nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )

    # Ingested Files - uploaded files with analysis
    op.create_table(
        'ingested_files',
        sa.Column('id', UUID, primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('deal_id', UUID, sa.ForeignKey('pe_deals.id', ondelete='SET NULL'), nullable=True),

        # File info
        sa.Column('filename', sa.String(255), nullable=False),
        sa.Column('original_filename', sa.String(255), nullable=False),
        sa.Column('file_type', sa.String(100), nullable=False),
        sa.Column('file_size_bytes', sa.BigInteger, nullable=False),
        sa.Column('content_hash', sa.String(64), nullable=True),

        # Storage
        sa.Column('storage_path', sa.String(500), nullable=True),
        sa.Column('storage_bucket', sa.String(255), nullable=True),

        # Source
        sa.Column('upload_source', sa.String(50), nullable=False, server_default='manual'),
        sa.Column('source_system', sa.String(100), nullable=True),
        sa.Column('source_account_id', sa.String(255), nullable=True),

        # Analysis results
        sa.Column('quality_score', sa.Numeric(5, 2), nullable=True),
        sa.Column('row_count', sa.Integer, nullable=True),
        sa.Column('column_count', sa.Integer, nullable=True),
        sa.Column('sheet_count', sa.Integer, nullable=True, server_default='1'),
        sa.Column('detected_categories', JSONB, nullable=True),
        sa.Column('schema_analysis', JSONB, nullable=True),
        sa.Column('analysis_summary', sa.Text, nullable=True),

        # Status
        sa.Column('status', sa.String(50), nullable=False, server_default='pending'),
        sa.Column('error_message', sa.Text, nullable=True),

        # Audit
        sa.Column('uploaded_by', sa.String(255), nullable=True),
        sa.Column('uploaded_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('analyzed_at', sa.TIMESTAMP(timezone=True), nullable=True),
    )

    # Ingestion Issues - quality issues and red flags
    op.create_table(
        'ingestion_issues',
        sa.Column('id', UUID, primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('file_id', UUID, sa.ForeignKey('ingested_files.id', ondelete='CASCADE'), nullable=False),
        sa.Column('deal_id', UUID, sa.ForeignKey('pe_deals.id', ondelete='SET NULL'), nullable=True),

        # Issue details
        sa.Column('issue_type', sa.String(50), nullable=False),
        sa.Column('severity', sa.String(20), nullable=False),
        sa.Column('category', sa.String(100), nullable=True),
        sa.Column('sheet_name', sa.String(255), nullable=True),
        sa.Column('column_name', sa.String(255), nullable=True),
        sa.Column('row_number', sa.Integer, nullable=True),

        # Description
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('details', JSONB, nullable=True),
        sa.Column('recommendation', sa.Text, nullable=True),

        # Resolution
        sa.Column('status', sa.String(50), nullable=False, server_default='open'),
        sa.Column('acknowledged', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('acknowledged_by', sa.String(255), nullable=True),
        sa.Column('acknowledged_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('resolution_notes', sa.Text, nullable=True),

        # Timestamps
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )

    # Indexes
    op.create_index('idx_pe_deals_status', 'pe_deals', ['status'])
    op.create_index('idx_pe_deals_target', 'pe_deals', ['target_company'])

    op.create_index('idx_ingested_files_deal', 'ingested_files', ['deal_id'])
    op.create_index('idx_ingested_files_status', 'ingested_files', ['status'])
    op.create_index('idx_ingested_files_uploaded', 'ingested_files', ['uploaded_at'])
    op.create_index('idx_ingested_files_source', 'ingested_files', ['upload_source'])
    op.create_index('idx_ingested_files_hash', 'ingested_files', ['content_hash'])

    op.create_index('idx_ingestion_issues_file', 'ingestion_issues', ['file_id'])
    op.create_index('idx_ingestion_issues_deal', 'ingestion_issues', ['deal_id'])
    op.create_index('idx_ingestion_issues_type', 'ingestion_issues', ['issue_type'])
    op.create_index('idx_ingestion_issues_severity', 'ingestion_issues', ['severity'])
    op.create_index('idx_ingestion_issues_status', 'ingestion_issues', ['status'])


def downgrade():
    # Drop indexes
    op.drop_index('idx_ingestion_issues_status')
    op.drop_index('idx_ingestion_issues_severity')
    op.drop_index('idx_ingestion_issues_type')
    op.drop_index('idx_ingestion_issues_deal')
    op.drop_index('idx_ingestion_issues_file')

    op.drop_index('idx_ingested_files_hash')
    op.drop_index('idx_ingested_files_source')
    op.drop_index('idx_ingested_files_uploaded')
    op.drop_index('idx_ingested_files_status')
    op.drop_index('idx_ingested_files_deal')

    op.drop_index('idx_pe_deals_target')
    op.drop_index('idx_pe_deals_status')

    # Drop tables
    op.drop_table('ingestion_issues')
    op.drop_table('ingested_files')
    op.drop_table('pe_deals')
