"""Pydantic schemas for API validation."""
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional, Literal
from datetime import datetime
from enum import Enum


class ExampleTypeEnum(str, Enum):
    """Example type enum."""
    INSTRUCTION = "instruction"
    QA = "qa"
    TASK = "task"


class DatasetKindEnum(str, Enum):
    """Dataset kind enum."""
    TRAIN = "train"
    EVAL = "eval"
    SYNTHETIC = "synthetic"
    FINETUNE_PACK = "finetune_pack"


# ContextDoc schemas
class ContextDocCreate(BaseModel):
    """Create a ContextDoc."""
    id: str
    title: str
    version: str
    body_text: str
    metadata_json: Dict[str, Any] = Field(default_factory=dict)
    nex_context_id: Optional[str] = None
    nex_context_version: Optional[str] = None


class ContextDocResponse(BaseModel):
    """ContextDoc response."""
    id: str
    title: str
    version: str
    body_text: str
    metadata_json: Dict[str, Any]
    nex_context_id: Optional[str]
    nex_context_version: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


# ContextVariant schemas
class ContextVariantCreate(BaseModel):
    """Create a ContextVariant."""
    id: str
    context_id: str
    domain: Optional[str] = None
    persona: Optional[str] = None
    task: Optional[str] = None
    style: Optional[str] = None
    constraints_json: Dict[str, Any] = Field(default_factory=dict)
    body_text: str
    parent_variant_id: Optional[str] = None


class ContextVariantResponse(BaseModel):
    """ContextVariant response."""
    id: str
    context_id: str
    domain: Optional[str]
    persona: Optional[str]
    task: Optional[str]
    style: Optional[str]
    constraints_json: Dict[str, Any]
    body_text: str
    parent_variant_id: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


# Aggregator schemas
class AggregateSampleRequest(BaseModel):
    """Request to sample/generate contexts."""
    context_id: Optional[str] = None  # If None, creates new
    variant_id: Optional[str] = None  # If None, creates new variant
    provider: str = "openai"
    model: str = "gpt-4o-mini"
    prompt: str = "Generate a comprehensive context document for {domain} domain."
    seed: Optional[int] = None
    domain: Optional[str] = None
    persona: Optional[str] = None
    task: Optional[str] = None


# SyntheticExample schemas
class SyntheticExampleCreate(BaseModel):
    """Create a SyntheticExample."""
    id: str
    variant_id: str
    example_type: ExampleTypeEnum
    input_json: Dict[str, Any]
    constraints_json: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)


class SyntheticExampleResponse(BaseModel):
    """SyntheticExample response."""
    id: str
    variant_id: str
    example_type: ExampleTypeEnum
    input_json: Dict[str, Any]
    constraints_json: Dict[str, Any]
    tags: List[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


# TeacherRun schemas
class TeacherRunCreate(BaseModel):
    """Create a TeacherRun."""
    id: str
    example_id: str
    provider: str
    model: str
    params_json: Dict[str, Any]


class TeacherRunResponse(BaseModel):
    """TeacherRun response."""
    id: str
    example_id: str
    provider: str
    model: str
    params_json: Dict[str, Any]
    output_json: Optional[Dict[str, Any]]
    usage_json: Optional[Dict[str, Any]]
    created_at: datetime
    
    class Config:
        from_attributes = True


# Targets schemas
class TargetsResponse(BaseModel):
    """Targets response."""
    id: str
    example_id: str
    y_text: str
    y_probs_json: Optional[Dict[str, Any]]
    y_scores_json: Optional[Dict[str, Any]]
    created_at: datetime
    
    class Config:
        from_attributes = True


# Dataset schemas
class DistillExamplesRequest(BaseModel):
    """Request to generate examples from variants."""
    variant_ids: List[str]
    example_type: ExampleTypeEnum
    quota_per_variant: int = 10
    rules: Dict[str, Any] = Field(default_factory=dict)


class DistillBuildRequest(BaseModel):
    """Build a dataset."""
    name: str
    version: str
    kind: DatasetKindEnum
    variant_ids: List[str]
    filters: Dict[str, Any] = Field(default_factory=dict)


# Variant composition schema
class VariantComposeRequest(BaseModel):
    """Compose a variant by mixing facets."""
    source_variant_ids: List[str] = Field(..., min_items=1)
    target_context_id: Optional[str] = None
    variant_id: Optional[str] = None
    domain: Optional[str] = None
    persona: Optional[str] = None
    task: Optional[str] = None
    style: Optional[str] = None
    constraints_json: Optional[Dict[str, Any]] = None
    composition_strategy: Literal["first", "concatenate", "merge"] = "first"


class DatasetManifestResponse(BaseModel):
    """DatasetManifest response."""
    id: str
    name: str
    version: str
    kind: DatasetKindEnum
    context_id: Optional[str]
    variant_ids: List[str]
    file_uris: List[str]
    filters_json: Dict[str, Any]
    created_at: datetime
    
    class Config:
        from_attributes = True
