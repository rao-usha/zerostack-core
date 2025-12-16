"""Pydantic models for Evaluation Packs."""
from datetime import datetime
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum


# Enums
class PackStatus(str, Enum):
    draft = "draft"
    approved = "approved"
    archived = "archived"


class EvalStatus(str, Enum):
    pass_ = "pass"
    warn = "warn"
    fail = "fail"


class MetricDirection(str, Enum):
    higher_is_better = "higher_is_better"
    lower_is_better = "lower_is_better"


# Pack Definition Schema
class MetricThreshold(BaseModel):
    promote: Optional[float] = None
    warn: Optional[float] = None
    fail: Optional[float] = None
    
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())


class MetricDefinition(BaseModel):
    key: str
    display_name: str
    compute: str  # e.g., "MAPE", "RMSE", "uplift", "rank_correlation"
    thresholds: MetricThreshold
    direction: MetricDirection
    
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())


class SliceDefinition(BaseModel):
    dimension: str
    values: Optional[List[str]] = None
    
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())


class ComparatorDefinition(BaseModel):
    type: str  # "baseline" | "prior_model" | "rules_engine"
    reference_id: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())


class EconomicMapping(BaseModel):
    metric_key: str
    dollar_per_unit: float
    unit_label: str
    
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())


class PackDefinition(BaseModel):
    """The pack_json structure."""
    id: str
    name: str
    model_family: str
    description: str
    metrics: List[MetricDefinition]
    slices: Optional[List[SliceDefinition]] = []
    comparators: Optional[List[ComparatorDefinition]] = []
    economic_mapping: Optional[List[EconomicMapping]] = []
    outputs: Optional[Dict[str, Any]] = {}
    
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())


# Evaluation Pack
class EvaluationPackBase(BaseModel):
    name: str
    model_family: str
    status: PackStatus = PackStatus.draft
    tags: List[str] = []
    
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())


class EvaluationPackCreate(EvaluationPackBase):
    id: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())


class EvaluationPackUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[PackStatus] = None
    tags: Optional[List[str]] = None
    
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())


class EvaluationPack(EvaluationPackBase):
    id: str
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())


# Evaluation Pack Version
class EvaluationPackVersionBase(BaseModel):
    pack_id: str
    version_number: str
    pack_json: PackDefinition
    change_note: Optional[str] = None
    created_by: Optional[str] = "system"
    
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())


class EvaluationPackVersionCreate(EvaluationPackVersionBase):
    version_id: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())


class EvaluationPackVersion(EvaluationPackVersionBase):
    version_id: str
    diff_from_prev: Optional[Dict[str, Any]] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())


# Recipe Evaluation Pack Association
class RecipePackAttach(BaseModel):
    recipe_id: str
    pack_id: str
    
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())


# Evaluation Result
class EvaluationResultCreate(BaseModel):
    run_id: str
    pack_id: str
    pack_version_id: str
    
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())


class EvaluationResult(BaseModel):
    id: str
    run_id: str
    pack_id: str
    pack_version_id: str
    executed_at: datetime
    status: EvalStatus
    results_json: Dict[str, Any]
    summary_text: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())


# Monitor Evaluation Snapshot
class MonitorEvaluationSnapshotCreate(BaseModel):
    model_id: str
    pack_id: str
    pack_version_id: str
    
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())


class MonitorEvaluationSnapshot(BaseModel):
    id: str
    model_id: str
    captured_at: datetime
    pack_id: str
    pack_version_id: str
    status: EvalStatus
    results_json: Dict[str, Any]
    
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())


# List responses
class PackListResponse(BaseModel):
    packs: List[EvaluationPack]
    total: int
    
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())


class EvaluationResultListResponse(BaseModel):
    results: List[EvaluationResult]
    total: int
    
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())


class MonitorSnapshotListResponse(BaseModel):
    snapshots: List[MonitorEvaluationSnapshot]
    total: int
    
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

