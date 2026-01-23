"""FO (Family Office) Collection API router - Read-only access to FO data."""
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from .service import FOCollectionService
from .models import (
    FOListResponse,
    FamilyOfficeDetail,
    FOSearchFilters,
    FOContactListResponse,
    FOInteractionListResponse,
    CoInvestmentListResponse,
    PortfolioCompanyListResponse,
    InvestorThemeListResponse,
    ImpactAnalysis,
    FOCollectionStats,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/fo-collection", tags=["fo-collection"])


# ========================================
# List & Search Endpoints
# ========================================

@router.get("/offices", response_model=FOListResponse)
async def list_family_offices(
    name: Optional[str] = Query(None, description="Filter by office name (partial match)"),
    family_name: Optional[str] = Query(None, description="Filter by family name (partial match)"),
    headquarters: Optional[str] = Query(None, description="Filter by headquarters (partial match)"),
    office_type: Optional[str] = Query(None, description="Filter by office type"),
    investment_focus: Optional[str] = Query(None, description="Filter by investment focus (partial match)"),
    min_aum: Optional[float] = Query(None, description="Minimum AUM amount"),
    max_aum: Optional[float] = Query(None, description="Maximum AUM amount"),
    status: Optional[str] = Query(None, description="Filter by status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=500, description="Items per page"),
    sort_by: str = Query("name", description="Field to sort by"),
    sort_desc: bool = Query(False, description="Sort in descending order"),
    db_id: Optional[str] = Query(None, description="Database configuration ID")
):
    """
    List family offices with optional filtering, pagination, and sorting.

    Supports filtering by:
    - Office name (partial match)
    - Family name (partial match)
    - Headquarters location (partial match)
    - Office type (exact match)
    - Investment focus (partial match)
    - AUM range
    - Status (exact match)
    """
    try:
        filters = FOSearchFilters(
            name=name,
            family_name=family_name,
            headquarters=headquarters,
            office_type=office_type,
            investment_focus=investment_focus,
            min_aum=min_aum,
            max_aum=max_aum,
            status=status,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_desc=sort_desc
        )

        offices, total = FOCollectionService.list_offices(filters, db_id)

        total_pages = (total + page_size - 1) // page_size if total > 0 else 1

        return FOListResponse(
            offices=offices,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error listing family offices: {e}")
        raise HTTPException(status_code=500, detail="Failed to list family offices")


# ========================================
# Office Detail Endpoints
# ========================================

@router.get("/offices/{office_id}", response_model=FamilyOfficeDetail)
async def get_family_office(
    office_id: int,
    db_id: Optional[str] = Query(None, description="Database configuration ID")
):
    """
    Get full detail for a family office including all related data.

    Returns:
    - Office details (name, AUM, headquarters, etc.)
    - Key contacts
    - Recent interactions
    - Co-investments
    - Portfolio companies
    - Investment themes
    """
    try:
        office = FOCollectionService.get_office_detail(office_id, db_id)

        if not office:
            raise HTTPException(status_code=404, detail=f"Family office {office_id} not found")

        return office
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting family office {office_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get family office")


@router.get("/offices/{office_id}/contacts", response_model=FOContactListResponse)
async def get_office_contacts(
    office_id: int,
    db_id: Optional[str] = Query(None, description="Database configuration ID")
):
    """
    Get contacts for a family office.

    Returns contacts ordered by:
    1. Primary contact first
    2. Alphabetically by name
    """
    try:
        # Verify office exists
        if not FOCollectionService.office_exists(office_id, db_id):
            raise HTTPException(status_code=404, detail=f"Family office {office_id} not found")

        contacts = FOCollectionService.get_office_contacts(office_id, db_id)

        return FOContactListResponse(
            contacts=contacts,
            total=len(contacts)
        )
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting contacts for family office {office_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get office contacts")


@router.get("/offices/{office_id}/interactions", response_model=FOInteractionListResponse)
async def get_office_interactions(
    office_id: int,
    limit: int = Query(100, ge=1, le=500, description="Maximum interactions to return"),
    offset: int = Query(0, ge=0, description="Number of interactions to skip"),
    db_id: Optional[str] = Query(None, description="Database configuration ID")
):
    """
    Get interaction history for a family office.

    Returns interactions ordered by date (newest first).
    """
    try:
        # Verify office exists
        if not FOCollectionService.office_exists(office_id, db_id):
            raise HTTPException(status_code=404, detail=f"Family office {office_id} not found")

        interactions, total = FOCollectionService.get_office_interactions(
            office_id, db_id, limit, offset
        )

        return FOInteractionListResponse(
            interactions=interactions,
            total=total
        )
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting interactions for family office {office_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get office interactions")


@router.get("/offices/{office_id}/co-investments", response_model=CoInvestmentListResponse)
async def get_office_co_investments(
    office_id: int,
    limit: int = Query(100, ge=1, le=500, description="Maximum co-investments to return"),
    offset: int = Query(0, ge=0, description="Number to skip"),
    db_id: Optional[str] = Query(None, description="Database configuration ID")
):
    """
    Get co-investments for a family office.

    Returns co-investments ordered by close date (newest first).
    """
    try:
        # Verify office exists
        if not FOCollectionService.office_exists(office_id, db_id):
            raise HTTPException(status_code=404, detail=f"Family office {office_id} not found")

        co_investments, total = FOCollectionService.get_office_co_investments(
            office_id, db_id, limit, offset
        )

        return CoInvestmentListResponse(
            co_investments=co_investments,
            total=total
        )
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting co-investments for family office {office_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get office co-investments")


@router.get("/offices/{office_id}/portfolio", response_model=PortfolioCompanyListResponse)
async def get_office_portfolio(
    office_id: int,
    limit: int = Query(100, ge=1, le=500, description="Maximum portfolio companies to return"),
    offset: int = Query(0, ge=0, description="Number to skip"),
    db_id: Optional[str] = Query(None, description="Database configuration ID")
):
    """
    Get portfolio companies for a family office.

    Returns portfolio companies ordered by investment date (newest first).
    """
    try:
        # Verify office exists
        if not FOCollectionService.office_exists(office_id, db_id):
            raise HTTPException(status_code=404, detail=f"Family office {office_id} not found")

        portfolio, total = FOCollectionService.get_office_portfolio(
            office_id, db_id, limit, offset
        )

        return PortfolioCompanyListResponse(
            portfolio_companies=portfolio,
            total=total
        )
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting portfolio for family office {office_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get office portfolio")


@router.get("/offices/{office_id}/themes", response_model=InvestorThemeListResponse)
async def get_office_themes(
    office_id: int,
    db_id: Optional[str] = Query(None, description="Database configuration ID")
):
    """
    Get investment themes for a family office.

    Returns themes ordered by priority.
    """
    try:
        # Verify office exists
        if not FOCollectionService.office_exists(office_id, db_id):
            raise HTTPException(status_code=404, detail=f"Family office {office_id} not found")

        themes = FOCollectionService.get_office_themes(office_id, db_id)

        return InvestorThemeListResponse(
            themes=themes,
            total=len(themes)
        )
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting themes for family office {office_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get office themes")


# ========================================
# Impact Analysis Endpoint
# ========================================

@router.get("/impact/{office_id}", response_model=ImpactAnalysis)
async def get_impact_analysis(
    office_id: int,
    db_id: Optional[str] = Query(None, description="Database configuration ID")
):
    """
    Get the latest ESG/impact analysis for a family office.

    Returns:
    - ESG scores (overall, environmental, social, governance)
    - Impact focus areas
    - Carbon footprint metrics
    - Diversity metrics
    - Reporting framework used
    """
    try:
        # Verify office exists
        if not FOCollectionService.office_exists(office_id, db_id):
            raise HTTPException(status_code=404, detail=f"Family office {office_id} not found")

        impact = FOCollectionService.get_impact_analysis(office_id, db_id)

        if not impact:
            raise HTTPException(
                status_code=404,
                detail=f"No impact analysis found for family office {office_id}"
            )

        return impact
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting impact analysis for family office {office_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get impact analysis")


# ========================================
# Statistics Endpoint
# ========================================

@router.get("/stats", response_model=FOCollectionStats)
async def get_fo_stats(
    db_id: Optional[str] = Query(None, description="Database configuration ID")
):
    """
    Get aggregate statistics for the Family Office collection.

    Returns:
    - Total counts (offices, contacts, interactions, co-investments, portfolio companies)
    - Total AUM amount
    - Breakdowns by office type, location, and status
    """
    try:
        stats = FOCollectionService.get_stats(db_id)
        return stats
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting FO stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get FO statistics")
