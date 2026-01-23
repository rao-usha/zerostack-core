"""Pydantic models for FO (Family Office) Collection API."""
from datetime import datetime, date
from typing import Optional, List, Any
from pydantic import BaseModel, Field


# ========================================
# Response Models - List View
# ========================================

class FamilyOfficeSummary(BaseModel):
    """Summary view of a family office for list endpoints."""
    id: int
    name: str
    aum: Optional[float] = None
    aum_currency: Optional[str] = None
    headquarters: Optional[str] = None
    family_name: Optional[str] = None
    office_type: Optional[str] = None
    investment_focus: Optional[str] = None
    status: Optional[str] = None

    class Config:
        from_attributes = True


class FOListResponse(BaseModel):
    """Paginated response for list of family offices."""
    offices: List[FamilyOfficeSummary]
    total: int
    page: int
    page_size: int
    total_pages: int


# ========================================
# Response Models - Related Entities
# ========================================

class FOContact(BaseModel):
    """Contact at a family office."""
    id: int
    family_office_id: int
    name: str
    title: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[str] = None
    is_primary: Optional[bool] = False
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class FOInteraction(BaseModel):
    """Interaction record with a family office."""
    id: int
    family_office_id: int
    interaction_type: Optional[str] = None
    interaction_date: Optional[date] = None
    subject: Optional[str] = None
    notes: Optional[str] = None
    outcome: Optional[str] = None
    follow_up_required: Optional[bool] = False
    follow_up_date: Optional[date] = None
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CoInvestment(BaseModel):
    """Co-investment opportunity or deal."""
    id: int
    family_office_id: int
    deal_name: Optional[str] = None
    deal_type: Optional[str] = None
    sector: Optional[str] = None
    investment_amount: Optional[float] = None
    investment_currency: Optional[str] = None
    status: Optional[str] = None
    close_date: Optional[date] = None
    description: Optional[str] = None
    lead_investor: Optional[str] = None
    co_investors: Optional[str] = None

    class Config:
        from_attributes = True


class PortfolioCompany(BaseModel):
    """Portfolio company owned by the family office."""
    id: int
    family_office_id: int
    company_name: Optional[str] = None
    sector: Optional[str] = None
    location: Optional[str] = None
    investment_date: Optional[date] = None
    investment_amount: Optional[float] = None
    ownership_percentage: Optional[float] = None
    current_valuation: Optional[float] = None
    status: Optional[str] = None
    description: Optional[str] = None

    class Config:
        from_attributes = True


class InvestorTheme(BaseModel):
    """Investment theme or focus area."""
    id: int
    family_office_id: int
    theme_name: Optional[str] = None
    theme_category: Optional[str] = None
    allocation_target: Optional[float] = None
    priority: Optional[str] = None
    description: Optional[str] = None
    active: Optional[bool] = True

    class Config:
        from_attributes = True


class ImpactAnalysis(BaseModel):
    """ESG and impact metrics for a family office."""
    id: int
    family_office_id: int
    analysis_date: Optional[date] = None
    esg_score: Optional[float] = None
    environmental_score: Optional[float] = None
    social_score: Optional[float] = None
    governance_score: Optional[float] = None
    impact_focus_areas: Optional[str] = None
    carbon_footprint: Optional[float] = None
    diversity_metrics: Optional[str] = None
    reporting_framework: Optional[str] = None
    notes: Optional[str] = None

    class Config:
        from_attributes = True


# ========================================
# Response Models - Full Detail
# ========================================

class FamilyOfficeDetail(BaseModel):
    """Full detail view of a family office with all related data."""
    id: int
    name: str
    aum: Optional[float] = None
    aum_currency: Optional[str] = None
    headquarters: Optional[str] = None
    family_name: Optional[str] = None
    office_type: Optional[str] = None
    investment_focus: Optional[str] = None
    status: Optional[str] = None
    description: Optional[str] = None
    founded_year: Optional[int] = None
    website: Optional[str] = None
    linkedin: Optional[str] = None
    investment_horizon: Optional[str] = None
    min_investment: Optional[float] = None
    max_investment: Optional[float] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # Nested related data
    contacts: List[FOContact] = []
    interactions: List[FOInteraction] = []
    co_investments: List[CoInvestment] = []
    portfolio_companies: List[PortfolioCompany] = []
    themes: List[InvestorTheme] = []

    class Config:
        from_attributes = True


# ========================================
# Response Models - Statistics
# ========================================

class FOCollectionStats(BaseModel):
    """Statistics for the FO collection."""
    total_offices: int
    total_contacts: int
    total_interactions: int
    total_co_investments: int
    total_portfolio_companies: int
    total_aum: Optional[float] = None
    total_aum_currency: Optional[str] = None
    offices_by_type: dict = {}
    offices_by_location: dict = {}
    offices_by_status: dict = {}


# ========================================
# Request Models - Search & Filters
# ========================================

class FOSearchFilters(BaseModel):
    """Search and filter parameters for family offices."""
    name: Optional[str] = Field(None, description="Filter by office name (partial match)")
    family_name: Optional[str] = Field(None, description="Filter by family name (partial match)")
    headquarters: Optional[str] = Field(None, description="Filter by headquarters location (partial match)")
    office_type: Optional[str] = Field(None, description="Filter by office type")
    investment_focus: Optional[str] = Field(None, description="Filter by investment focus (partial match)")
    min_aum: Optional[float] = Field(None, description="Minimum AUM amount")
    max_aum: Optional[float] = Field(None, description="Maximum AUM amount")
    status: Optional[str] = Field(None, description="Filter by status")

    # Pagination
    page: int = Field(1, ge=1, description="Page number")
    page_size: int = Field(50, ge=1, le=500, description="Items per page")

    # Sorting
    sort_by: str = Field("name", description="Field to sort by")
    sort_desc: bool = Field(False, description="Sort in descending order")


# ========================================
# Response Models - API Lists
# ========================================

class FOContactListResponse(BaseModel):
    """Response for list of FO contacts."""
    contacts: List[FOContact]
    total: int


class FOInteractionListResponse(BaseModel):
    """Response for list of FO interactions."""
    interactions: List[FOInteraction]
    total: int


class CoInvestmentListResponse(BaseModel):
    """Response for list of co-investments."""
    co_investments: List[CoInvestment]
    total: int


class PortfolioCompanyListResponse(BaseModel):
    """Response for list of portfolio companies."""
    portfolio_companies: List[PortfolioCompany]
    total: int


class InvestorThemeListResponse(BaseModel):
    """Response for list of investor themes."""
    themes: List[InvestorTheme]
    total: int
