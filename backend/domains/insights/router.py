"""Insights API router."""
from fastapi import APIRouter, HTTPException
from typing import List, Optional
from uuid import UUID
from domains.insights.models import Insight, InsightCreate, InsightReport
from domains.insights.service import InsightsService

router = APIRouter(prefix="/insights", tags=["insights"])

insights_service = InsightsService()


@router.post("", response_model=Insight, status_code=201)
async def create_insight(insight: InsightCreate):
    """Create an insight."""
    raise HTTPException(status_code=501, detail="Not implemented")


@router.get("", response_model=List[Insight])
async def list_insights(
    dataset_id: Optional[UUID] = None,
    model_id: Optional[UUID] = None,
    insight_type: Optional[str] = None
):
    """List insights."""
    raise HTTPException(status_code=501, detail="Not implemented")


@router.get("/{insight_id}", response_model=Insight)
async def get_insight(insight_id: UUID):
    """Get an insight."""
    raise HTTPException(status_code=501, detail="Not implemented")


@router.post("/reports/generate", response_model=InsightReport, status_code=201)
async def generate_report(
    dataset_id: Optional[UUID] = None,
    model_id: Optional[UUID] = None,
    title: Optional[str] = None
):
    """Generate an insights report."""
    raise HTTPException(status_code=501, detail="Not implemented")

