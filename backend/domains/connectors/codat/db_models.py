"""
Database models for Codat integration.

Stores company connections, sync status, and cached financial data.
"""
from sqlalchemy import (
    Table,
    Column,
    ForeignKey,
    Boolean,
    Integer,
    String,
    JSON,
    Text,
    TIMESTAMP,
    DECIMAL,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from db.meta import METADATA


# Codat companies - our representation of Codat company records
codat_companies = Table(
    "codat_companies",
    METADATA,
    Column("id", UUID, primary_key=True),  # Our internal ID
    Column("codat_company_id", String(64), nullable=False, unique=True),  # Codat's ID
    Column("deal_id", UUID, ForeignKey("pe_deals.id", ondelete="SET NULL"), nullable=True),

    # Company info
    Column("name", String(255), nullable=False),
    Column("description", Text),

    # Status
    Column("status", String(32), nullable=False, server_default="pending"),
    # pending, connected, syncing, active, error, disconnected

    # Codat link info
    Column("link_url", Text),
    Column("redirect_url", Text),

    # Connection info (from primary data connection)
    Column("platform", String(64)),  # QuickBooks, Xero, etc.
    Column("platform_key", String(32)),  # gbol, gxer, etc.

    # Sync status
    Column("last_sync_requested", TIMESTAMP(timezone=True)),
    Column("last_sync_completed", TIMESTAMP(timezone=True)),
    Column("sync_status", String(32), server_default="never"),
    # never, queued, syncing, success, partial, error
    Column("sync_error", Text),

    # Cached summary metrics (updated after each sync)
    Column("total_revenue", DECIMAL(18, 2)),
    Column("total_assets", DECIMAL(18, 2)),
    Column("total_liabilities", DECIMAL(18, 2)),
    Column("total_customers", Integer),
    Column("data_currency", String(8), server_default="USD"),

    # Timestamps
    Column("codat_created_at", TIMESTAMP(timezone=True)),  # When created in Codat
    Column("created_at", TIMESTAMP(timezone=True), server_default=func.now()),
    Column("updated_at", TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now()),

    # Indexes
    Index("ix_codat_companies_deal_id", "deal_id"),
    Index("ix_codat_companies_status", "status"),
    Index("ix_codat_companies_platform", "platform"),
)


# Codat data connections - tracks individual platform connections
codat_connections = Table(
    "codat_connections",
    METADATA,
    Column("id", UUID, primary_key=True),
    Column("codat_connection_id", String(64), nullable=False, unique=True),
    Column("company_id", UUID, ForeignKey("codat_companies.id", ondelete="CASCADE"), nullable=False),

    # Connection details
    Column("platform_name", String(64), nullable=False),
    Column("integration_id", String(64)),
    Column("integration_key", String(32)),
    Column("source_id", String(64)),

    # Status
    Column("status", String(32), nullable=False),
    # PendingAuth, Linked, Unlinked, Deauthorized

    # Link info
    Column("link_url", Text),

    # Sync tracking
    Column("last_sync", TIMESTAMP(timezone=True)),
    Column("created", TIMESTAMP(timezone=True)),

    # Error tracking
    Column("error_message", Text),
    Column("error_details", JSON, server_default="{}"),

    # Timestamps
    Column("created_at", TIMESTAMP(timezone=True), server_default=func.now()),
    Column("updated_at", TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now()),

    # Indexes
    Index("ix_codat_connections_company_id", "company_id"),
    Index("ix_codat_connections_status", "status"),
)


# Data sync history - tracks each sync operation
codat_sync_history = Table(
    "codat_sync_history",
    METADATA,
    Column("id", UUID, primary_key=True),
    Column("company_id", UUID, ForeignKey("codat_companies.id", ondelete="CASCADE"), nullable=False),
    Column("connection_id", UUID, ForeignKey("codat_connections.id", ondelete="SET NULL")),

    # Sync details
    Column("codat_sync_id", String(64)),
    Column("data_type", String(64), nullable=False),
    # balanceSheet, profitAndLoss, invoices, customers, bankTransactions, etc.

    # Status
    Column("status", String(32), nullable=False),
    # queued, in_progress, success, error, not_supported

    # Results
    Column("records_synced", Integer),
    Column("error_message", Text),
    Column("details", JSON, server_default="{}"),

    # Timestamps
    Column("requested_at", TIMESTAMP(timezone=True), server_default=func.now()),
    Column("started_at", TIMESTAMP(timezone=True)),
    Column("completed_at", TIMESTAMP(timezone=True)),

    # Indexes
    Index("ix_codat_sync_history_company_id", "company_id"),
    Index("ix_codat_sync_history_data_type", "data_type"),
    Index("ix_codat_sync_history_status", "status"),
)


# Cached financial statements - store locally for faster access
codat_financial_cache = Table(
    "codat_financial_cache",
    METADATA,
    Column("id", UUID, primary_key=True),
    Column("company_id", UUID, ForeignKey("codat_companies.id", ondelete="CASCADE"), nullable=False),

    # Report type
    Column("report_type", String(32), nullable=False),  # balance_sheet, profit_and_loss

    # Period
    Column("period_start", TIMESTAMP(timezone=True)),
    Column("period_end", TIMESTAMP(timezone=True)),
    Column("period_length_months", Integer),

    # The full report data as JSON
    Column("report_data", JSON, nullable=False),

    # Currency
    Column("currency", String(8), server_default="USD"),

    # Summary metrics (for quick queries)
    Column("total_assets", DECIMAL(18, 2)),
    Column("total_liabilities", DECIMAL(18, 2)),
    Column("total_equity", DECIMAL(18, 2)),
    Column("total_revenue", DECIMAL(18, 2)),
    Column("gross_profit", DECIMAL(18, 2)),
    Column("net_profit", DECIMAL(18, 2)),

    # Timestamps
    Column("report_date", TIMESTAMP(timezone=True)),
    Column("synced_at", TIMESTAMP(timezone=True), server_default=func.now()),
    Column("created_at", TIMESTAMP(timezone=True), server_default=func.now()),

    # Indexes
    Index("ix_codat_financial_cache_company_report", "company_id", "report_type"),
    Index("ix_codat_financial_cache_period", "period_end"),
)


# Cached customers
codat_customers_cache = Table(
    "codat_customers_cache",
    METADATA,
    Column("id", UUID, primary_key=True),
    Column("company_id", UUID, ForeignKey("codat_companies.id", ondelete="CASCADE"), nullable=False),
    Column("codat_customer_id", String(64), nullable=False),

    # Customer info
    Column("customer_name", String(255), nullable=False),
    Column("contact_name", String(255)),
    Column("email", String(255)),
    Column("phone", String(64)),
    Column("default_currency", String(8), server_default="USD"),
    Column("status", String(32)),

    # Financial metrics
    Column("total_revenue", DECIMAL(18, 2)),
    Column("outstanding_balance", DECIMAL(18, 2)),
    Column("invoice_count", Integer),

    # Addresses as JSON
    Column("addresses", JSON, server_default="[]"),

    # Timestamps
    Column("source_modified_date", TIMESTAMP(timezone=True)),
    Column("synced_at", TIMESTAMP(timezone=True), server_default=func.now()),
    Column("created_at", TIMESTAMP(timezone=True), server_default=func.now()),
    Column("updated_at", TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now()),

    # Indexes
    Index("ix_codat_customers_cache_company_id", "company_id"),
    Index("ix_codat_customers_cache_codat_id", "codat_customer_id"),

    # Unique constraint on company + codat customer id
    Index("ix_codat_customers_cache_unique", "company_id", "codat_customer_id", unique=True),
)


# Cached invoices
codat_invoices_cache = Table(
    "codat_invoices_cache",
    METADATA,
    Column("id", UUID, primary_key=True),
    Column("company_id", UUID, ForeignKey("codat_companies.id", ondelete="CASCADE"), nullable=False),
    Column("codat_invoice_id", String(64), nullable=False),

    # Invoice info
    Column("invoice_number", String(64)),
    Column("customer_id", String(64)),
    Column("customer_name", String(255)),

    # Dates
    Column("issue_date", TIMESTAMP(timezone=True)),
    Column("due_date", TIMESTAMP(timezone=True)),
    Column("paid_on_date", TIMESTAMP(timezone=True)),

    # Amounts
    Column("currency", String(8), server_default="USD"),
    Column("sub_total", DECIMAL(18, 2)),
    Column("tax_amount", DECIMAL(18, 2)),
    Column("total_amount", DECIMAL(18, 2)),
    Column("amount_due", DECIMAL(18, 2)),

    # Status
    Column("status", String(32)),  # Draft, Submitted, PartiallyPaid, Paid, Void

    # Line items as JSON
    Column("line_items", JSON, server_default="[]"),

    # Timestamps
    Column("source_modified_date", TIMESTAMP(timezone=True)),
    Column("synced_at", TIMESTAMP(timezone=True), server_default=func.now()),
    Column("created_at", TIMESTAMP(timezone=True), server_default=func.now()),
    Column("updated_at", TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now()),

    # Indexes
    Index("ix_codat_invoices_cache_company_id", "company_id"),
    Index("ix_codat_invoices_cache_customer_id", "customer_id"),
    Index("ix_codat_invoices_cache_status", "status"),
    Index("ix_codat_invoices_cache_issue_date", "issue_date"),

    # Unique constraint
    Index("ix_codat_invoices_cache_unique", "company_id", "codat_invoice_id", unique=True),
)


# Cached bank transactions
codat_bank_transactions_cache = Table(
    "codat_bank_transactions_cache",
    METADATA,
    Column("id", UUID, primary_key=True),
    Column("company_id", UUID, ForeignKey("codat_companies.id", ondelete="CASCADE"), nullable=False),
    Column("codat_transaction_id", String(64), nullable=False),

    # Transaction info
    Column("account_id", String(64)),
    Column("account_name", String(255)),
    Column("date", TIMESTAMP(timezone=True)),
    Column("description", Text),

    # Amount
    Column("amount", DECIMAL(18, 2)),
    Column("currency", String(8), server_default="USD"),
    Column("transaction_type", String(32)),  # Credit, Debit

    # Categorization
    Column("category", String(255)),
    Column("merchant_name", String(255)),

    # Reconciliation
    Column("reconciled", Boolean, server_default="false"),

    # Timestamps
    Column("source_modified_date", TIMESTAMP(timezone=True)),
    Column("synced_at", TIMESTAMP(timezone=True), server_default=func.now()),
    Column("created_at", TIMESTAMP(timezone=True), server_default=func.now()),

    # Indexes
    Index("ix_codat_bank_transactions_company_id", "company_id"),
    Index("ix_codat_bank_transactions_account_id", "account_id"),
    Index("ix_codat_bank_transactions_date", "date"),
    Index("ix_codat_bank_transactions_type", "transaction_type"),

    # Unique constraint
    Index("ix_codat_bank_transactions_unique", "company_id", "codat_transaction_id", unique=True),
)


# Codat webhook events - log all incoming webhooks
codat_webhook_events = Table(
    "codat_webhook_events",
    METADATA,
    Column("id", UUID, primary_key=True),

    # Event info
    Column("codat_event_id", String(64)),
    Column("event_type", String(64), nullable=False),
    Column("company_id", String(64)),
    Column("connection_id", String(64)),

    # Raw payload
    Column("payload", JSON, nullable=False),

    # Processing status
    Column("processed", Boolean, server_default="false"),
    Column("processed_at", TIMESTAMP(timezone=True)),
    Column("processing_error", Text),

    # Timestamps
    Column("received_at", TIMESTAMP(timezone=True), server_default=func.now()),

    # Indexes
    Index("ix_codat_webhook_events_type", "event_type"),
    Index("ix_codat_webhook_events_company", "company_id"),
    Index("ix_codat_webhook_events_processed", "processed"),
)
