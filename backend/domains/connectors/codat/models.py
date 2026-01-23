"""
Codat Integration Models

Pydantic schemas for Codat API requests/responses and normalized financial data.
"""
from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class CodatDataType(str, Enum):
    """Data types available from Codat."""
    BALANCE_SHEET = "balanceSheet"
    PROFIT_AND_LOSS = "profitAndLoss"
    INVOICES = "invoices"
    CUSTOMERS = "customers"
    SUPPLIERS = "suppliers"
    BANK_TRANSACTIONS = "bankTransactions"
    BANK_ACCOUNTS = "bankAccounts"
    PAYMENTS = "payments"
    BILLS = "bills"
    ACCOUNTS = "accounts"
    JOURNAL_ENTRIES = "journalEntries"
    ITEMS = "items"


class CodatPlatform(str, Enum):
    """Supported accounting platforms."""
    QUICKBOOKS_ONLINE = "gbol"
    QUICKBOOKS_DESKTOP = "qhyp"
    XERO = "gxer"
    SAGE = "wvks"
    NETSUITE = "akxx"
    FRESHBOOKS = "vqzp"
    WAVE = "wavo"
    ZOHO_BOOKS = "rwuv"
    MYOB = "pdvj"


class CodatConnectionStatus(str, Enum):
    """Connection status."""
    PENDING_AUTH = "PendingAuth"
    LINKED = "Linked"
    UNLINKED = "Unlinked"
    DEAUTHORIZED = "Deauthorized"


class CodatSyncStatus(str, Enum):
    """Data sync status."""
    QUEUED = "Queued"
    IN_PROGRESS = "InProgress"
    SUCCESS = "Success"
    ERROR = "Error"
    NOT_SUPPORTED = "NotSupported"


# --- Company & Connection Models ---

class CodatCompanyCreate(BaseModel):
    """Request to create a Codat company."""
    name: str
    deal_id: Optional[str] = None
    description: Optional[str] = None


class CodatCompany(BaseModel):
    """Codat company response."""
    id: str
    name: str
    platform: Optional[str] = None
    redirect: Optional[str] = None
    last_sync: Optional[datetime] = None
    data_connections: List["CodatConnection"] = Field(default_factory=list)
    created: Optional[datetime] = None

    class Config:
        from_attributes = True


class CodatConnection(BaseModel):
    """Codat data connection."""
    id: str
    integration_id: str
    integration_key: str
    source_id: str
    platform_name: str
    link_url: str
    status: CodatConnectionStatus
    last_sync: Optional[datetime] = None
    created: Optional[datetime] = None
    data_connection_errors: List[Dict[str, Any]] = Field(default_factory=list)

    class Config:
        from_attributes = True


class CodatLinkResponse(BaseModel):
    """Response with link URL for OAuth."""
    company_id: str
    link_url: str


class CodatSyncResult(BaseModel):
    """Result from data sync operation."""
    company_id: str
    data_type: CodatDataType
    sync_id: str
    status: CodatSyncStatus
    message: Optional[str] = None
    records_synced: Optional[int] = None
    completed_on_utc: Optional[datetime] = None


# --- Financial Statement Models ---

class ReportItem(BaseModel):
    """Item in a financial report."""
    name: str
    value: Decimal = Field(default=Decimal(0))
    account_id: Optional[str] = None
    items: List["ReportItem"] = Field(default_factory=list)


class BalanceSheetLine(BaseModel):
    """Line item in balance sheet."""
    name: str
    value: Decimal = Field(default=Decimal(0))
    account_id: Optional[str] = None
    sub_items: List["BalanceSheetLine"] = Field(default_factory=list)


class BalanceSheet(BaseModel):
    """Balance sheet report."""
    company_id: str
    report_date: date
    currency: str = "USD"

    # Assets
    assets: List[BalanceSheetLine] = Field(default_factory=list)
    total_assets: Decimal = Field(default=Decimal(0))

    # Liabilities
    liabilities: List[BalanceSheetLine] = Field(default_factory=list)
    total_liabilities: Decimal = Field(default=Decimal(0))

    # Equity
    equity: List[BalanceSheetLine] = Field(default_factory=list)
    total_equity: Decimal = Field(default=Decimal(0))

    # Net assets (should equal total equity)
    net_assets: Decimal = Field(default=Decimal(0))

    generated_at: datetime = Field(default_factory=datetime.utcnow)


class ProfitAndLossLine(BaseModel):
    """Line item in P&L."""
    name: str
    value: Decimal = Field(default=Decimal(0))
    account_id: Optional[str] = None
    sub_items: List["ProfitAndLossLine"] = Field(default_factory=list)


class ProfitAndLoss(BaseModel):
    """Profit and Loss statement."""
    company_id: str
    from_date: date
    to_date: date
    currency: str = "USD"

    # Revenue/Income
    income: List[ProfitAndLossLine] = Field(default_factory=list)
    total_income: Decimal = Field(default=Decimal(0))

    # Cost of Sales
    cost_of_sales: List[ProfitAndLossLine] = Field(default_factory=list)
    total_cost_of_sales: Decimal = Field(default=Decimal(0))

    # Gross Profit
    gross_profit: Decimal = Field(default=Decimal(0))

    # Operating Expenses
    expenses: List[ProfitAndLossLine] = Field(default_factory=list)
    total_expenses: Decimal = Field(default=Decimal(0))

    # Operating Profit
    operating_profit: Decimal = Field(default=Decimal(0))

    # Other Income/Expenses
    other_income: Decimal = Field(default=Decimal(0))
    other_expenses: Decimal = Field(default=Decimal(0))

    # Net Profit
    net_profit: Decimal = Field(default=Decimal(0))

    generated_at: datetime = Field(default_factory=datetime.utcnow)


# --- Transactional Models ---

class Address(BaseModel):
    """Address information."""
    line1: Optional[str] = None
    line2: Optional[str] = None
    city: Optional[str] = None
    region: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None


class Contact(BaseModel):
    """Contact information."""
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None


class Customer(BaseModel):
    """Customer record."""
    id: str
    company_id: str
    customer_name: str
    contact_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    addresses: List[Address] = Field(default_factory=list)
    default_currency: str = "USD"
    status: str = "Active"

    # Financial metrics (calculated)
    total_revenue: Optional[Decimal] = None
    outstanding_balance: Optional[Decimal] = None
    invoice_count: Optional[int] = None

    modified_date: Optional[datetime] = None
    source_modified_date: Optional[datetime] = None


class InvoiceLineItem(BaseModel):
    """Line item on an invoice."""
    description: Optional[str] = None
    unit_amount: Decimal = Field(default=Decimal(0))
    quantity: Decimal = Field(default=Decimal(1))
    discount_amount: Decimal = Field(default=Decimal(0))
    tax_amount: Decimal = Field(default=Decimal(0))
    total_amount: Decimal = Field(default=Decimal(0))
    account_ref: Optional[str] = None
    item_ref: Optional[str] = None


class Invoice(BaseModel):
    """Invoice record."""
    id: str
    company_id: str
    invoice_number: Optional[str] = None
    customer_ref: Optional[str] = None
    customer_name: Optional[str] = None
    issue_date: date
    due_date: Optional[date] = None
    paid_on_date: Optional[date] = None
    currency: str = "USD"

    # Amounts
    sub_total: Decimal = Field(default=Decimal(0))
    tax_amount: Decimal = Field(default=Decimal(0))
    total_amount: Decimal = Field(default=Decimal(0))
    amount_due: Decimal = Field(default=Decimal(0))

    # Status
    status: str = "Submitted"  # Draft, Submitted, PartiallyPaid, Paid, Void

    # Line items
    line_items: List[InvoiceLineItem] = Field(default_factory=list)

    # Payment info
    payments: List[Dict[str, Any]] = Field(default_factory=list)

    modified_date: Optional[datetime] = None
    source_modified_date: Optional[datetime] = None


class BankAccount(BaseModel):
    """Bank account record."""
    id: str
    company_id: str
    account_name: str
    account_type: str  # Credit, Debit, Loan, etc.
    account_number: Optional[str] = None
    currency: str = "USD"
    current_balance: Optional[Decimal] = None
    available_balance: Optional[Decimal] = None
    institution: Optional[str] = None
    status: str = "Active"  # Active, Archived, Unknown
    modified_date: Optional[datetime] = None


class BankTransaction(BaseModel):
    """Bank transaction record."""
    id: str
    company_id: str
    account_id: str
    account_name: Optional[str] = None
    date: date
    description: Optional[str] = None
    amount: Decimal
    currency: str = "USD"
    transaction_type: str  # Credit, Debit

    # Categorization
    category: Optional[str] = None
    merchant_name: Optional[str] = None

    # Reconciliation
    reconciled: bool = False

    modified_date: Optional[datetime] = None
    source_modified_date: Optional[datetime] = None


# --- Summary Models ---

class AccountingSummary(BaseModel):
    """Summary of accounting data."""
    company_id: str
    company_name: str
    platform: Optional[str] = None
    currency: str = "USD"

    # Financial summary
    total_revenue_ytd: Optional[Decimal] = None
    total_expenses_ytd: Optional[Decimal] = None
    net_income_ytd: Optional[Decimal] = None

    total_assets: Optional[Decimal] = None
    total_liabilities: Optional[Decimal] = None
    total_equity: Optional[Decimal] = None

    # Customer summary
    total_customers: Optional[int] = None
    total_receivables: Optional[Decimal] = None
    average_invoice_amount: Optional[Decimal] = None

    # Bank summary
    total_bank_balance: Optional[Decimal] = None
    bank_accounts_count: Optional[int] = None

    # Data freshness
    last_sync: Optional[datetime] = None
    data_as_of: Optional[date] = None

    generated_at: datetime = Field(default_factory=datetime.utcnow)


# --- Webhook Models ---

class CodatWebhookEvent(BaseModel):
    """Codat webhook event."""
    id: str
    type: str  # DatasetStatusHasChanged, DataConnectionStatusChanged, etc.
    company_id: str
    data_connection_id: Optional[str] = None
    data: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime


class CodatDatasetStatus(BaseModel):
    """Status of a dataset sync."""
    data_type: str
    status: CodatSyncStatus
    error_message: Optional[str] = None


# --- Request/Response Models ---

class SyncRequest(BaseModel):
    """Request to sync specific data types."""
    data_types: List[CodatDataType] = Field(
        default_factory=lambda: [
            CodatDataType.BALANCE_SHEET,
            CodatDataType.PROFIT_AND_LOSS,
            CodatDataType.INVOICES,
            CodatDataType.CUSTOMERS,
        ]
    )


class FinancialPeriod(BaseModel):
    """Financial reporting period."""
    period_start: date
    period_end: date
    period_length: int = 12  # months


# Update forward references
ReportItem.model_rebuild()
BalanceSheetLine.model_rebuild()
ProfitAndLossLine.model_rebuild()
CodatCompany.model_rebuild()
