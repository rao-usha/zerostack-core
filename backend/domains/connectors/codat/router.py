"""
Codat API Router

Endpoints for Codat accounting system integration:
- Company management
- OAuth linking flow
- Data synchronization
- Financial data retrieval
- Webhook handling
"""
import hashlib
import hmac
import logging
from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, Query, Request, BackgroundTasks, Depends
from pydantic import BaseModel, Field

from core.config import settings
from .service import CodatService, CodatServiceError, CodatAuthError, CodatAPIError, get_codat_service
from .models import (
    CodatCompany,
    CodatCompanyCreate,
    CodatConnection,
    CodatDataType,
    CodatLinkResponse,
    CodatSyncResult,
    BalanceSheet,
    ProfitAndLoss,
    Invoice,
    Customer,
    BankAccount,
    BankTransaction,
    AccountingSummary,
    SyncRequest,
)


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/codat", tags=["codat"])


# =========================================================================
# Response Models
# =========================================================================

class CompanyListResponse(BaseModel):
    """List of companies."""
    companies: List[CodatCompany]
    total: int


class SyncStatusResponse(BaseModel):
    """Sync status response."""
    company_id: str
    results: List[CodatSyncResult]


class InvoiceListResponse(BaseModel):
    """List of invoices."""
    invoices: List[Invoice]
    total: int
    page: int
    page_size: int


class CustomerListResponse(BaseModel):
    """List of customers."""
    customers: List[Customer]
    total: int
    page: int
    page_size: int


class BankAccountListResponse(BaseModel):
    """List of bank accounts."""
    accounts: List[BankAccount]
    total: int


class BankTransactionListResponse(BaseModel):
    """List of bank transactions."""
    transactions: List[BankTransaction]
    total: int
    page: int
    page_size: int


class WebhookResponse(BaseModel):
    """Webhook processing response."""
    received: bool
    event_type: Optional[str] = None
    company_id: Optional[str] = None
    message: str


class HealthResponse(BaseModel):
    """Codat health check response."""
    configured: bool
    message: str


# =========================================================================
# Health Check
# =========================================================================

@router.get("/health", response_model=HealthResponse)
async def check_codat_health():
    """
    Check if Codat is properly configured.

    Returns configuration status without exposing API key.
    """
    service = get_codat_service()
    if service.is_configured:
        return HealthResponse(
            configured=True,
            message="Codat API key is configured",
        )
    return HealthResponse(
        configured=False,
        message="Codat API key not configured. Set CODAT_API_KEY environment variable.",
    )


# =========================================================================
# Company Management
# =========================================================================

@router.post("/companies", response_model=CodatCompany)
async def create_company(request: CodatCompanyCreate):
    """
    Create a new company in Codat.

    This is the first step in connecting to an accounting system.
    After creation, use the link endpoint to get the OAuth URL.
    """
    service = get_codat_service()
    try:
        company = await service.create_company(
            name=request.name,
            deal_id=request.deal_id,
            description=request.description,
        )
        return company
    except CodatAuthError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except CodatAPIError as e:
        raise HTTPException(status_code=e.status_code or 500, detail=str(e))


@router.get("/companies", response_model=CompanyListResponse)
async def list_companies(
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=500),
):
    """
    List all companies.
    """
    service = get_codat_service()
    try:
        companies = await service.list_companies(page=page, page_size=page_size)
        return CompanyListResponse(
            companies=companies,
            total=len(companies),  # Codat doesn't return total, would need separate call
        )
    except CodatAuthError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except CodatAPIError as e:
        raise HTTPException(status_code=e.status_code or 500, detail=str(e))


@router.get("/companies/{company_id}", response_model=CodatCompany)
async def get_company(company_id: str):
    """
    Get company details including connections.
    """
    service = get_codat_service()
    try:
        company = await service.get_company(company_id)
        return company
    except CodatAuthError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except CodatAPIError as e:
        if e.status_code == 404:
            raise HTTPException(status_code=404, detail="Company not found")
        raise HTTPException(status_code=e.status_code or 500, detail=str(e))


@router.delete("/companies/{company_id}")
async def delete_company(company_id: str):
    """
    Delete a company and all its data.
    """
    service = get_codat_service()
    try:
        await service.delete_company(company_id)
        return {"deleted": True, "company_id": company_id}
    except CodatAuthError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except CodatAPIError as e:
        if e.status_code == 404:
            raise HTTPException(status_code=404, detail="Company not found")
        raise HTTPException(status_code=e.status_code or 500, detail=str(e))


# =========================================================================
# OAuth / Linking
# =========================================================================

@router.get("/companies/{company_id}/link", response_model=CodatLinkResponse)
async def get_link_url(company_id: str):
    """
    Get the OAuth link URL for connecting an accounting platform.

    Share this URL with the target company's finance team.
    They will use it to authorize access to their accounting system.
    """
    service = get_codat_service()
    try:
        link = await service.get_link_url(company_id)
        return link
    except CodatAuthError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except CodatAPIError as e:
        if e.status_code == 404:
            raise HTTPException(status_code=404, detail="Company not found")
        raise HTTPException(status_code=e.status_code or 500, detail=str(e))


@router.get("/companies/{company_id}/connections", response_model=List[CodatConnection])
async def list_connections(company_id: str):
    """
    List all data connections for a company.
    """
    service = get_codat_service()
    try:
        connections = await service.list_connections(company_id)
        return connections
    except CodatAuthError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except CodatAPIError as e:
        if e.status_code == 404:
            raise HTTPException(status_code=404, detail="Company not found")
        raise HTTPException(status_code=e.status_code or 500, detail=str(e))


# =========================================================================
# Data Sync
# =========================================================================

@router.post("/companies/{company_id}/sync", response_model=SyncStatusResponse)
async def sync_data(
    company_id: str,
    request: SyncRequest = None,
    background_tasks: BackgroundTasks = None,
):
    """
    Trigger data sync for a company.

    By default syncs: Balance Sheet, P&L, Invoices, Customers.
    Specify data_types to sync specific data.
    """
    service = get_codat_service()
    data_types = request.data_types if request else None

    try:
        results = await service.sync_data(company_id, data_types)
        return SyncStatusResponse(
            company_id=company_id,
            results=results,
        )
    except CodatAuthError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except CodatAPIError as e:
        if e.status_code == 404:
            raise HTTPException(status_code=404, detail="Company not found")
        raise HTTPException(status_code=e.status_code or 500, detail=str(e))


@router.get("/companies/{company_id}/sync-status/{data_type}", response_model=CodatSyncResult)
async def get_sync_status(company_id: str, data_type: CodatDataType):
    """
    Get sync status for a specific data type.
    """
    service = get_codat_service()
    try:
        status = await service.get_sync_status(company_id, data_type)
        return status
    except CodatAuthError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except CodatAPIError as e:
        raise HTTPException(status_code=e.status_code or 500, detail=str(e))


# =========================================================================
# Financial Statements
# =========================================================================

@router.get("/companies/{company_id}/balance-sheet", response_model=BalanceSheet)
async def get_balance_sheet(
    company_id: str,
    period_length: int = Query(12, ge=1, le=24, description="Period length in months"),
    periods_to_compare: int = Query(1, ge=1, le=12, description="Number of periods"),
):
    """
    Get balance sheet report.
    """
    service = get_codat_service()
    try:
        balance_sheet = await service.get_balance_sheet(
            company_id,
            period_length=period_length,
            periods_to_compare=periods_to_compare,
        )
        return balance_sheet
    except CodatAuthError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except CodatAPIError as e:
        if e.status_code == 404:
            raise HTTPException(status_code=404, detail="Company not found or no balance sheet data")
        raise HTTPException(status_code=e.status_code or 500, detail=str(e))


@router.get("/companies/{company_id}/profit-loss", response_model=ProfitAndLoss)
async def get_profit_and_loss(
    company_id: str,
    period_length: int = Query(12, ge=1, le=24, description="Period length in months"),
    periods_to_compare: int = Query(1, ge=1, le=12, description="Number of periods"),
):
    """
    Get profit and loss statement.
    """
    service = get_codat_service()
    try:
        pnl = await service.get_profit_and_loss(
            company_id,
            period_length=period_length,
            periods_to_compare=periods_to_compare,
        )
        return pnl
    except CodatAuthError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except CodatAPIError as e:
        if e.status_code == 404:
            raise HTTPException(status_code=404, detail="Company not found or no P&L data")
        raise HTTPException(status_code=e.status_code or 500, detail=str(e))


# =========================================================================
# Transactional Data
# =========================================================================

@router.get("/companies/{company_id}/invoices", response_model=InvoiceListResponse)
async def get_invoices(
    company_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=500),
):
    """
    Get invoices.
    """
    service = get_codat_service()
    try:
        invoices = await service.get_invoices(
            company_id,
            page=page,
            page_size=page_size,
        )
        return InvoiceListResponse(
            invoices=invoices,
            total=len(invoices),
            page=page,
            page_size=page_size,
        )
    except CodatAuthError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except CodatAPIError as e:
        if e.status_code == 404:
            raise HTTPException(status_code=404, detail="Company not found")
        raise HTTPException(status_code=e.status_code or 500, detail=str(e))


@router.get("/companies/{company_id}/customers", response_model=CustomerListResponse)
async def get_customers(
    company_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=500),
):
    """
    Get customers.
    """
    service = get_codat_service()
    try:
        customers = await service.get_customers(
            company_id,
            page=page,
            page_size=page_size,
        )
        return CustomerListResponse(
            customers=customers,
            total=len(customers),
            page=page,
            page_size=page_size,
        )
    except CodatAuthError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except CodatAPIError as e:
        if e.status_code == 404:
            raise HTTPException(status_code=404, detail="Company not found")
        raise HTTPException(status_code=e.status_code or 500, detail=str(e))


@router.get("/companies/{company_id}/bank-accounts", response_model=BankAccountListResponse)
async def get_bank_accounts(company_id: str):
    """
    Get bank accounts.
    """
    service = get_codat_service()
    try:
        accounts = await service.get_bank_accounts(company_id)
        return BankAccountListResponse(
            accounts=accounts,
            total=len(accounts),
        )
    except CodatAuthError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except CodatAPIError as e:
        if e.status_code == 404:
            raise HTTPException(status_code=404, detail="Company not found")
        raise HTTPException(status_code=e.status_code or 500, detail=str(e))


@router.get("/companies/{company_id}/bank-transactions", response_model=BankTransactionListResponse)
async def get_bank_transactions(
    company_id: str,
    account_id: Optional[str] = Query(None, description="Filter by account ID"),
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=500),
):
    """
    Get bank transactions.
    """
    service = get_codat_service()
    try:
        transactions = await service.get_bank_transactions(
            company_id,
            account_id=account_id,
            page=page,
            page_size=page_size,
        )
        return BankTransactionListResponse(
            transactions=transactions,
            total=len(transactions),
            page=page,
            page_size=page_size,
        )
    except CodatAuthError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except CodatAPIError as e:
        if e.status_code == 404:
            raise HTTPException(status_code=404, detail="Company not found")
        raise HTTPException(status_code=e.status_code or 500, detail=str(e))


# =========================================================================
# Summary
# =========================================================================

@router.get("/companies/{company_id}/summary", response_model=AccountingSummary)
async def get_accounting_summary(company_id: str):
    """
    Get summary of all accounting data for a company.

    Aggregates key metrics from financial statements, customers, invoices, and bank accounts.
    """
    service = get_codat_service()
    try:
        summary = await service.get_accounting_summary(company_id)
        return summary
    except CodatAuthError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except CodatAPIError as e:
        if e.status_code == 404:
            raise HTTPException(status_code=404, detail="Company not found")
        raise HTTPException(status_code=e.status_code or 500, detail=str(e))


# =========================================================================
# Webhooks
# =========================================================================

def _verify_webhook_signature(payload: bytes, signature: str, secret: str) -> bool:
    """Verify Codat webhook signature."""
    if not secret:
        return True  # Skip verification if no secret configured

    expected = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(signature.lower(), expected.lower())


@router.post("/webhook", response_model=WebhookResponse)
async def handle_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
):
    """
    Handle Codat webhook events.

    Events include:
    - DataConnectionStatusChanged: When a connection is linked/unlinked
    - DataSyncCompleted: When data sync completes
    - NewCompanySynchronized: When initial sync completes
    """
    # Get raw body for signature verification
    body = await request.body()

    # Verify signature if secret is configured
    webhook_secret = getattr(settings, 'codat_webhook_secret', None)
    signature = request.headers.get('Codat-Signature', '')

    if webhook_secret and not _verify_webhook_signature(body, signature, webhook_secret):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    # Parse payload
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    event_type = payload.get('type') or payload.get('Type', 'Unknown')
    company_id = payload.get('companyId') or payload.get('CompanyId')

    logger.info(f"Received Codat webhook: {event_type} for company {company_id}")

    # Process webhook in background
    # TODO: Implement webhook processing logic
    # background_tasks.add_task(process_webhook, payload)

    return WebhookResponse(
        received=True,
        event_type=event_type,
        company_id=company_id,
        message="Webhook received successfully",
    )
