"""Pydantic models for LP Collection API."""
from datetime import datetime, date
from typing import Optional, List, Any
from pydantic import BaseModel, Field


# ========================================
# Response Models - List View
# ========================================

class LPFundSummary(BaseModel):
    """Summary view of an LP fund for list endpoints."""
    id: int
    fund_name: str
    lp_name: Optional[str] = None
    commitment: Optional[float] = None
    commitment_currency: Optional[str] = None
    vintage_year: Optional[int] = None
    strategy: Optional[str] = None
    fund_type: Optional[str] = None
    status: Optional[str] = None

    class Config:
        from_attributes = True


class LPFundListResponse(BaseModel):
    """Paginated response for list of LP funds."""
    funds: List[LPFundSummary]
    total: int
    page: int
    page_size: int
    total_pages: int


# ========================================
# Response Models - Related Entities
# ========================================

class LPKeyContact(BaseModel):
    """Key contact at an LP organization."""
    id: int
    fund_id: int
    name: str
    title: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[str] = None
    is_primary: Optional[bool] = False
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class LPDocumentSummary(BaseModel):
    """Summary view of an LP document."""
    id: int
    fund_id: int
    document_type: Optional[str] = None
    document_name: Optional[str] = None
    document_date: Optional[date] = None
    source_url: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class LPDocumentTextSection(BaseModel):
    """Extracted text section from an LP document."""
    id: int
    document_id: int
    section_name: Optional[str] = None
    section_text: Optional[str] = None
    page_number: Optional[int] = None
    section_order: Optional[int] = None

    class Config:
        from_attributes = True


class LPDocumentDetail(BaseModel):
    """Full detail view of an LP document with text sections."""
    id: int
    fund_id: int
    document_type: Optional[str] = None
    document_name: Optional[str] = None
    document_date: Optional[date] = None
    source_url: Optional[str] = None
    created_at: Optional[datetime] = None
    text_sections: List[LPDocumentTextSection] = []

    class Config:
        from_attributes = True


class LPStrategyThematicTag(BaseModel):
    """Thematic tag associated with a strategy snapshot."""
    id: int
    strategy_snapshot_id: int
    tag_name: str
    tag_category: Optional[str] = None
    weight: Optional[float] = None

    class Config:
        from_attributes = True


class LPStrategySnapshot(BaseModel):
    """Strategy allocation snapshot with thematic tags."""
    id: int
    fund_id: int
    snapshot_date: Optional[date] = None
    strategy_name: Optional[str] = None
    allocation_percentage: Optional[float] = None
    target_return: Optional[float] = None
    risk_tolerance: Optional[str] = None
    notes: Optional[str] = None
    thematic_tags: List[LPStrategyThematicTag] = []

    class Config:
        from_attributes = True


class LPAssetClassAllocation(BaseModel):
    """Target allocation by asset class."""
    id: int
    fund_id: int
    asset_class: Optional[str] = None
    target_allocation: Optional[float] = None
    current_allocation: Optional[float] = None
    min_allocation: Optional[float] = None
    max_allocation: Optional[float] = None
    as_of_date: Optional[date] = None

    class Config:
        from_attributes = True


class LPAssetClassProjection(BaseModel):
    """Projected allocation over time."""
    id: int
    fund_id: int
    asset_class: Optional[str] = None
    projection_date: Optional[date] = None
    projected_allocation: Optional[float] = None
    confidence_level: Optional[str] = None
    scenario: Optional[str] = None

    class Config:
        from_attributes = True


class LPManagerExposure(BaseModel):
    """Manager or vehicle exposure data."""
    id: int
    fund_id: int
    manager_name: Optional[str] = None
    vehicle_name: Optional[str] = None
    exposure_amount: Optional[float] = None
    exposure_percentage: Optional[float] = None
    asset_class: Optional[str] = None
    strategy: Optional[str] = None
    vintage_year: Optional[int] = None
    as_of_date: Optional[date] = None

    class Config:
        from_attributes = True


# ========================================
# Response Models - Full Detail
# ========================================

class LPFundDetail(BaseModel):
    """Full detail view of an LP fund with all related data."""
    id: int
    fund_name: str
    lp_name: Optional[str] = None
    commitment: Optional[float] = None
    commitment_currency: Optional[str] = None
    vintage_year: Optional[int] = None
    strategy: Optional[str] = None
    fund_type: Optional[str] = None
    status: Optional[str] = None
    description: Optional[str] = None
    aum: Optional[float] = None
    headquarters: Optional[str] = None
    website: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # Nested related data
    contacts: List[LPKeyContact] = []
    documents: List[LPDocumentSummary] = []
    strategy_snapshots: List[LPStrategySnapshot] = []
    allocations: List[LPAssetClassAllocation] = []
    projections: List[LPAssetClassProjection] = []
    exposures: List[LPManagerExposure] = []

    class Config:
        from_attributes = True


# ========================================
# Response Models - Statistics
# ========================================

class LPCollectionStats(BaseModel):
    """Statistics for the LP collection."""
    total_funds: int
    total_contacts: int
    total_documents: int
    total_commitment: Optional[float] = None
    total_commitment_currency: Optional[str] = None
    funds_by_strategy: dict = {}
    funds_by_vintage: dict = {}
    funds_by_status: dict = {}


# ========================================
# Request Models - Search & Filters
# ========================================

class LPSearchFilters(BaseModel):
    """Search and filter parameters for LP funds."""
    lp_name: Optional[str] = Field(None, description="Filter by LP name (partial match)")
    fund_name: Optional[str] = Field(None, description="Filter by fund name (partial match)")
    fund_type: Optional[str] = Field(None, description="Filter by fund type")
    strategy: Optional[str] = Field(None, description="Filter by strategy")
    vintage_year: Optional[int] = Field(None, description="Filter by vintage year")
    vintage_year_min: Optional[int] = Field(None, description="Minimum vintage year")
    vintage_year_max: Optional[int] = Field(None, description="Maximum vintage year")
    min_commitment: Optional[float] = Field(None, description="Minimum commitment amount")
    max_commitment: Optional[float] = Field(None, description="Maximum commitment amount")
    status: Optional[str] = Field(None, description="Filter by status")

    # Pagination
    page: int = Field(1, ge=1, description="Page number")
    page_size: int = Field(50, ge=1, le=500, description="Items per page")

    # Sorting
    sort_by: str = Field("fund_name", description="Field to sort by")
    sort_desc: bool = Field(False, description="Sort in descending order")


# ========================================
# Response Models - API Lists
# ========================================

class LPContactListResponse(BaseModel):
    """Response for list of LP contacts."""
    contacts: List[LPKeyContact]
    total: int


class LPDocumentListResponse(BaseModel):
    """Response for list of LP documents."""
    documents: List[LPDocumentSummary]
    total: int


class LPAllocationListResponse(BaseModel):
    """Response for list of LP allocations."""
    allocations: List[LPAssetClassAllocation]
    total: int


class LPExposureListResponse(BaseModel):
    """Response for list of LP exposures."""
    exposures: List[LPManagerExposure]
    total: int
