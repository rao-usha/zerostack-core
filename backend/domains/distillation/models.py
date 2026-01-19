"""
Distillation Workbench Pydantic models for API requests/responses.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID
from enum import Enum


# ============================================
# Enums
# ============================================

class TaskType(str, Enum):
    """Types of distillation tasks."""
    QA = "qa"
    SUMMARY = "summary"
    INSTRUCTION = "instruction"
    FREEFORM = "freeform"


class TriggerType(str, Enum):
    """How a run was triggered."""
    MANUAL = "manual"
    SCHEDULED = "scheduled"
    INTERACTIVE = "interactive"


class RunStatus(str, Enum):
    """Status of a distillation run."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class BankedStatus(str, Enum):
    """Status of a banked response."""
    DRAFT = "draft"
    REVIEWED = "reviewed"
    APPROVED = "approved"
    REJECTED = "rejected"


class ComparisonType(str, Enum):
    """Type of model comparison."""
    SIDE_BY_SIDE = "side_by_side"
    BLIND = "blind"
    AB_PREFERENCE = "ab_preference"


class VoteType(str, Enum):
    """Type of vote."""
    WINNER = "winner"
    RANKING = "ranking"
    RATING = "rating"


class DatasetType(str, Enum):
    """Type of dataset."""
    TRAINING = "training"
    EVALUATION = "evaluation"
    BENCHMARK = "benchmark"


class DatasetStatus(str, Enum):
    """Status of a dataset."""
    DRAFT = "draft"
    BUILDING = "building"
    READY = "ready"
    EXPORTED = "exported"


# ============================================
# Domain & Topic Models
# ============================================

class DomainBase(BaseModel):
    """Base domain model."""
    name: str = Field(..., max_length=100)
    description: Optional[str] = None
    icon: Optional[str] = Field(default=None, max_length=50)
    color: Optional[str] = Field(default=None, max_length=7)


class DomainCreate(DomainBase):
    """Request to create a domain."""
    pass


class DomainUpdate(BaseModel):
    """Request to update a domain."""
    name: Optional[str] = Field(default=None, max_length=100)
    description: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None


class DomainResponse(DomainBase):
    """Domain response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    created_at: datetime
    updated_at: datetime
    topic_count: Optional[int] = None


class TopicBase(BaseModel):
    """Base topic model."""
    name: str = Field(..., max_length=100)
    description: Optional[str] = None
    parent_topic_id: Optional[UUID] = None


class TopicCreate(TopicBase):
    """Request to create a topic."""
    domain_id: UUID


class TopicUpdate(BaseModel):
    """Request to update a topic."""
    name: Optional[str] = Field(default=None, max_length=100)
    description: Optional[str] = None
    parent_topic_id: Optional[UUID] = None


class TopicResponse(TopicBase):
    """Topic response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    domain_id: UUID
    created_at: datetime


class TagBase(BaseModel):
    """Base tag model."""
    name: str = Field(..., max_length=100)
    color: Optional[str] = Field(default=None, max_length=7)


class TagCreate(TagBase):
    """Request to create a tag."""
    pass


class TagResponse(TagBase):
    """Tag response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    created_at: datetime


# ============================================
# Task Models
# ============================================

class TaskVariable(BaseModel):
    """Variable definition for a task template."""
    name: str
    type: str = "string"  # 'string', 'number', 'boolean', 'list'
    default: Optional[Any] = None
    required: bool = False
    description: Optional[str] = None


class TaskBase(BaseModel):
    """Base task model."""
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    task_type: TaskType
    prompt_template: str
    system_prompt: Optional[str] = None
    variables: List[TaskVariable] = Field(default_factory=list)
    target_models: List[str] = Field(..., min_length=1)


class TaskCreate(TaskBase):
    """Request to create a task."""
    domain_id: Optional[UUID] = None
    topic_id: Optional[UUID] = None
    schedule_cron: Optional[str] = None
    schedule_enabled: bool = False


class TaskUpdate(BaseModel):
    """Request to update a task."""
    name: Optional[str] = Field(default=None, max_length=255)
    description: Optional[str] = None
    prompt_template: Optional[str] = None
    system_prompt: Optional[str] = None
    variables: Optional[List[TaskVariable]] = None
    target_models: Optional[List[str]] = None
    domain_id: Optional[UUID] = None
    topic_id: Optional[UUID] = None
    schedule_cron: Optional[str] = None
    schedule_enabled: Optional[bool] = None
    is_active: Optional[bool] = None


class TaskResponse(TaskBase):
    """Task response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    domain_id: Optional[UUID]
    topic_id: Optional[UUID]
    schedule_cron: Optional[str]
    schedule_enabled: bool
    is_active: bool
    created_by: Optional[str]
    created_at: datetime
    updated_at: datetime


# ============================================
# Run Models
# ============================================

class RunCreate(BaseModel):
    """Request to create/execute a run."""
    task_id: Optional[UUID] = None
    # For ad-hoc runs
    ad_hoc_prompt: Optional[str] = None
    ad_hoc_system_prompt: Optional[str] = None
    ad_hoc_models: Optional[List[str]] = None
    # Variables
    variables: Dict[str, Any] = Field(default_factory=dict)
    # Organization
    domain_id: Optional[UUID] = None
    topic_id: Optional[UUID] = None


class RunResponse(BaseModel):
    """Run response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    task_id: Optional[UUID]
    ad_hoc_prompt: Optional[str]
    ad_hoc_models: Optional[List[str]]
    variables_used: Dict[str, Any]
    trigger_type: TriggerType
    domain_id: Optional[UUID]
    topic_id: Optional[UUID]
    status: RunStatus
    error_message: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_by: Optional[str]
    created_at: datetime
    response_count: Optional[int] = None


# ============================================
# Response Models
# ============================================

class ResponseResponse(BaseModel):
    """Model response from distillation."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    run_id: UUID
    provider: str
    model: str
    prompt_sent: str
    system_prompt_used: Optional[str]
    response_text: str
    tokens_input: Optional[int]
    tokens_output: Optional[int]
    latency_ms: Optional[int]
    domain_id: Optional[UUID]
    topic_id: Optional[UUID]
    created_at: datetime
    tags: List[TagResponse] = Field(default_factory=list)


class ResponseUpdate(BaseModel):
    """Request to update a response."""
    domain_id: Optional[UUID] = None
    topic_id: Optional[UUID] = None
    tag_ids: Optional[List[UUID]] = None
    quality_rating: Optional[int] = None  # 1-5 rating


# ============================================
# Bank Models
# ============================================

class BankCreate(BaseModel):
    """Request to bank a response."""
    response_id: UUID
    domain_id: Optional[UUID] = None
    topic_id: Optional[UUID] = None
    quality_score: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    notes: Optional[str] = None


class BankedResponse(BaseModel):
    """Banked response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    response_id: UUID
    domain_id: Optional[UUID]
    topic_id: Optional[UUID]
    quality_score: Optional[float]
    notes: Optional[str]
    status: BankedStatus
    banked_by: Optional[str]
    banked_at: datetime
    reviewed_by: Optional[str]
    reviewed_at: Optional[datetime]
    # Include the original response
    response: Optional[ResponseResponse] = None


class BankedUpdate(BaseModel):
    """Request to update a banked response."""
    domain_id: Optional[UUID] = None
    topic_id: Optional[UUID] = None
    quality_score: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    notes: Optional[str] = None
    status: Optional[BankedStatus] = None


# ============================================
# Comparison Models
# ============================================

class ComparisonCreate(BaseModel):
    """Request to create a comparison."""
    response_ids: List[UUID] = Field(..., min_length=2)
    comparison_type: ComparisonType = ComparisonType.SIDE_BY_SIDE
    prompt_used: str


class VoteCreate(BaseModel):
    """Request to submit a vote."""
    comparison_id: UUID
    vote_type: VoteType
    winner_response_id: Optional[UUID] = None
    rankings: Optional[List[Dict[str, Any]]] = None  # [{response_id, rank}]
    ratings: Optional[List[Dict[str, Any]]] = None   # [{response_id, score}]
    notes: Optional[str] = None


class VoteResponse(BaseModel):
    """Vote response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    comparison_id: UUID
    winner_response_id: Optional[UUID]
    vote_type: VoteType
    rankings: Optional[List[Dict[str, Any]]]
    ratings: Optional[List[Dict[str, Any]]]
    voter: Optional[str]
    voter_type: str
    notes: Optional[str]
    created_at: datetime


class ComparisonResponse(BaseModel):
    """Comparison response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    run_id: Optional[UUID]
    comparison_type: ComparisonType
    prompt_used: str
    status: str
    created_by: Optional[str]
    created_at: datetime
    responses: List[ResponseResponse] = Field(default_factory=list)
    votes: List[VoteResponse] = Field(default_factory=list)


# ============================================
# Interactive Chat Models
# ============================================

class InteractiveChatRequest(BaseModel):
    """Request for interactive chat with SOTA models."""
    message: str = Field(..., min_length=1, max_length=50000)
    system_prompt: Optional[str] = None
    models: List[str] = Field(default=["gpt-4o"])
    domain_id: Optional[UUID] = None
    topic_id: Optional[UUID] = None
    # If True, automatically create a comparison for multi-model runs
    create_comparison: bool = False


class InteractiveChatResponse(BaseModel):
    """Response from interactive chat."""
    run_id: UUID
    responses: List[ResponseResponse]
    comparison_id: Optional[UUID] = None


# ============================================
# Dataset Models
# ============================================

class DatasetCreate(BaseModel):
    """Request to create a dataset."""
    name: str = Field(..., max_length=255)
    version: str = Field(..., max_length=50)
    description: Optional[str] = None
    dataset_type: DatasetType
    domain_id: Optional[UUID] = None
    selection_criteria: Dict[str, Any] = Field(default_factory=dict)


class DatasetResponse(BaseModel):
    """Dataset response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    name: str
    version: str
    description: Optional[str]
    dataset_type: DatasetType
    domain_id: Optional[UUID]
    selection_criteria: Dict[str, Any]
    item_count: int
    export_format: Optional[str]
    export_path: Optional[str]
    status: DatasetStatus
    created_by: Optional[str]
    created_at: datetime
    updated_at: datetime


class DatasetItemAdd(BaseModel):
    """Request to add items to a dataset."""
    banked_ids: Optional[List[UUID]] = None
    structured_ids: Optional[List[UUID]] = None
    split: str = "train"


# ============================================
# Structured Extraction Models (Phase 5)
# ============================================

class StructuredCreate(BaseModel):
    """Request to create a structured extraction."""
    banked_id: UUID
    schema_name: str = Field(..., max_length=100)
    structured_data: Dict[str, Any]
    extraction_method: str = "manual"


class StructuredUpdate(BaseModel):
    """Request to update structured data."""
    structured_data: Dict[str, Any]


class StructuredResponse(BaseModel):
    """Structured extraction response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    banked_id: UUID
    schema_name: str
    structured_data: Dict[str, Any]
    extraction_method: Optional[str]
    extracted_by: Optional[str]
    extracted_at: datetime


class LLMExtractionRequest(BaseModel):
    """Request for LLM-assisted extraction."""
    banked_id: UUID
    schema_name: str


class SchemaFieldDefinition(BaseModel):
    """Definition of a field in a schema."""
    type: str
    required: bool = False
    description: Optional[str] = None
    enum: Optional[List[str]] = None


class SchemaDefinition(BaseModel):
    """Schema definition for structuring."""
    name: str
    description: str
    fields: Dict[str, SchemaFieldDefinition]


# ============================================
# Expert Review Models (Phase 6)
# ============================================

class ReviewStatus(str, Enum):
    """Status of a review item."""
    PENDING = "pending"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_REVISION = "needs_revision"


class ReviewQueueCreate(BaseModel):
    """Request to create a review queue."""
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    domain_id: Optional[UUID] = None
    topic_id: Optional[UUID] = None
    min_quality_score: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    assigned_experts: List[str] = Field(default_factory=list)


class ReviewQueueUpdate(BaseModel):
    """Request to update a review queue."""
    name: Optional[str] = Field(default=None, max_length=255)
    description: Optional[str] = None
    domain_id: Optional[UUID] = None
    topic_id: Optional[UUID] = None
    min_quality_score: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    assigned_experts: Optional[List[str]] = None
    is_active: Optional[bool] = None


class ReviewQueueResponse(BaseModel):
    """Review queue response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    name: str
    description: Optional[str]
    domain_id: Optional[UUID]
    topic_id: Optional[UUID]
    min_quality_score: Optional[float]
    assigned_experts: List[str]
    is_active: bool
    created_by: Optional[str]
    created_at: datetime
    updated_at: datetime
    # Counts
    pending_count: Optional[int] = None
    completed_count: Optional[int] = None


class ReviewItemCreate(BaseModel):
    """Request to add items to a review queue."""
    banked_ids: List[UUID]
    priority: int = 0
    assigned_to: Optional[str] = None


class ReviewItemUpdate(BaseModel):
    """Request to update a review item."""
    status: Optional[ReviewStatus] = None
    assigned_to: Optional[str] = None
    review_notes: Optional[str] = None
    review_score: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    priority: Optional[int] = None


class ReviewItemResponse(BaseModel):
    """Review item response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    queue_id: UUID
    banked_id: UUID
    status: str
    assigned_to: Optional[str]
    review_notes: Optional[str]
    review_score: Optional[float]
    reviewed_by: Optional[str]
    reviewed_at: Optional[datetime]
    priority: int
    created_at: datetime
    # Include banked response details
    banked: Optional[BankedResponse] = None


class ReviewAction(BaseModel):
    """Request to take action on a review item."""
    action: ReviewStatus
    review_notes: Optional[str] = None
    review_score: Optional[float] = Field(default=None, ge=0.0, le=1.0)


class ReviewExportRequest(BaseModel):
    """Request to export review items."""
    export_format: str = Field(..., pattern="^(csv|json)$")


class ReviewExportResponse(BaseModel):
    """Review export response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    queue_id: UUID
    export_format: str
    file_path: Optional[str]
    item_count: int
    imported_at: Optional[datetime]
    items_updated: Optional[int]
    exported_by: Optional[str]
    exported_at: datetime


class ReviewImportRequest(BaseModel):
    """Request to import review ratings."""
    items: List[Dict[str, Any]]  # [{id, status, review_score, review_notes}]


# ============================================
# List Responses
# ============================================

class DomainListResponse(BaseModel):
    """List of domains."""
    domains: List[DomainResponse]
    total: int


class TopicListResponse(BaseModel):
    """List of topics."""
    topics: List[TopicResponse]
    total: int


class TaskListResponse(BaseModel):
    """List of tasks."""
    tasks: List[TaskResponse]
    total: int


class RunListResponse(BaseModel):
    """List of runs."""
    runs: List[RunResponse]
    total: int


class ResponseListResponse(BaseModel):
    """List of responses."""
    responses: List[ResponseResponse]
    total: int


class BankedListResponse(BaseModel):
    """List of banked responses."""
    banked: List[BankedResponse]
    total: int


class DatasetListResponse(BaseModel):
    """List of datasets."""
    datasets: List[DatasetResponse]
    total: int
