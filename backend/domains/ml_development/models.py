"""ML Model Development Pydantic models."""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


# Enums
class ModelFamily(str, Enum):
    """Model family types."""
    PRICING = "pricing"
    NEXT_BEST_ACTION = "next_best_action"
    LOCATION_SCORING = "location_scoring"
    FORECASTING = "forecasting"


class RecipeLevel(str, Enum):
    """Recipe level in inheritance hierarchy."""
    BASELINE = "baseline"
    INDUSTRY = "industry"
    CLIENT = "client"


class RecipeStatus(str, Enum):
    """Recipe status."""
    DRAFT = "draft"
    APPROVED = "approved"
    ARCHIVED = "archived"


class ModelStatus(str, Enum):
    """Model status."""
    DRAFT = "draft"
    STAGING = "staging"
    PRODUCTION = "production"
    RETIRED = "retired"


class RunType(str, Enum):
    """Run type."""
    TRAIN = "train"
    EVAL = "eval"
    BACKTEST = "backtest"


class RunStatus(str, Enum):
    """Run status."""
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


# Recipe models
class MLRecipe(BaseModel):
    """ML Recipe definition."""
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())
    
    id: str
    name: str
    model_family: ModelFamily
    level: RecipeLevel
    status: RecipeStatus = RecipeStatus.DRAFT
    parent_id: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class MLRecipeCreate(BaseModel):
    """Request to create an ML recipe."""
    name: str
    model_family: ModelFamily
    level: RecipeLevel
    parent_id: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    manifest: Dict[str, Any] = Field(default_factory=dict)


class MLRecipeUpdate(BaseModel):
    """Request to update an ML recipe."""
    name: Optional[str] = None
    status: Optional[RecipeStatus] = None
    tags: Optional[List[str]] = None


# Recipe Version models
class MLRecipeVersion(BaseModel):
    """ML Recipe version."""
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())
    
    version_id: str
    recipe_id: str
    version_number: str
    manifest_json: Dict[str, Any]
    diff_from_prev: Optional[Dict[str, Any]] = None
    created_by: Optional[str] = None
    created_at: datetime
    change_note: Optional[str] = None


class MLRecipeVersionCreate(BaseModel):
    """Request to create a recipe version."""
    recipe_id: str
    manifest_json: Dict[str, Any]
    change_note: Optional[str] = None
    created_by: Optional[str] = None


# Model models
class MLModel(BaseModel):
    """ML Model (registered artifact)."""
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())
    
    id: str
    name: str
    model_family: ModelFamily
    recipe_id: str
    recipe_version_id: str
    status: ModelStatus = ModelStatus.DRAFT
    owner: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class MLModelCreate(BaseModel):
    """Request to create an ML model."""
    name: str
    recipe_id: str
    recipe_version_id: str
    owner: Optional[str] = None


class MLModelUpdate(BaseModel):
    """Request to update an ML model."""
    name: Optional[str] = None
    status: Optional[ModelStatus] = None
    owner: Optional[str] = None


# Run models
class MLRun(BaseModel):
    """ML Run (training/evaluation)."""
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())
    
    id: str
    model_id: Optional[str] = None
    recipe_id: str
    recipe_version_id: str
    run_type: RunType
    status: RunStatus = RunStatus.QUEUED
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    metrics_json: Dict[str, Any] = Field(default_factory=dict)
    artifacts_json: Dict[str, Any] = Field(default_factory=dict)
    logs_text: Optional[str] = None


class MLRunCreate(BaseModel):
    """Request to create an ML run."""
    recipe_id: str
    recipe_version_id: str
    run_type: RunType
    model_id: Optional[str] = None


# Monitor Snapshot models
class MLMonitorSnapshot(BaseModel):
    """ML Model monitoring snapshot."""
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())
    
    id: str
    model_id: str
    captured_at: datetime
    performance_metrics_json: Dict[str, Any] = Field(default_factory=dict)
    drift_metrics_json: Dict[str, Any] = Field(default_factory=dict)
    data_freshness_json: Dict[str, Any] = Field(default_factory=dict)
    alerts_json: Dict[str, Any] = Field(default_factory=dict)


class MLMonitorSnapshotCreate(BaseModel):
    """Request to create a monitoring snapshot."""
    model_id: str
    performance_metrics_json: Dict[str, Any] = Field(default_factory=dict)
    drift_metrics_json: Dict[str, Any] = Field(default_factory=dict)
    data_freshness_json: Dict[str, Any] = Field(default_factory=dict)
    alerts_json: Dict[str, Any] = Field(default_factory=dict)


# Synthetic Example models
class MLSyntheticExample(BaseModel):
    """ML Synthetic example for recipe."""
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())
    
    id: str
    recipe_id: str
    dataset_schema_json: Dict[str, Any] = Field(default_factory=dict)
    sample_rows_json: List[Dict[str, Any]] = Field(default_factory=list)
    example_run_json: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class MLSyntheticExampleCreate(BaseModel):
    """Request to create a synthetic example."""
    recipe_id: str
    dataset_schema_json: Dict[str, Any] = Field(default_factory=dict)
    sample_rows_json: List[Dict[str, Any]] = Field(default_factory=list)
    example_run_json: Dict[str, Any] = Field(default_factory=dict)


# List responses
class RecipeListResponse(BaseModel):
    """Response for recipe list."""
    recipes: List[MLRecipe]
    total: int


class ModelListResponse(BaseModel):
    """Response for model list."""
    models: List[MLModel]
    total: int


class RunListResponse(BaseModel):
    """Response for run list."""
    runs: List[MLRun]
    total: int


# Chat models for ML chat assistant
class MLChatMessage(BaseModel):
    """Chat message for ML assistant."""
    role: str  # "user" | "assistant" | "system"
    content: str
    timestamp: Optional[datetime] = None


class MLChatRequest(BaseModel):
    """Request to ML chat assistant."""
    message: str
    provider: str = "openai"
    model: str = "gpt-4o"
    context: Optional[Dict[str, Any]] = None
    recipe_id: Optional[str] = None


class MLChatResponse(BaseModel):
    """Response from ML chat assistant."""
    message: str
    suggested_changes: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


