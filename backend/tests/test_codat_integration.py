"""
Unit tests for Codat Integration

Tests for Codat connector service, models, and API endpoints.
"""
from datetime import datetime, date, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from domains.connectors.codat.models import (
    CodatCompany,
    CodatCompanyCreate,
    CodatConnection,
    CodatConnectionStatus,
    CodatDataType,
    CodatLinkResponse,
    CodatSyncResult,
    CodatSyncStatus,
    BalanceSheet,
    BalanceSheetLine,
    ProfitAndLoss,
    ProfitAndLossLine,
    Invoice,
    InvoiceLineItem,
    Customer,
    BankAccount,
    BankTransaction,
    AccountingSummary,
    CodatPlatform,
)
from domains.connectors.codat.service import (
    CodatService,
    CodatServiceError,
    CodatAuthError,
    CodatAPIError,
)


class TestCodatModels:
    """Tests for Codat Pydantic models."""

    def test_codat_company_create(self):
        """Test company creation model."""
        company = CodatCompanyCreate(
            name="Test Company",
            deal_id="deal-123",
            description="Test description",
        )
        assert company.name == "Test Company"
        assert company.deal_id == "deal-123"
        assert company.description == "Test description"

    def test_codat_company_response(self):
        """Test company response model."""
        company = CodatCompany(
            id="comp-123",
            name="Test Company",
            platform="QuickBooks",
            redirect="https://link.codat.io/company/comp-123",
            created=datetime.now(),
        )
        assert company.id == "comp-123"
        assert company.name == "Test Company"
        assert company.platform == "QuickBooks"
        assert company.data_connections == []

    def test_codat_connection(self):
        """Test connection model."""
        conn = CodatConnection(
            id="conn-123",
            integration_id="int-123",
            integration_key="gbol",
            source_id="src-123",
            platform_name="QuickBooks Online",
            link_url="https://link.codat.io/...",
            status=CodatConnectionStatus.LINKED,
            last_sync=datetime.now(),
        )
        assert conn.status == CodatConnectionStatus.LINKED
        assert conn.platform_name == "QuickBooks Online"

    def test_balance_sheet_model(self):
        """Test balance sheet model."""
        bs = BalanceSheet(
            company_id="comp-123",
            report_date=date.today(),
            currency="USD",
            assets=[
                BalanceSheetLine(
                    name="Current Assets",
                    value=Decimal("100000"),
                    sub_items=[
                        BalanceSheetLine(name="Cash", value=Decimal("50000")),
                        BalanceSheetLine(name="Receivables", value=Decimal("50000")),
                    ],
                ),
            ],
            total_assets=Decimal("100000"),
            liabilities=[
                BalanceSheetLine(name="Current Liabilities", value=Decimal("30000")),
            ],
            total_liabilities=Decimal("30000"),
            equity=[
                BalanceSheetLine(name="Retained Earnings", value=Decimal("70000")),
            ],
            total_equity=Decimal("70000"),
            net_assets=Decimal("70000"),
        )
        assert bs.total_assets == Decimal("100000")
        assert bs.total_liabilities == Decimal("30000")
        assert bs.net_assets == Decimal("70000")

    def test_profit_and_loss_model(self):
        """Test P&L model."""
        pnl = ProfitAndLoss(
            company_id="comp-123",
            from_date=date.today() - timedelta(days=365),
            to_date=date.today(),
            currency="USD",
            income=[
                ProfitAndLossLine(name="Sales", value=Decimal("500000")),
            ],
            total_income=Decimal("500000"),
            cost_of_sales=[
                ProfitAndLossLine(name="COGS", value=Decimal("200000")),
            ],
            total_cost_of_sales=Decimal("200000"),
            gross_profit=Decimal("300000"),
            expenses=[
                ProfitAndLossLine(name="Operating Expenses", value=Decimal("150000")),
            ],
            total_expenses=Decimal("150000"),
            operating_profit=Decimal("150000"),
            net_profit=Decimal("150000"),
        )
        assert pnl.total_income == Decimal("500000")
        assert pnl.gross_profit == Decimal("300000")
        assert pnl.net_profit == Decimal("150000")

    def test_invoice_model(self):
        """Test invoice model."""
        invoice = Invoice(
            id="inv-123",
            company_id="comp-123",
            invoice_number="INV-001",
            customer_ref="cust-123",
            customer_name="Test Customer",
            issue_date=date.today(),
            due_date=date.today() + timedelta(days=30),
            currency="USD",
            sub_total=Decimal("1000"),
            tax_amount=Decimal("100"),
            total_amount=Decimal("1100"),
            amount_due=Decimal("1100"),
            status="Submitted",
            line_items=[
                InvoiceLineItem(
                    description="Service",
                    unit_amount=Decimal("500"),
                    quantity=Decimal("2"),
                    total_amount=Decimal("1000"),
                ),
            ],
        )
        assert invoice.total_amount == Decimal("1100")
        assert len(invoice.line_items) == 1
        assert invoice.status == "Submitted"

    def test_customer_model(self):
        """Test customer model."""
        customer = Customer(
            id="cust-123",
            company_id="comp-123",
            customer_name="Test Customer Inc.",
            contact_name="John Doe",
            email="john@test.com",
            phone="+1-555-1234",
            default_currency="USD",
            status="Active",
            total_revenue=Decimal("50000"),
            outstanding_balance=Decimal("5000"),
            invoice_count=10,
        )
        assert customer.customer_name == "Test Customer Inc."
        assert customer.total_revenue == Decimal("50000")

    def test_bank_transaction_model(self):
        """Test bank transaction model."""
        txn = BankTransaction(
            id="txn-123",
            company_id="comp-123",
            account_id="acct-123",
            account_name="Business Checking",
            date=date.today(),
            description="Payment received",
            amount=Decimal("1500.00"),
            currency="USD",
            transaction_type="Credit",
            category="Sales",
            reconciled=False,
        )
        assert txn.amount == Decimal("1500.00")
        assert txn.transaction_type == "Credit"

    def test_accounting_summary_model(self):
        """Test accounting summary model."""
        summary = AccountingSummary(
            company_id="comp-123",
            company_name="Test Company",
            platform="QuickBooks Online",
            currency="USD",
            total_revenue_ytd=Decimal("500000"),
            total_expenses_ytd=Decimal("350000"),
            net_income_ytd=Decimal("150000"),
            total_assets=Decimal("200000"),
            total_liabilities=Decimal("80000"),
            total_equity=Decimal("120000"),
            total_customers=50,
            total_receivables=Decimal("25000"),
            average_invoice_amount=Decimal("5000"),
            total_bank_balance=Decimal("75000"),
            bank_accounts_count=2,
            last_sync=datetime.now(),
            data_as_of=date.today(),
        )
        assert summary.net_income_ytd == Decimal("150000")
        assert summary.total_customers == 50

    def test_codat_data_type_enum(self):
        """Test data type enum values."""
        assert CodatDataType.BALANCE_SHEET.value == "balanceSheet"
        assert CodatDataType.PROFIT_AND_LOSS.value == "profitAndLoss"
        assert CodatDataType.INVOICES.value == "invoices"
        assert CodatDataType.CUSTOMERS.value == "customers"

    def test_codat_platform_enum(self):
        """Test platform enum values."""
        assert CodatPlatform.QUICKBOOKS_ONLINE.value == "gbol"
        assert CodatPlatform.XERO.value == "gxer"
        assert CodatPlatform.SAGE.value == "wvks"


class TestCodatService:
    """Tests for Codat service."""

    @pytest.fixture
    def mock_service(self):
        """Create service with mocked HTTP client."""
        service = CodatService(api_key="test-api-key")
        return service

    def test_service_initialization(self):
        """Test service initialization."""
        service = CodatService(api_key="test-key")
        assert service.api_key == "test-key"
        assert service.is_configured is True

    def test_service_not_configured(self):
        """Test service without API key."""
        service = CodatService(api_key=None)
        assert service.is_configured is False

    @pytest.mark.asyncio
    async def test_create_company_success(self, mock_service):
        """Test successful company creation."""
        mock_response = {
            "id": "comp-123",
            "name": "Test Company",
            "redirect": "https://link.codat.io/company/comp-123",
            "created": "2024-01-01T00:00:00Z",
        }

        with patch.object(mock_service, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            company = await mock_service.create_company(
                name="Test Company",
                deal_id="deal-123",
            )

            assert company.id == "comp-123"
            assert company.name == "Test Company"
            mock_request.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_company_success(self, mock_service):
        """Test getting company details."""
        mock_response = {
            "id": "comp-123",
            "name": "Test Company",
            "platform": "QuickBooks",
            "redirect": "https://link.codat.io/company/comp-123",
            "lastSync": "2024-01-15T10:00:00Z",
            "created": "2024-01-01T00:00:00Z",
            "dataConnections": [
                {
                    "id": "conn-123",
                    "integrationId": "int-123",
                    "integrationKey": "gbol",
                    "sourceId": "src-123",
                    "platformName": "QuickBooks Online",
                    "linkUrl": "https://...",
                    "status": "Linked",
                    "lastSync": "2024-01-15T10:00:00Z",
                    "created": "2024-01-01T00:00:00Z",
                },
            ],
        }

        with patch.object(mock_service, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            company = await mock_service.get_company("comp-123")

            assert company.id == "comp-123"
            assert len(company.data_connections) == 1
            assert company.data_connections[0].status == CodatConnectionStatus.LINKED

    @pytest.mark.asyncio
    async def test_list_companies(self, mock_service):
        """Test listing companies."""
        mock_response = {
            "results": [
                {"id": "comp-1", "name": "Company 1", "created": "2024-01-01T00:00:00Z"},
                {"id": "comp-2", "name": "Company 2", "created": "2024-01-02T00:00:00Z"},
            ],
        }

        with patch.object(mock_service, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            companies = await mock_service.list_companies()

            assert len(companies) == 2
            assert companies[0].id == "comp-1"
            assert companies[1].id == "comp-2"

    @pytest.mark.asyncio
    async def test_get_link_url(self, mock_service):
        """Test getting link URL."""
        mock_company = {
            "id": "comp-123",
            "name": "Test Company",
            "redirect": "https://link.codat.io/company/comp-123",
            "created": "2024-01-01T00:00:00Z",
            "dataConnections": [],
        }

        with patch.object(mock_service, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_company

            link = await mock_service.get_link_url("comp-123")

            assert link.company_id == "comp-123"
            assert "link.codat.io" in link.link_url

    @pytest.mark.asyncio
    async def test_sync_data(self, mock_service):
        """Test triggering data sync."""
        mock_response = {"id": "sync-123"}

        with patch.object(mock_service, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            results = await mock_service.sync_data(
                "comp-123",
                [CodatDataType.BALANCE_SHEET, CodatDataType.PROFIT_AND_LOSS],
            )

            assert len(results) == 2
            assert all(r.status == CodatSyncStatus.QUEUED for r in results)

    @pytest.mark.asyncio
    async def test_get_balance_sheet(self, mock_service):
        """Test getting balance sheet."""
        mock_response = {
            "reports": [
                {
                    "date": "2024-01-31",
                    "items": [
                        {
                            "name": "Assets",
                            "items": [
                                {"name": "Cash", "value": 50000},
                                {"name": "Receivables", "value": 30000},
                            ],
                        },
                        {
                            "name": "Liabilities",
                            "items": [
                                {"name": "Payables", "value": 20000},
                            ],
                        },
                        {
                            "name": "Equity",
                            "items": [
                                {"name": "Retained Earnings", "value": 60000},
                            ],
                        },
                    ],
                },
            ],
            "currency": "USD",
        }

        with patch.object(mock_service, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            bs = await mock_service.get_balance_sheet("comp-123")

            assert bs.company_id == "comp-123"
            assert bs.currency == "USD"
            assert bs.total_assets == Decimal("80000")

    @pytest.mark.asyncio
    async def test_get_profit_and_loss(self, mock_service):
        """Test getting P&L."""
        mock_response = {
            "reports": [
                {
                    "fromDate": "2023-01-01",
                    "toDate": "2023-12-31",
                    "items": [
                        {
                            "name": "Income",
                            "items": [
                                {"name": "Sales", "value": 100000},
                            ],
                        },
                        {
                            "name": "COGS",
                            "items": [
                                {"name": "Cost of Goods", "value": 40000},
                            ],
                        },
                        {
                            "name": "Operating Expenses",
                            "items": [
                                {"name": "Rent", "value": 12000},
                                {"name": "Salaries", "value": 30000},
                            ],
                        },
                    ],
                },
            ],
            "currency": "USD",
        }

        with patch.object(mock_service, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            pnl = await mock_service.get_profit_and_loss("comp-123")

            assert pnl.company_id == "comp-123"
            assert pnl.total_income == Decimal("100000")
            assert pnl.total_cost_of_sales == Decimal("40000")
            assert pnl.gross_profit == Decimal("60000")

    @pytest.mark.asyncio
    async def test_get_invoices(self, mock_service):
        """Test getting invoices."""
        mock_response = {
            "results": [
                {
                    "id": "inv-1",
                    "invoiceNumber": "INV-001",
                    "issueDate": "2024-01-15",
                    "dueDate": "2024-02-15",
                    "totalAmount": 1000,
                    "amountDue": 1000,
                    "status": "Submitted",
                    "currency": "USD",
                    "lineItems": [],
                },
                {
                    "id": "inv-2",
                    "invoiceNumber": "INV-002",
                    "issueDate": "2024-01-20",
                    "totalAmount": 2500,
                    "amountDue": 0,
                    "status": "Paid",
                    "currency": "USD",
                    "lineItems": [],
                },
            ],
        }

        with patch.object(mock_service, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            invoices = await mock_service.get_invoices("comp-123")

            assert len(invoices) == 2
            assert invoices[0].invoice_number == "INV-001"
            assert invoices[1].status == "Paid"

    @pytest.mark.asyncio
    async def test_get_customers(self, mock_service):
        """Test getting customers."""
        mock_response = {
            "results": [
                {
                    "id": "cust-1",
                    "customerName": "Customer One",
                    "emailAddress": "one@test.com",
                    "status": "Active",
                    "defaultCurrency": "USD",
                },
                {
                    "id": "cust-2",
                    "customerName": "Customer Two",
                    "emailAddress": "two@test.com",
                    "status": "Active",
                    "defaultCurrency": "USD",
                },
            ],
        }

        with patch.object(mock_service, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            customers = await mock_service.get_customers("comp-123")

            assert len(customers) == 2
            assert customers[0].customer_name == "Customer One"
            assert customers[0].email == "one@test.com"

    @pytest.mark.asyncio
    async def test_get_bank_accounts(self, mock_service):
        """Test getting bank accounts."""
        mock_response = {
            "results": [
                {
                    "id": "acct-1",
                    "accountName": "Business Checking",
                    "accountType": "Debit",
                    "currency": "USD",
                    "balance": 50000,
                    "status": "Active",
                },
            ],
        }

        with patch.object(mock_service, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            accounts = await mock_service.get_bank_accounts("comp-123")

            assert len(accounts) == 1
            assert accounts[0].account_name == "Business Checking"
            assert accounts[0].current_balance == Decimal("50000")

    @pytest.mark.asyncio
    async def test_get_bank_transactions(self, mock_service):
        """Test getting bank transactions."""
        mock_response = {
            "results": [
                {
                    "id": "txn-1",
                    "accountId": "acct-1",
                    "date": "2024-01-15",
                    "description": "Customer payment",
                    "amount": 1500,
                    "currency": "USD",
                    "transactionType": "Credit",
                    "reconciled": False,
                },
                {
                    "id": "txn-2",
                    "accountId": "acct-1",
                    "date": "2024-01-16",
                    "description": "Office supplies",
                    "amount": -250,
                    "currency": "USD",
                    "transactionType": "Debit",
                    "reconciled": True,
                },
            ],
        }

        with patch.object(mock_service, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            transactions = await mock_service.get_bank_transactions("comp-123")

            assert len(transactions) == 2
            assert transactions[0].description == "Customer payment"
            assert transactions[0].transaction_type == "Credit"


class TestCodatServiceErrors:
    """Tests for error handling."""

    @pytest.fixture
    def service(self):
        return CodatService(api_key="test-key")

    @pytest.mark.asyncio
    async def test_auth_error_no_key(self):
        """Test error when no API key configured."""
        service = CodatService(api_key=None)

        with pytest.raises(CodatAuthError):
            await service._request("GET", "/companies")

    @pytest.mark.asyncio
    async def test_api_error_handling(self, service):
        """Test API error handling."""
        import httpx

        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.content = b'{"message": "Not found"}'
        mock_response.json.return_value = {"message": "Not found"}

        with patch.object(service, '_get_client', new_callable=AsyncMock) as mock_get_client:
            mock_client = AsyncMock()
            mock_client.request = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client

            with pytest.raises(CodatAPIError) as exc_info:
                await service._request("GET", "/companies/invalid")

            assert exc_info.value.status_code == 404


class TestSyncStatusEnum:
    """Tests for sync status enum."""

    def test_sync_status_values(self):
        """Test sync status enum values."""
        assert CodatSyncStatus.QUEUED.value == "Queued"
        assert CodatSyncStatus.IN_PROGRESS.value == "InProgress"
        assert CodatSyncStatus.SUCCESS.value == "Success"
        assert CodatSyncStatus.ERROR.value == "Error"

    def test_connection_status_values(self):
        """Test connection status enum values."""
        assert CodatConnectionStatus.PENDING_AUTH.value == "PendingAuth"
        assert CodatConnectionStatus.LINKED.value == "Linked"
        assert CodatConnectionStatus.UNLINKED.value == "Unlinked"


class TestBalanceSheetCalculations:
    """Tests for balance sheet calculations."""

    def test_sum_nested_items(self):
        """Test summing nested balance sheet items."""
        bs = BalanceSheet(
            company_id="test",
            report_date=date.today(),
            assets=[
                BalanceSheetLine(
                    name="Current Assets",
                    value=Decimal("0"),  # Parent value is 0
                    sub_items=[
                        BalanceSheetLine(name="Cash", value=Decimal("10000")),
                        BalanceSheetLine(name="AR", value=Decimal("5000")),
                    ],
                ),
                BalanceSheetLine(
                    name="Fixed Assets",
                    value=Decimal("20000"),
                ),
            ],
            total_assets=Decimal("35000"),  # Sum of all
        )

        # Calculate sum of assets including sub_items
        total = Decimal("0")
        for asset in bs.assets:
            total += asset.value
            for sub in asset.sub_items:
                total += sub.value

        assert total == Decimal("35000")


class TestFinancialSummary:
    """Tests for financial summary generation."""

    @pytest.mark.asyncio
    async def test_accounting_summary_aggregation(self):
        """Test that accounting summary aggregates data correctly."""
        service = CodatService(api_key="test-key")

        # Mock all dependent calls
        mock_company = CodatCompany(
            id="comp-123",
            name="Test Company",
            data_connections=[
                CodatConnection(
                    id="conn-1",
                    integration_id="int-1",
                    integration_key="gbol",
                    source_id="src-1",
                    platform_name="QuickBooks Online",
                    link_url="",
                    status=CodatConnectionStatus.LINKED,
                ),
            ],
        )

        mock_bs = BalanceSheet(
            company_id="comp-123",
            report_date=date.today(),
            currency="USD",
            total_assets=Decimal("100000"),
            total_liabilities=Decimal("40000"),
            total_equity=Decimal("60000"),
        )

        mock_pnl = ProfitAndLoss(
            company_id="comp-123",
            from_date=date.today() - timedelta(days=365),
            to_date=date.today(),
            total_income=Decimal("500000"),
            total_expenses=Decimal("350000"),
            net_profit=Decimal("150000"),
        )

        mock_customers = [
            Customer(id="c1", company_id="comp-123", customer_name="Cust 1"),
            Customer(id="c2", company_id="comp-123", customer_name="Cust 2"),
        ]

        mock_invoices = [
            Invoice(
                id="inv-1",
                company_id="comp-123",
                issue_date=date.today(),
                total_amount=Decimal("1000"),
                amount_due=Decimal("500"),
            ),
        ]

        mock_bank_accounts = [
            BankAccount(
                id="acct-1",
                company_id="comp-123",
                account_name="Checking",
                account_type="Debit",
                current_balance=Decimal("25000"),
            ),
        ]

        with patch.object(service, 'get_company', new_callable=AsyncMock) as mock_get_company, \
             patch.object(service, 'get_balance_sheet', new_callable=AsyncMock) as mock_get_bs, \
             patch.object(service, 'get_profit_and_loss', new_callable=AsyncMock) as mock_get_pnl, \
             patch.object(service, 'get_customers', new_callable=AsyncMock) as mock_get_cust, \
             patch.object(service, 'get_invoices', new_callable=AsyncMock) as mock_get_inv, \
             patch.object(service, 'get_bank_accounts', new_callable=AsyncMock) as mock_get_bank:

            mock_get_company.return_value = mock_company
            mock_get_bs.return_value = mock_bs
            mock_get_pnl.return_value = mock_pnl
            mock_get_cust.return_value = mock_customers
            mock_get_inv.return_value = mock_invoices
            mock_get_bank.return_value = mock_bank_accounts

            summary = await service.get_accounting_summary("comp-123")

            assert summary.company_id == "comp-123"
            assert summary.company_name == "Test Company"
            assert summary.platform == "QuickBooks Online"
            assert summary.total_revenue_ytd == Decimal("500000")
            assert summary.net_income_ytd == Decimal("150000")
            assert summary.total_assets == Decimal("100000")
            assert summary.total_customers == 2
            assert summary.total_receivables == Decimal("500")
            assert summary.total_bank_balance == Decimal("25000")
            assert summary.bank_accounts_count == 1
