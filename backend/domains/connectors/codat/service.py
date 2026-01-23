"""
Codat Connector Service

Handles integration with Codat API for accounting system data:
- Company creation and linking
- OAuth flow management
- Data synchronization
- Financial data retrieval
"""
import logging
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import UUID

import httpx

from core.config import settings
from .models import (
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
    BankTransaction,
    BankAccount,
    AccountingSummary,
)

logger = logging.getLogger(__name__)


class CodatServiceError(Exception):
    """Base exception for Codat service errors."""
    pass


class CodatAuthError(CodatServiceError):
    """Authentication error with Codat API."""
    pass


class CodatAPIError(CodatServiceError):
    """Error from Codat API."""
    def __init__(self, message: str, status_code: int = None, response: dict = None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class CodatService:
    """
    Service for interacting with Codat API.

    Codat provides unified access to accounting platforms like:
    - QuickBooks Online/Desktop
    - Xero
    - Sage
    - NetSuite
    - FreshBooks
    - Wave
    - Zoho Books
    - MYOB
    """

    BASE_URL = "https://api.codat.io"

    def __init__(self, api_key: str = None):
        """
        Initialize Codat service.

        Args:
            api_key: Codat API key. If not provided, reads from settings.
        """
        self.api_key = api_key or getattr(settings, 'codat_api_key', None)
        if not self.api_key:
            logger.warning("Codat API key not configured - service will run in mock mode")

        self._client: Optional[httpx.AsyncClient] = None

    @property
    def is_configured(self) -> bool:
        """Check if Codat is properly configured."""
        return bool(self.api_key)

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.BASE_URL,
                headers={
                    "Authorization": f"Basic {self.api_key}",
                    "Content-Type": "application/json",
                },
                timeout=30.0,
            )
        return self._client

    async def close(self):
        """Close HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def _request(
        self,
        method: str,
        endpoint: str,
        data: dict = None,
        params: dict = None,
    ) -> dict:
        """
        Make authenticated request to Codat API.

        Args:
            method: HTTP method
            endpoint: API endpoint
            data: Request body
            params: Query parameters

        Returns:
            Response JSON

        Raises:
            CodatAuthError: If authentication fails
            CodatAPIError: If API returns an error
        """
        if not self.is_configured:
            raise CodatAuthError("Codat API key not configured")

        client = await self._get_client()

        try:
            response = await client.request(
                method=method,
                url=endpoint,
                json=data,
                params=params,
            )

            if response.status_code == 401:
                raise CodatAuthError("Invalid Codat API key")

            if response.status_code >= 400:
                error_data = response.json() if response.content else {}
                raise CodatAPIError(
                    f"Codat API error: {response.status_code}",
                    status_code=response.status_code,
                    response=error_data,
                )

            return response.json() if response.content else {}

        except httpx.RequestError as e:
            raise CodatAPIError(f"Request failed: {str(e)}")

    # =========================================================================
    # Company Management
    # =========================================================================

    async def create_company(
        self,
        name: str,
        deal_id: Optional[str] = None,
        description: Optional[str] = None,
    ) -> CodatCompany:
        """
        Create a new company in Codat.

        This is the first step in connecting to an accounting system.
        After creation, use get_link_url to get the OAuth link.

        Args:
            name: Company name
            deal_id: Optional deal ID for internal tracking
            description: Optional description

        Returns:
            Created company with ID
        """
        data = {
            "name": name,
            "description": description or f"PE Deal: {deal_id}" if deal_id else None,
        }

        # Remove None values
        data = {k: v for k, v in data.items() if v is not None}

        result = await self._request("POST", "/companies", data=data)

        return CodatCompany(
            id=result["id"],
            name=result["name"],
            platform=result.get("platform"),
            redirect=result.get("redirect"),
            created=datetime.fromisoformat(result["created"].replace("Z", "+00:00"))
            if result.get("created")
            else None,
        )

    async def get_company(self, company_id: str) -> CodatCompany:
        """
        Get company details.

        Args:
            company_id: Codat company ID

        Returns:
            Company details including connections
        """
        result = await self._request("GET", f"/companies/{company_id}")

        connections = []
        for conn in result.get("dataConnections", []):
            connections.append(CodatConnection(
                id=conn["id"],
                integration_id=conn.get("integrationId", ""),
                integration_key=conn.get("integrationKey", ""),
                source_id=conn.get("sourceId", ""),
                platform_name=conn.get("platformName", "Unknown"),
                link_url=conn.get("linkUrl", ""),
                status=CodatConnectionStatus(conn["status"]),
                last_sync=datetime.fromisoformat(conn["lastSync"].replace("Z", "+00:00"))
                if conn.get("lastSync")
                else None,
                created=datetime.fromisoformat(conn["created"].replace("Z", "+00:00"))
                if conn.get("created")
                else None,
            ))

        return CodatCompany(
            id=result["id"],
            name=result["name"],
            platform=result.get("platform"),
            redirect=result.get("redirect"),
            last_sync=datetime.fromisoformat(result["lastSync"].replace("Z", "+00:00"))
            if result.get("lastSync")
            else None,
            data_connections=connections,
            created=datetime.fromisoformat(result["created"].replace("Z", "+00:00"))
            if result.get("created")
            else None,
        )

    async def list_companies(
        self,
        page: int = 1,
        page_size: int = 100,
    ) -> List[CodatCompany]:
        """
        List all companies.

        Args:
            page: Page number
            page_size: Results per page

        Returns:
            List of companies
        """
        result = await self._request(
            "GET",
            "/companies",
            params={"page": page, "pageSize": page_size},
        )

        companies = []
        for company in result.get("results", []):
            companies.append(CodatCompany(
                id=company["id"],
                name=company["name"],
                platform=company.get("platform"),
                redirect=company.get("redirect"),
                last_sync=datetime.fromisoformat(company["lastSync"].replace("Z", "+00:00"))
                if company.get("lastSync")
                else None,
                created=datetime.fromisoformat(company["created"].replace("Z", "+00:00"))
                if company.get("created")
                else None,
            ))

        return companies

    async def delete_company(self, company_id: str) -> bool:
        """
        Delete a company and all its data.

        Args:
            company_id: Codat company ID

        Returns:
            True if deleted
        """
        await self._request("DELETE", f"/companies/{company_id}")
        return True

    # =========================================================================
    # OAuth / Linking
    # =========================================================================

    async def get_link_url(self, company_id: str) -> CodatLinkResponse:
        """
        Get the OAuth link URL for connecting an accounting platform.

        This URL should be presented to the target company's finance team.
        They will use it to authorize access to their accounting system.

        Args:
            company_id: Codat company ID

        Returns:
            Link response with URL
        """
        company = await self.get_company(company_id)

        # The redirect URL is the hosted link page
        link_url = company.redirect or f"https://link.codat.io/company/{company_id}"

        return CodatLinkResponse(
            company_id=company_id,
            link_url=link_url,
        )

    async def list_connections(self, company_id: str) -> List[CodatConnection]:
        """
        List all data connections for a company.

        Args:
            company_id: Codat company ID

        Returns:
            List of connections
        """
        result = await self._request("GET", f"/companies/{company_id}/connections")

        connections = []
        for conn in result.get("results", []):
            connections.append(CodatConnection(
                id=conn["id"],
                integration_id=conn.get("integrationId", ""),
                integration_key=conn.get("integrationKey", ""),
                source_id=conn.get("sourceId", ""),
                platform_name=conn.get("platformName", "Unknown"),
                link_url=conn.get("linkUrl", ""),
                status=CodatConnectionStatus(conn["status"]),
                last_sync=datetime.fromisoformat(conn["lastSync"].replace("Z", "+00:00"))
                if conn.get("lastSync")
                else None,
                created=datetime.fromisoformat(conn["created"].replace("Z", "+00:00"))
                if conn.get("created")
                else None,
            ))

        return connections

    # =========================================================================
    # Data Sync
    # =========================================================================

    async def sync_data(
        self,
        company_id: str,
        data_types: List[CodatDataType] = None,
    ) -> List[CodatSyncResult]:
        """
        Trigger data sync for specified data types.

        Args:
            company_id: Codat company ID
            data_types: List of data types to sync. If None, syncs all.

        Returns:
            List of sync results
        """
        if data_types is None:
            data_types = [
                CodatDataType.BALANCE_SHEET,
                CodatDataType.PROFIT_AND_LOSS,
                CodatDataType.INVOICES,
                CodatDataType.CUSTOMERS,
                CodatDataType.BANK_TRANSACTIONS,
            ]

        results = []
        for data_type in data_types:
            try:
                result = await self._request(
                    "POST",
                    f"/companies/{company_id}/data/queue/{data_type.value}",
                )

                results.append(CodatSyncResult(
                    company_id=company_id,
                    data_type=data_type,
                    sync_id=result.get("id", ""),
                    status=CodatSyncStatus.QUEUED,
                    message="Sync queued",
                ))
            except CodatAPIError as e:
                results.append(CodatSyncResult(
                    company_id=company_id,
                    data_type=data_type,
                    sync_id="",
                    status=CodatSyncStatus.ERROR,
                    message=str(e),
                ))

        return results

    async def get_sync_status(
        self,
        company_id: str,
        data_type: CodatDataType,
    ) -> CodatSyncResult:
        """
        Get sync status for a data type.

        Args:
            company_id: Codat company ID
            data_type: Data type to check

        Returns:
            Sync status
        """
        result = await self._request(
            "GET",
            f"/companies/{company_id}/dataStatus",
        )

        for data_set in result.get("dataSets", []):
            if data_set.get("dataType") == data_type.value:
                return CodatSyncResult(
                    company_id=company_id,
                    data_type=data_type,
                    sync_id=data_set.get("currentSyncId", ""),
                    status=CodatSyncStatus(data_set.get("currentStatus", "Success")),
                    completed_on_utc=datetime.fromisoformat(
                        data_set["lastSuccessfulSync"].replace("Z", "+00:00")
                    ) if data_set.get("lastSuccessfulSync") else None,
                )

        return CodatSyncResult(
            company_id=company_id,
            data_type=data_type,
            sync_id="",
            status=CodatSyncStatus.NOT_SUPPORTED,
            message="Data type not available",
        )

    # =========================================================================
    # Financial Statements
    # =========================================================================

    async def get_balance_sheet(
        self,
        company_id: str,
        period_length: int = 12,
        periods_to_compare: int = 1,
        start_month: date = None,
    ) -> BalanceSheet:
        """
        Get balance sheet report.

        Args:
            company_id: Codat company ID
            period_length: Number of months per period
            periods_to_compare: Number of periods to retrieve
            start_month: Start month (defaults to current)

        Returns:
            Balance sheet data
        """
        params = {
            "periodLength": period_length,
            "periodsToCompare": periods_to_compare,
        }
        if start_month:
            params["startMonth"] = start_month.strftime("%Y-%m-%d")

        result = await self._request(
            "GET",
            f"/companies/{company_id}/data/financials/balanceSheet",
            params=params,
        )

        reports = result.get("reports", [])
        if not reports:
            # Return empty balance sheet
            return BalanceSheet(
                company_id=company_id,
                report_date=date.today(),
                currency=result.get("currency", "USD"),
            )

        report = reports[0]  # Most recent period

        def parse_items(items: list) -> List[BalanceSheetLine]:
            """Parse balance sheet items recursively."""
            parsed = []
            for item in items:
                line = BalanceSheetLine(
                    name=item.get("name", "Unknown"),
                    value=Decimal(str(item.get("value", 0))),
                    account_id=item.get("accountId"),
                    sub_items=parse_items(item.get("items", [])),
                )
                parsed.append(line)
            return parsed

        # Parse sections
        assets = []
        liabilities = []
        equity = []

        for section in report.get("items", []):
            section_name = section.get("name", "").lower()
            items = parse_items(section.get("items", []))

            if "asset" in section_name:
                assets.extend(items)
            elif "liabilit" in section_name:
                liabilities.extend(items)
            elif "equity" in section_name or "capital" in section_name:
                equity.extend(items)

        # Calculate totals
        def sum_items(items: List[BalanceSheetLine]) -> Decimal:
            total = Decimal(0)
            for item in items:
                total += item.value
                total += sum_items(item.sub_items)
            return total

        total_assets = sum_items(assets)
        total_liabilities = sum_items(liabilities)
        total_equity = sum_items(equity)

        return BalanceSheet(
            company_id=company_id,
            report_date=date.fromisoformat(report.get("date", date.today().isoformat())[:10]),
            currency=result.get("currency", "USD"),
            assets=assets,
            total_assets=total_assets,
            liabilities=liabilities,
            total_liabilities=total_liabilities,
            equity=equity,
            total_equity=total_equity,
            net_assets=total_assets - total_liabilities,
        )

    async def get_profit_and_loss(
        self,
        company_id: str,
        period_length: int = 12,
        periods_to_compare: int = 1,
        start_month: date = None,
    ) -> ProfitAndLoss:
        """
        Get profit and loss statement.

        Args:
            company_id: Codat company ID
            period_length: Number of months per period
            periods_to_compare: Number of periods to retrieve
            start_month: Start month (defaults to current)

        Returns:
            P&L data
        """
        params = {
            "periodLength": period_length,
            "periodsToCompare": periods_to_compare,
        }
        if start_month:
            params["startMonth"] = start_month.strftime("%Y-%m-%d")

        result = await self._request(
            "GET",
            f"/companies/{company_id}/data/financials/profitAndLoss",
            params=params,
        )

        reports = result.get("reports", [])
        if not reports:
            return ProfitAndLoss(
                company_id=company_id,
                from_date=date.today() - timedelta(days=365),
                to_date=date.today(),
                currency=result.get("currency", "USD"),
            )

        report = reports[0]

        def parse_items(items: list) -> List[ProfitAndLossLine]:
            """Parse P&L items recursively."""
            parsed = []
            for item in items:
                line = ProfitAndLossLine(
                    name=item.get("name", "Unknown"),
                    value=Decimal(str(item.get("value", 0))),
                    account_id=item.get("accountId"),
                    sub_items=parse_items(item.get("items", [])),
                )
                parsed.append(line)
            return parsed

        # Parse sections
        income = []
        cost_of_sales = []
        expenses = []

        for section in report.get("items", []):
            section_name = section.get("name", "").lower()
            items = parse_items(section.get("items", []))

            if "income" in section_name or "revenue" in section_name or "sales" in section_name:
                if "cost" not in section_name:
                    income.extend(items)
            elif "cost of" in section_name or "cogs" in section_name:
                cost_of_sales.extend(items)
            elif "expense" in section_name or "operating" in section_name:
                expenses.extend(items)

        def sum_items(items: List[ProfitAndLossLine]) -> Decimal:
            total = Decimal(0)
            for item in items:
                total += item.value
                total += sum_items(item.sub_items)
            return total

        total_income = sum_items(income)
        total_cost_of_sales = sum_items(cost_of_sales)
        total_expenses = sum_items(expenses)
        gross_profit = total_income - total_cost_of_sales
        operating_profit = gross_profit - total_expenses

        from_date_str = report.get("fromDate", "")
        to_date_str = report.get("toDate", "")

        return ProfitAndLoss(
            company_id=company_id,
            from_date=date.fromisoformat(from_date_str[:10]) if from_date_str else date.today() - timedelta(days=365),
            to_date=date.fromisoformat(to_date_str[:10]) if to_date_str else date.today(),
            currency=result.get("currency", "USD"),
            income=income,
            total_income=total_income,
            cost_of_sales=cost_of_sales,
            total_cost_of_sales=total_cost_of_sales,
            gross_profit=gross_profit,
            expenses=expenses,
            total_expenses=total_expenses,
            operating_profit=operating_profit,
            net_profit=operating_profit,  # Simplified - no other income/expenses
        )

    # =========================================================================
    # Transactional Data
    # =========================================================================

    async def get_invoices(
        self,
        company_id: str,
        page: int = 1,
        page_size: int = 100,
    ) -> List[Invoice]:
        """
        Get invoices.

        Args:
            company_id: Codat company ID
            page: Page number
            page_size: Results per page

        Returns:
            List of invoices
        """
        result = await self._request(
            "GET",
            f"/companies/{company_id}/data/invoices",
            params={"page": page, "pageSize": page_size},
        )

        invoices = []
        for inv in result.get("results", []):
            line_items = []
            for line in inv.get("lineItems", []):
                line_items.append(InvoiceLineItem(
                    description=line.get("description"),
                    unit_amount=Decimal(str(line.get("unitAmount", 0))),
                    quantity=Decimal(str(line.get("quantity", 1))),
                    discount_amount=Decimal(str(line.get("discountAmount", 0))),
                    tax_amount=Decimal(str(line.get("taxAmount", 0))),
                    total_amount=Decimal(str(line.get("totalAmount", 0))),
                ))

            invoices.append(Invoice(
                id=inv["id"],
                company_id=company_id,
                invoice_number=inv.get("invoiceNumber"),
                customer_ref=inv.get("customerRef", {}).get("id"),
                customer_name=inv.get("customerRef", {}).get("companyName"),
                issue_date=date.fromisoformat(inv["issueDate"][:10]) if inv.get("issueDate") else date.today(),
                due_date=date.fromisoformat(inv["dueDate"][:10]) if inv.get("dueDate") else None,
                paid_on_date=date.fromisoformat(inv["paidOnDate"][:10]) if inv.get("paidOnDate") else None,
                currency=inv.get("currency", "USD"),
                sub_total=Decimal(str(inv.get("subTotal", 0))),
                tax_amount=Decimal(str(inv.get("totalTaxAmount", 0))),
                total_amount=Decimal(str(inv.get("totalAmount", 0))),
                amount_due=Decimal(str(inv.get("amountDue", 0))),
                status=inv.get("status", "Unknown"),
                line_items=line_items,
            ))

        return invoices

    async def get_customers(
        self,
        company_id: str,
        page: int = 1,
        page_size: int = 100,
    ) -> List[Customer]:
        """
        Get customers.

        Args:
            company_id: Codat company ID
            page: Page number
            page_size: Results per page

        Returns:
            List of customers
        """
        result = await self._request(
            "GET",
            f"/companies/{company_id}/data/customers",
            params={"page": page, "pageSize": page_size},
        )

        customers = []
        for cust in result.get("results", []):
            customers.append(Customer(
                id=cust["id"],
                company_id=company_id,
                customer_name=cust.get("customerName", "Unknown"),
                contact_name=cust.get("contactName"),
                email=cust.get("emailAddress"),
                phone=cust.get("phone"),
                default_currency=cust.get("defaultCurrency", "USD"),
                status=cust.get("status", "Active"),
                modified_date=datetime.fromisoformat(cust["modifiedDate"].replace("Z", "+00:00"))
                if cust.get("modifiedDate")
                else None,
            ))

        return customers

    async def get_bank_accounts(
        self,
        company_id: str,
    ) -> List[BankAccount]:
        """
        Get bank accounts.

        Args:
            company_id: Codat company ID

        Returns:
            List of bank accounts
        """
        result = await self._request(
            "GET",
            f"/companies/{company_id}/data/bankAccounts",
        )

        accounts = []
        for acct in result.get("results", []):
            accounts.append(BankAccount(
                id=acct["id"],
                company_id=company_id,
                account_name=acct.get("accountName", "Unknown"),
                account_type=acct.get("accountType", "Unknown"),
                account_number=acct.get("accountNumber"),
                currency=acct.get("currency", "USD"),
                current_balance=Decimal(str(acct.get("balance", 0))),
                institution=acct.get("institution"),
                status=acct.get("status", "Unknown"),
            ))

        return accounts

    async def get_bank_transactions(
        self,
        company_id: str,
        account_id: str = None,
        page: int = 1,
        page_size: int = 100,
    ) -> List[BankTransaction]:
        """
        Get bank transactions.

        Args:
            company_id: Codat company ID
            account_id: Optional specific account
            page: Page number
            page_size: Results per page

        Returns:
            List of transactions
        """
        # Get from banking endpoint
        endpoint = f"/companies/{company_id}/data/bankTransactions"
        if account_id:
            endpoint = f"/companies/{company_id}/data/bankAccounts/{account_id}/transactions"

        result = await self._request(
            "GET",
            endpoint,
            params={"page": page, "pageSize": page_size},
        )

        transactions = []
        for txn in result.get("results", []):
            transactions.append(BankTransaction(
                id=txn["id"],
                company_id=company_id,
                account_id=txn.get("accountId", account_id or ""),
                date=date.fromisoformat(txn["date"][:10]) if txn.get("date") else date.today(),
                description=txn.get("description"),
                amount=Decimal(str(txn.get("amount", 0))),
                currency=txn.get("currency", "USD"),
                transaction_type=txn.get("transactionType", "Unknown"),
                category=txn.get("transactionCategory"),
                reconciled=txn.get("reconciled", False),
            ))

        return transactions

    # =========================================================================
    # Summary & Analysis
    # =========================================================================

    async def get_accounting_summary(self, company_id: str) -> AccountingSummary:
        """
        Get summary of all accounting data for a company.

        Args:
            company_id: Codat company ID

        Returns:
            Accounting summary with key metrics
        """
        company = await self.get_company(company_id)

        # Get financial statements
        try:
            balance_sheet = await self.get_balance_sheet(company_id)
        except CodatAPIError:
            balance_sheet = None

        try:
            pnl = await self.get_profit_and_loss(company_id)
        except CodatAPIError:
            pnl = None

        # Get customers
        try:
            customers = await self.get_customers(company_id)
        except CodatAPIError:
            customers = []

        # Get invoices for receivables
        try:
            invoices = await self.get_invoices(company_id)
            total_receivables = sum(inv.amount_due for inv in invoices)
            avg_invoice = (
                sum(inv.total_amount for inv in invoices) / len(invoices)
                if invoices else Decimal(0)
            )
        except CodatAPIError:
            total_receivables = Decimal(0)
            avg_invoice = Decimal(0)
            invoices = []

        # Get bank accounts
        try:
            bank_accounts = await self.get_bank_accounts(company_id)
            total_bank_balance = sum(
                acct.current_balance or Decimal(0) for acct in bank_accounts
            )
        except CodatAPIError:
            bank_accounts = []
            total_bank_balance = Decimal(0)

        # Determine platform from connections
        platform = None
        for conn in company.data_connections:
            if conn.status == CodatConnectionStatus.LINKED:
                platform = conn.platform_name
                break

        return AccountingSummary(
            company_id=company_id,
            company_name=company.name,
            platform=platform,
            currency=balance_sheet.currency if balance_sheet else "USD",
            total_revenue_ytd=pnl.total_income if pnl else None,
            total_expenses_ytd=pnl.total_expenses if pnl else None,
            net_income_ytd=pnl.net_profit if pnl else None,
            total_assets=balance_sheet.total_assets if balance_sheet else None,
            total_liabilities=balance_sheet.total_liabilities if balance_sheet else None,
            total_equity=balance_sheet.total_equity if balance_sheet else None,
            total_customers=len(customers),
            total_receivables=total_receivables,
            average_invoice_amount=avg_invoice,
            total_bank_balance=total_bank_balance,
            bank_accounts_count=len(bank_accounts),
            last_sync=company.last_sync,
            data_as_of=balance_sheet.report_date if balance_sheet else None,
        )


# Singleton instance
_codat_service: Optional[CodatService] = None


def get_codat_service() -> CodatService:
    """Get or create Codat service instance."""
    global _codat_service
    if _codat_service is None:
        _codat_service = CodatService()
    return _codat_service
