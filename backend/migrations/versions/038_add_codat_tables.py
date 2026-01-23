"""Add Codat integration tables.

Revision ID: 038_add_codat_tables
Revises: 037_add_investor_ingestion
Create Date: 2026-01-23

Adds tables for Codat accounting system integration:
- codat_companies: Track connected companies
- codat_connections: Track data connections per company
- codat_sync_history: Track sync operations
- codat_financial_cache: Cache financial statements
- codat_customers_cache: Cache customer data
- codat_invoices_cache: Cache invoice data
- codat_bank_transactions_cache: Cache bank transactions
- codat_webhook_events: Log incoming webhooks
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB


# revision identifiers
revision = '038_add_codat_tables'
down_revision = '037_add_investor_ingestion'
branch_labels = None
depends_on = None


def upgrade():
    # Codat Companies - our representation of Codat company records
    op.create_table(
        'codat_companies',
        sa.Column('id', UUID, primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('codat_company_id', sa.String(64), nullable=False, unique=True),
        sa.Column('deal_id', UUID, sa.ForeignKey('pe_deals.id', ondelete='SET NULL'), nullable=True),

        # Company info
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=True),

        # Status
        sa.Column('status', sa.String(32), nullable=False, server_default='pending'),

        # Codat link info
        sa.Column('link_url', sa.Text, nullable=True),
        sa.Column('redirect_url', sa.Text, nullable=True),

        # Connection info
        sa.Column('platform', sa.String(64), nullable=True),
        sa.Column('platform_key', sa.String(32), nullable=True),

        # Sync status
        sa.Column('last_sync_requested', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('last_sync_completed', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('sync_status', sa.String(32), server_default='never'),
        sa.Column('sync_error', sa.Text, nullable=True),

        # Cached summary metrics
        sa.Column('total_revenue', sa.DECIMAL(18, 2), nullable=True),
        sa.Column('total_assets', sa.DECIMAL(18, 2), nullable=True),
        sa.Column('total_liabilities', sa.DECIMAL(18, 2), nullable=True),
        sa.Column('total_customers', sa.Integer, nullable=True),
        sa.Column('data_currency', sa.String(8), server_default='USD'),

        # Timestamps
        sa.Column('codat_created_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )

    # Codat Connections - tracks individual platform connections
    op.create_table(
        'codat_connections',
        sa.Column('id', UUID, primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('codat_connection_id', sa.String(64), nullable=False, unique=True),
        sa.Column('company_id', UUID, sa.ForeignKey('codat_companies.id', ondelete='CASCADE'), nullable=False),

        # Connection details
        sa.Column('platform_name', sa.String(64), nullable=False),
        sa.Column('integration_id', sa.String(64), nullable=True),
        sa.Column('integration_key', sa.String(32), nullable=True),
        sa.Column('source_id', sa.String(64), nullable=True),

        # Status
        sa.Column('status', sa.String(32), nullable=False),

        # Link info
        sa.Column('link_url', sa.Text, nullable=True),

        # Sync tracking
        sa.Column('last_sync', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('created', sa.TIMESTAMP(timezone=True), nullable=True),

        # Error tracking
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('error_details', JSONB, server_default='{}'),

        # Timestamps
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )

    # Codat Sync History - tracks each sync operation
    op.create_table(
        'codat_sync_history',
        sa.Column('id', UUID, primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('company_id', UUID, sa.ForeignKey('codat_companies.id', ondelete='CASCADE'), nullable=False),
        sa.Column('connection_id', UUID, sa.ForeignKey('codat_connections.id', ondelete='SET NULL'), nullable=True),

        # Sync details
        sa.Column('codat_sync_id', sa.String(64), nullable=True),
        sa.Column('data_type', sa.String(64), nullable=False),

        # Status
        sa.Column('status', sa.String(32), nullable=False),

        # Results
        sa.Column('records_synced', sa.Integer, nullable=True),
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('details', JSONB, server_default='{}'),

        # Timestamps
        sa.Column('requested_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('started_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('completed_at', sa.TIMESTAMP(timezone=True), nullable=True),
    )

    # Codat Financial Cache - store financial statements locally
    op.create_table(
        'codat_financial_cache',
        sa.Column('id', UUID, primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('company_id', UUID, sa.ForeignKey('codat_companies.id', ondelete='CASCADE'), nullable=False),

        # Report type
        sa.Column('report_type', sa.String(32), nullable=False),

        # Period
        sa.Column('period_start', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('period_end', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('period_length_months', sa.Integer, nullable=True),

        # The full report data as JSON
        sa.Column('report_data', JSONB, nullable=False),

        # Currency
        sa.Column('currency', sa.String(8), server_default='USD'),

        # Summary metrics
        sa.Column('total_assets', sa.DECIMAL(18, 2), nullable=True),
        sa.Column('total_liabilities', sa.DECIMAL(18, 2), nullable=True),
        sa.Column('total_equity', sa.DECIMAL(18, 2), nullable=True),
        sa.Column('total_revenue', sa.DECIMAL(18, 2), nullable=True),
        sa.Column('gross_profit', sa.DECIMAL(18, 2), nullable=True),
        sa.Column('net_profit', sa.DECIMAL(18, 2), nullable=True),

        # Timestamps
        sa.Column('report_date', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('synced_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )

    # Codat Customers Cache
    op.create_table(
        'codat_customers_cache',
        sa.Column('id', UUID, primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('company_id', UUID, sa.ForeignKey('codat_companies.id', ondelete='CASCADE'), nullable=False),
        sa.Column('codat_customer_id', sa.String(64), nullable=False),

        # Customer info
        sa.Column('customer_name', sa.String(255), nullable=False),
        sa.Column('contact_name', sa.String(255), nullable=True),
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('phone', sa.String(64), nullable=True),
        sa.Column('default_currency', sa.String(8), server_default='USD'),
        sa.Column('status', sa.String(32), nullable=True),

        # Financial metrics
        sa.Column('total_revenue', sa.DECIMAL(18, 2), nullable=True),
        sa.Column('outstanding_balance', sa.DECIMAL(18, 2), nullable=True),
        sa.Column('invoice_count', sa.Integer, nullable=True),

        # Addresses as JSON
        sa.Column('addresses', JSONB, server_default='[]'),

        # Timestamps
        sa.Column('source_modified_date', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('synced_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )

    # Codat Invoices Cache
    op.create_table(
        'codat_invoices_cache',
        sa.Column('id', UUID, primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('company_id', UUID, sa.ForeignKey('codat_companies.id', ondelete='CASCADE'), nullable=False),
        sa.Column('codat_invoice_id', sa.String(64), nullable=False),

        # Invoice info
        sa.Column('invoice_number', sa.String(64), nullable=True),
        sa.Column('customer_id', sa.String(64), nullable=True),
        sa.Column('customer_name', sa.String(255), nullable=True),

        # Dates
        sa.Column('issue_date', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('due_date', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('paid_on_date', sa.TIMESTAMP(timezone=True), nullable=True),

        # Amounts
        sa.Column('currency', sa.String(8), server_default='USD'),
        sa.Column('sub_total', sa.DECIMAL(18, 2), nullable=True),
        sa.Column('tax_amount', sa.DECIMAL(18, 2), nullable=True),
        sa.Column('total_amount', sa.DECIMAL(18, 2), nullable=True),
        sa.Column('amount_due', sa.DECIMAL(18, 2), nullable=True),

        # Status
        sa.Column('status', sa.String(32), nullable=True),

        # Line items as JSON
        sa.Column('line_items', JSONB, server_default='[]'),

        # Timestamps
        sa.Column('source_modified_date', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('synced_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )

    # Codat Bank Transactions Cache
    op.create_table(
        'codat_bank_transactions_cache',
        sa.Column('id', UUID, primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('company_id', UUID, sa.ForeignKey('codat_companies.id', ondelete='CASCADE'), nullable=False),
        sa.Column('codat_transaction_id', sa.String(64), nullable=False),

        # Transaction info
        sa.Column('account_id', sa.String(64), nullable=True),
        sa.Column('account_name', sa.String(255), nullable=True),
        sa.Column('date', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('description', sa.Text, nullable=True),

        # Amount
        sa.Column('amount', sa.DECIMAL(18, 2), nullable=True),
        sa.Column('currency', sa.String(8), server_default='USD'),
        sa.Column('transaction_type', sa.String(32), nullable=True),

        # Categorization
        sa.Column('category', sa.String(255), nullable=True),
        sa.Column('merchant_name', sa.String(255), nullable=True),

        # Reconciliation
        sa.Column('reconciled', sa.Boolean, server_default='false'),

        # Timestamps
        sa.Column('source_modified_date', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('synced_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )

    # Codat Webhook Events - log all incoming webhooks
    op.create_table(
        'codat_webhook_events',
        sa.Column('id', UUID, primary_key=True, server_default=sa.text('gen_random_uuid()')),

        # Event info
        sa.Column('codat_event_id', sa.String(64), nullable=True),
        sa.Column('event_type', sa.String(64), nullable=False),
        sa.Column('company_id', sa.String(64), nullable=True),
        sa.Column('connection_id', sa.String(64), nullable=True),

        # Raw payload
        sa.Column('payload', JSONB, nullable=False),

        # Processing status
        sa.Column('processed', sa.Boolean, server_default='false'),
        sa.Column('processed_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('processing_error', sa.Text, nullable=True),

        # Timestamps
        sa.Column('received_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )

    # Create indexes
    # codat_companies indexes
    op.create_index('ix_codat_companies_deal_id', 'codat_companies', ['deal_id'])
    op.create_index('ix_codat_companies_status', 'codat_companies', ['status'])
    op.create_index('ix_codat_companies_platform', 'codat_companies', ['platform'])

    # codat_connections indexes
    op.create_index('ix_codat_connections_company_id', 'codat_connections', ['company_id'])
    op.create_index('ix_codat_connections_status', 'codat_connections', ['status'])

    # codat_sync_history indexes
    op.create_index('ix_codat_sync_history_company_id', 'codat_sync_history', ['company_id'])
    op.create_index('ix_codat_sync_history_data_type', 'codat_sync_history', ['data_type'])
    op.create_index('ix_codat_sync_history_status', 'codat_sync_history', ['status'])

    # codat_financial_cache indexes
    op.create_index('ix_codat_financial_cache_company_report', 'codat_financial_cache', ['company_id', 'report_type'])
    op.create_index('ix_codat_financial_cache_period', 'codat_financial_cache', ['period_end'])

    # codat_customers_cache indexes
    op.create_index('ix_codat_customers_cache_company_id', 'codat_customers_cache', ['company_id'])
    op.create_index('ix_codat_customers_cache_unique', 'codat_customers_cache', ['company_id', 'codat_customer_id'], unique=True)

    # codat_invoices_cache indexes
    op.create_index('ix_codat_invoices_cache_company_id', 'codat_invoices_cache', ['company_id'])
    op.create_index('ix_codat_invoices_cache_customer_id', 'codat_invoices_cache', ['customer_id'])
    op.create_index('ix_codat_invoices_cache_status', 'codat_invoices_cache', ['status'])
    op.create_index('ix_codat_invoices_cache_issue_date', 'codat_invoices_cache', ['issue_date'])
    op.create_index('ix_codat_invoices_cache_unique', 'codat_invoices_cache', ['company_id', 'codat_invoice_id'], unique=True)

    # codat_bank_transactions_cache indexes
    op.create_index('ix_codat_bank_transactions_company_id', 'codat_bank_transactions_cache', ['company_id'])
    op.create_index('ix_codat_bank_transactions_account_id', 'codat_bank_transactions_cache', ['account_id'])
    op.create_index('ix_codat_bank_transactions_date', 'codat_bank_transactions_cache', ['date'])
    op.create_index('ix_codat_bank_transactions_unique', 'codat_bank_transactions_cache', ['company_id', 'codat_transaction_id'], unique=True)

    # codat_webhook_events indexes
    op.create_index('ix_codat_webhook_events_type', 'codat_webhook_events', ['event_type'])
    op.create_index('ix_codat_webhook_events_company', 'codat_webhook_events', ['company_id'])
    op.create_index('ix_codat_webhook_events_processed', 'codat_webhook_events', ['processed'])


def downgrade():
    # Drop indexes
    op.drop_index('ix_codat_webhook_events_processed')
    op.drop_index('ix_codat_webhook_events_company')
    op.drop_index('ix_codat_webhook_events_type')

    op.drop_index('ix_codat_bank_transactions_unique')
    op.drop_index('ix_codat_bank_transactions_date')
    op.drop_index('ix_codat_bank_transactions_account_id')
    op.drop_index('ix_codat_bank_transactions_company_id')

    op.drop_index('ix_codat_invoices_cache_unique')
    op.drop_index('ix_codat_invoices_cache_issue_date')
    op.drop_index('ix_codat_invoices_cache_status')
    op.drop_index('ix_codat_invoices_cache_customer_id')
    op.drop_index('ix_codat_invoices_cache_company_id')

    op.drop_index('ix_codat_customers_cache_unique')
    op.drop_index('ix_codat_customers_cache_company_id')

    op.drop_index('ix_codat_financial_cache_period')
    op.drop_index('ix_codat_financial_cache_company_report')

    op.drop_index('ix_codat_sync_history_status')
    op.drop_index('ix_codat_sync_history_data_type')
    op.drop_index('ix_codat_sync_history_company_id')

    op.drop_index('ix_codat_connections_status')
    op.drop_index('ix_codat_connections_company_id')

    op.drop_index('ix_codat_companies_platform')
    op.drop_index('ix_codat_companies_status')
    op.drop_index('ix_codat_companies_deal_id')

    # Drop tables
    op.drop_table('codat_webhook_events')
    op.drop_table('codat_bank_transactions_cache')
    op.drop_table('codat_invoices_cache')
    op.drop_table('codat_customers_cache')
    op.drop_table('codat_financial_cache')
    op.drop_table('codat_sync_history')
    op.drop_table('codat_connections')
    op.drop_table('codat_companies')
