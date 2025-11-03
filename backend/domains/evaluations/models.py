"""Evaluation models."""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime
from enum import Enum


class EvaluationStatus(str, Enum):
    """Evaluation status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Metric(BaseModel):
    """Evaluation metric."""
    name: str
    value: float
    unit: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Scenario(BaseModel):
    """Evaluation scenario."""
    id: UUID
    name: str
    description: Optional[str] = None
    test_data_id: Optional[UUID] = None
    expected_outcomes: Dict[str, Any] = Field(default_factory=dict)
    config: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        from_attributes = True


class ScenarioCreate(BaseModel):
    """Request to create a scenario."""
    name: str
    description: Optional[str] = None
    test_data_id: Optional[UUID] = None
    expected_outcomes: Dict[str, Any] = Field(default_factory=dict)
    config: Dict[str, Any] = Field(default_factory=dict)


class Evaluation(BaseModel):
    """Evaluation run."""
    id: UUID
    name: str
    description: Optional[str] = None
    model_id: Optional[UUID] = None
    dataset_id: Optional[UUID] = None
    scenario_id: Optional[UUID] = None
    status: EvaluationStatus = EvaluationStatus.PENDING
    metrics: List[Metric] = Field(default_factory=list)
    results: Dict[str, Any] = Field(default_factory=dict)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[UUID] = None
    
    class Config:
        from_attributes = True


class EvaluationCreate(BaseModel):
    """Request to create an evaluation."""
    name: str
    description: Optional[str] = None
    model_id: Optional[UUID] = None
    dataset_id: Optional[UUID] = None
    scenario_id: Optional[UUID] = None
    config: Dict[str, Any] = Field(default_factory=dict)


class EvaluationReport(BaseModel):
    """Evaluation report."""
    evaluation_id: UUID
    summary: Dict[str, Any] = Field(default_factory=dict)
    metrics: List[Metric] = Field(default_factory=list)
    scenarios: List[Scenario] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=datetime.utcnow)

