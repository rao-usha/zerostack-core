"""Evaluation API router."""
from fastapi import APIRouter, HTTPException
from typing import List, Optional
from uuid import UUID
from domains.evaluations.models import (
    Evaluation, EvaluationCreate, Scenario, ScenarioCreate,
    EvaluationReport, EvaluationStatus
)
from domains.evaluations.service import EvaluationRunner, ScenarioService, ReportService

router = APIRouter(prefix="/evaluations", tags=["evaluations"])

evaluation_runner = EvaluationRunner()
scenario_service = ScenarioService()
report_service = ReportService()


@router.post("", response_model=Evaluation, status_code=201)
async def create_evaluation(evaluation: EvaluationCreate):
    """Create and run an evaluation."""
    raise HTTPException(status_code=501, detail="Not implemented")


@router.get("", response_model=List[Evaluation])
async def list_evaluations(
    model_id: Optional[UUID] = None,
    status: Optional[EvaluationStatus] = None
):
    """List evaluations."""
    raise HTTPException(status_code=501, detail="Not implemented")


@router.get("/{evaluation_id}", response_model=Evaluation)
async def get_evaluation(evaluation_id: UUID):
    """Get an evaluation."""
    raise HTTPException(status_code=501, detail="Not implemented")


@router.post("/{evaluation_id}/cancel")
async def cancel_evaluation(evaluation_id: UUID):
    """Cancel a running evaluation."""
    raise HTTPException(status_code=501, detail="Not implemented")


@router.post("/scenarios", response_model=Scenario, status_code=201)
async def create_scenario(scenario: ScenarioCreate):
    """Create a scenario."""
    raise HTTPException(status_code=501, detail="Not implemented")


@router.get("/scenarios", response_model=List[Scenario])
async def list_scenarios():
    """List scenarios."""
    raise HTTPException(status_code=501, detail="Not implemented")


@router.get("/{evaluation_id}/report", response_model=EvaluationReport)
async def get_evaluation_report(evaluation_id: UUID):
    """Get evaluation report."""
    raise HTTPException(status_code=501, detail="Not implemented")

