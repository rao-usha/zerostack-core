"""LP Collection API router - Read-only access to LP data."""
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Depends

from .service import LPCollectionService
from .models import (
    LPFundListResponse,
    LPFundDetail,
    LPSearchFilters,
    LPContactListResponse,
    LPDocumentListResponse,
    LPDocumentDetail,
    LPAllocationListResponse,
    LPExposureListResponse,
    LPCollectionStats,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/lp-collection", tags=["lp-collection"])


# ========================================
# List & Search Endpoints
# ========================================

@router.get("/funds", response_model=LPFundListResponse)
async def list_lp_funds(
    lp_name: Optional[str] = Query(None, description="Filter by LP name (partial match)"),
    fund_name: Optional[str] = Query(None, description="Filter by fund name (partial match)"),
    fund_type: Optional[str] = Query(None, description="Filter by fund type"),
    strategy: Optional[str] = Query(None, description="Filter by strategy"),
    vintage_year: Optional[int] = Query(None, description="Filter by exact vintage year"),
    vintage_year_min: Optional[int] = Query(None, description="Minimum vintage year"),
    vintage_year_max: Optional[int] = Query(None, description="Maximum vintage year"),
    min_commitment: Optional[float] = Query(None, description="Minimum commitment amount"),
    max_commitment: Optional[float] = Query(None, description="Maximum commitment amount"),
    status: Optional[str] = Query(None, description="Filter by status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=500, description="Items per page"),
    sort_by: str = Query("fund_name", description="Field to sort by"),
    sort_desc: bool = Query(False, description="Sort in descending order"),
    db_id: Optional[str] = Query(None, description="Database configuration ID")
):
    """
    List LP funds with optional filtering, pagination, and sorting.

    Supports filtering by:
    - LP name (partial match)
    - Fund name (partial match)
    - Fund type (exact match)
    - Strategy (partial match)
    - Vintage year (exact or range)
    - Commitment amount (range)
    - Status (exact match)
    """
    try:
        filters = LPSearchFilters(
            lp_name=lp_name,
            fund_name=fund_name,
            fund_type=fund_type,
            strategy=strategy,
            vintage_year=vintage_year,
            vintage_year_min=vintage_year_min,
            vintage_year_max=vintage_year_max,
            min_commitment=min_commitment,
            max_commitment=max_commitment,
            status=status,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_desc=sort_desc
        )

        funds, total = LPCollectionService.list_funds(filters, db_id)

        total_pages = (total + page_size - 1) // page_size if total > 0 else 1

        return LPFundListResponse(
            funds=funds,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error listing LP funds: {e}")
        raise HTTPException(status_code=500, detail="Failed to list LP funds")


# ========================================
# Fund Detail Endpoints
# ========================================

@router.get("/funds/{fund_id}", response_model=LPFundDetail)
async def get_lp_fund(
    fund_id: int,
    db_id: Optional[str] = Query(None, description="Database configuration ID")
):
    """
    Get full detail for an LP fund including all related data.

    Returns:
    - Fund details (name, commitment, strategy, etc.)
    - Key contacts
    - Documents (summaries)
    - Strategy snapshots with thematic tags
    - Asset class allocations
    - Asset class projections
    - Manager/vehicle exposures
    """
    try:
        fund = LPCollectionService.get_fund_detail(fund_id, db_id)

        if not fund:
            raise HTTPException(status_code=404, detail=f"LP fund {fund_id} not found")

        return fund
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting LP fund {fund_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get LP fund")


@router.get("/funds/{fund_id}/contacts", response_model=LPContactListResponse)
async def get_fund_contacts(
    fund_id: int,
    db_id: Optional[str] = Query(None, description="Database configuration ID")
):
    """
    Get key contacts for an LP fund.

    Returns contacts ordered by:
    1. Primary contact first
    2. Alphabetically by name
    """
    try:
        # Verify fund exists
        if not LPCollectionService.fund_exists(fund_id, db_id):
            raise HTTPException(status_code=404, detail=f"LP fund {fund_id} not found")

        contacts = LPCollectionService.get_fund_contacts(fund_id, db_id)

        return LPContactListResponse(
            contacts=contacts,
            total=len(contacts)
        )
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting contacts for LP fund {fund_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get fund contacts")


@router.get("/funds/{fund_id}/documents", response_model=LPDocumentListResponse)
async def get_fund_documents(
    fund_id: int,
    limit: int = Query(100, ge=1, le=500, description="Maximum documents to return"),
    offset: int = Query(0, ge=0, description="Number of documents to skip"),
    db_id: Optional[str] = Query(None, description="Database configuration ID")
):
    """
    Get documents for an LP fund.

    Returns documents ordered by date (newest first).
    """
    try:
        # Verify fund exists
        if not LPCollectionService.fund_exists(fund_id, db_id):
            raise HTTPException(status_code=404, detail=f"LP fund {fund_id} not found")

        documents, total = LPCollectionService.get_fund_documents(
            fund_id, db_id, limit, offset
        )

        return LPDocumentListResponse(
            documents=documents,
            total=total
        )
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting documents for LP fund {fund_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get fund documents")


@router.get("/funds/{fund_id}/allocations", response_model=LPAllocationListResponse)
async def get_fund_allocations(
    fund_id: int,
    db_id: Optional[str] = Query(None, description="Database configuration ID")
):
    """
    Get target asset class allocations for an LP fund.

    Returns allocations ordered by target allocation (highest first).
    """
    try:
        # Verify fund exists
        if not LPCollectionService.fund_exists(fund_id, db_id):
            raise HTTPException(status_code=404, detail=f"LP fund {fund_id} not found")

        allocations = LPCollectionService.get_fund_allocations(fund_id, db_id)

        return LPAllocationListResponse(
            allocations=allocations,
            total=len(allocations)
        )
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting allocations for LP fund {fund_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get fund allocations")


@router.get("/funds/{fund_id}/exposures", response_model=LPExposureListResponse)
async def get_fund_exposures(
    fund_id: int,
    db_id: Optional[str] = Query(None, description="Database configuration ID")
):
    """
    Get manager/vehicle exposures for an LP fund.

    Returns exposures ordered by exposure amount (highest first).
    """
    try:
        # Verify fund exists
        if not LPCollectionService.fund_exists(fund_id, db_id):
            raise HTTPException(status_code=404, detail=f"LP fund {fund_id} not found")

        exposures = LPCollectionService.get_fund_exposures(fund_id, db_id)

        return LPExposureListResponse(
            exposures=exposures,
            total=len(exposures)
        )
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting exposures for LP fund {fund_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get fund exposures")


# ========================================
# Document Detail Endpoint
# ========================================

@router.get("/documents/{doc_id}", response_model=LPDocumentDetail)
async def get_document_detail(
    doc_id: int,
    db_id: Optional[str] = Query(None, description="Database configuration ID")
):
    """
    Get full document detail with extracted text sections.

    Returns:
    - Document metadata (type, name, date, source URL)
    - All extracted text sections ordered by section order and page number
    """
    try:
        document = LPCollectionService.get_document_detail(doc_id, db_id)

        if not document:
            raise HTTPException(status_code=404, detail=f"Document {doc_id} not found")

        return document
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting document {doc_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get document")


# ========================================
# Statistics Endpoint
# ========================================

@router.get("/stats", response_model=LPCollectionStats)
async def get_lp_stats(
    db_id: Optional[str] = Query(None, description="Database configuration ID")
):
    """
    Get aggregate statistics for the LP collection.

    Returns:
    - Total counts (funds, contacts, documents)
    - Total commitment amount
    - Breakdowns by strategy, vintage year, and status
    """
    try:
        stats = LPCollectionService.get_stats(db_id)
        return stats
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting LP stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get LP statistics")
