"""Insights API router with full CRUD operations."""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional
from uuid import UUID
from sqlmodel import Session

from db_session import get_session
from domains.insights.service import InsightsService
from domains.insights.models import (
    InsightGenerateRequest,
    InsightReportResponse,
    InsightListResponse,
)

router = APIRouter(prefix="/insights", tags=["insights"])

# Service instance
insights_service = InsightsService()


@router.post("/generate", response_model=InsightReportResponse, status_code=201)
async def generate_insights(
    request: InsightGenerateRequest,
    session: Session = Depends(get_session),
):
    """
    Generate insights for a dataset.

    Analyzes the dataset and generates comprehensive insights including:
    - Executive KPIs and performance scores
    - Trends, anomalies, and correlations
    - Growth metrics and risk indicators
    - Strategic recommendations

    By default, persists the generated report to the database.
    Set `persist: false` to generate without saving.
    """
    try:
        return insights_service.generate_insights(request, session)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate insights: {str(e)}")


@router.get("", response_model=InsightListResponse)
async def list_insights(
    dataset_id: Optional[UUID] = Query(None, description="Filter by dataset ID"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    session: Session = Depends(get_session),
):
    """
    List stored insight reports.

    Returns a paginated list of insight reports, optionally filtered by dataset.
    """
    return insights_service.list_insights(
        session=session,
        dataset_id=dataset_id,
        page=page,
        page_size=page_size,
    )


@router.get("/{insight_id}", response_model=InsightReportResponse)
async def get_insight(
    insight_id: UUID,
    session: Session = Depends(get_session),
):
    """
    Get a specific insight report by ID.

    Returns the full insight report with all analytics data.
    """
    result = insights_service.get_insight(insight_id, session)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Insight report {insight_id} not found")
    return result


@router.delete("/{insight_id}", status_code=204)
async def delete_insight(
    insight_id: UUID,
    session: Session = Depends(get_session),
):
    """
    Delete an insight report.

    Permanently removes the insight report from the database.
    """
    deleted = insights_service.delete_insight(insight_id, session)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Insight report {insight_id} not found")
    return None
