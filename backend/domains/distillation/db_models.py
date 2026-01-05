"""
Distillation Workbench SQLModel database models.

These map directly to the database tables created in migration 015.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4
from sqlmodel import SQLModel, Field as SQLField, Column, Relationship
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from sqlalchemy import String


# ============================================
# Domain & Topic Hierarchy
# ============================================

class DistillationDomain(SQLModel, table=True):
    """Knowledge domain (Insurance, Finance, Retail, etc.)"""
    __tablename__ = "distillation_domains"
    
    id: Optional[UUID] = SQLField(default_factory=uuid4, primary_key=True)
    name: str = SQLField(max_length=100, unique=True)
    description: Optional[str] = None
    icon: Optional[str] = SQLField(default=None, max_length=50)
    color: Optional[str] = SQLField(default=None, max_length=7)
    created_at: datetime = SQLField(default_factory=datetime.utcnow)
    updated_at: datetime = SQLField(default_factory=datetime.utcnow)
    
    # Relationships
    topics: List["DistillationTopic"] = Relationship(back_populates="domain")


class DistillationTopic(SQLModel, table=True):
    """Topic within a domain (hierarchical)."""
    __tablename__ = "distillation_topics"
    
    id: Optional[UUID] = SQLField(default_factory=uuid4, primary_key=True)
    domain_id: UUID = SQLField(foreign_key="distillation_domains.id")
    name: str = SQLField(max_length=100)
    description: Optional[str] = None
    parent_topic_id: Optional[UUID] = SQLField(default=None, foreign_key="distillation_topics.id")
    created_at: datetime = SQLField(default_factory=datetime.utcnow)
    
    # Relationships
    domain: Optional[DistillationDomain] = Relationship(back_populates="topics")


class DistillationTag(SQLModel, table=True):
    """Freeform tags for organizing responses."""
    __tablename__ = "distillation_tags"
    
    id: Optional[UUID] = SQLField(default_factory=uuid4, primary_key=True)
    name: str = SQLField(max_length=100, unique=True)
    color: Optional[str] = SQLField(default=None, max_length=7)
    created_at: datetime = SQLField(default_factory=datetime.utcnow)


# ============================================
# Task Library
# ============================================

class DistillationTask(SQLModel, table=True):
    """Reusable task template for automated knowledge extraction."""
    __tablename__ = "distillation_tasks"
    
    model_config = {"protected_namespaces": ()}
    
    id: Optional[UUID] = SQLField(default_factory=uuid4, primary_key=True)
    name: str = SQLField(max_length=255)
    description: Optional[str] = None
    
    # Organization
    domain_id: Optional[UUID] = SQLField(default=None, foreign_key="distillation_domains.id")
    topic_id: Optional[UUID] = SQLField(default=None, foreign_key="distillation_topics.id")
    
    # Task configuration
    task_type: str = SQLField(max_length=50)  # 'qa', 'summary', 'instruction', 'freeform'
    prompt_template: str
    system_prompt: Optional[str] = None
    variables: List[Dict[str, Any]] = SQLField(default=[], sa_column=Column(JSONB))
    
    # Model targeting - stored as array of strings
    target_models: List[str] = SQLField(default=[], sa_column=Column(ARRAY(String)))
    
    # Scheduling
    schedule_cron: Optional[str] = SQLField(default=None, max_length=100)
    schedule_enabled: bool = SQLField(default=False)
    
    # Status
    is_active: bool = SQLField(default=True)
    
    # Metadata
    created_by: Optional[str] = SQLField(default=None, max_length=100)
    created_at: datetime = SQLField(default_factory=datetime.utcnow)
    updated_at: datetime = SQLField(default_factory=datetime.utcnow)


# ============================================
# Runs & Responses
# ============================================

class DistillationRun(SQLModel, table=True):
    """Execution of a task or ad-hoc prompt."""
    __tablename__ = "distillation_runs"
    
    model_config = {"protected_namespaces": ()}
    
    id: Optional[UUID] = SQLField(default_factory=uuid4, primary_key=True)
    task_id: Optional[UUID] = SQLField(default=None, foreign_key="distillation_tasks.id")
    
    # For ad-hoc/interactive runs
    ad_hoc_prompt: Optional[str] = None
    ad_hoc_system_prompt: Optional[str] = None
    ad_hoc_models: Optional[List[str]] = SQLField(default=None, sa_column=Column(ARRAY(String)))
    
    # Execution context
    variables_used: Dict[str, Any] = SQLField(default={}, sa_column=Column(JSONB))
    trigger_type: str = SQLField(max_length=20)  # 'manual', 'scheduled', 'interactive'
    
    # Organization
    domain_id: Optional[UUID] = SQLField(default=None, foreign_key="distillation_domains.id")
    topic_id: Optional[UUID] = SQLField(default=None, foreign_key="distillation_topics.id")
    
    # Status
    status: str = SQLField(default="pending", max_length=20)
    error_message: Optional[str] = None
    
    # Timing
    scheduled_for: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    created_by: Optional[str] = SQLField(default=None, max_length=100)
    created_at: datetime = SQLField(default_factory=datetime.utcnow)
    
    # Relationships
    responses: List["DistillationResponse"] = Relationship(back_populates="run")


class DistillationResponse(SQLModel, table=True):
    """Response from a SOTA model."""
    __tablename__ = "distillation_responses"
    
    model_config = {"protected_namespaces": ()}
    
    id: Optional[UUID] = SQLField(default_factory=uuid4, primary_key=True)
    run_id: UUID = SQLField(foreign_key="distillation_runs.id")
    
    # Model info
    provider: str = SQLField(max_length=50)
    model: str = SQLField(max_length=100)
    
    # Request/Response
    prompt_sent: str
    system_prompt_used: Optional[str] = None
    response_text: str
    
    # Metrics
    tokens_input: Optional[int] = None
    tokens_output: Optional[int] = None
    latency_ms: Optional[int] = None
    
    # Embedding for similarity search (stored separately due to pgvector)
    # embedding: Optional[List[float]] = SQLField(default=None, sa_column=Column(Vector(1536)))
    
    # Organization
    domain_id: Optional[UUID] = SQLField(default=None, foreign_key="distillation_domains.id")
    topic_id: Optional[UUID] = SQLField(default=None, foreign_key="distillation_topics.id")
    
    # Quality rating (1-5)
    quality_rating: Optional[int] = SQLField(default=None)
    
    created_at: datetime = SQLField(default_factory=datetime.utcnow)
    
    # Relationships
    run: Optional[DistillationRun] = Relationship(back_populates="responses")


class DistillationResponseTag(SQLModel, table=True):
    """Many-to-many link between responses and tags."""
    __tablename__ = "distillation_response_tags"
    
    response_id: UUID = SQLField(foreign_key="distillation_responses.id", primary_key=True)
    tag_id: UUID = SQLField(foreign_key="distillation_tags.id", primary_key=True)


# ============================================
# Banked Responses & Structuring
# ============================================

class DistillationBanked(SQLModel, table=True):
    """Curated/banked response for future use."""
    __tablename__ = "distillation_banked"
    
    id: Optional[UUID] = SQLField(default_factory=uuid4, primary_key=True)
    response_id: UUID = SQLField(foreign_key="distillation_responses.id")
    
    # Organization override
    domain_id: Optional[UUID] = SQLField(default=None, foreign_key="distillation_domains.id")
    topic_id: Optional[UUID] = SQLField(default=None, foreign_key="distillation_topics.id")
    
    # Curation
    quality_score: Optional[float] = None
    notes: Optional[str] = None
    
    # Status
    status: str = SQLField(default="draft", max_length=20)
    
    banked_by: Optional[str] = SQLField(default=None, max_length=100)
    banked_at: datetime = SQLField(default_factory=datetime.utcnow)
    reviewed_by: Optional[str] = SQLField(default=None, max_length=100)
    reviewed_at: Optional[datetime] = None


class DistillationStructured(SQLModel, table=True):
    """Structured extraction from a banked response."""
    __tablename__ = "distillation_structured"
    
    id: Optional[UUID] = SQLField(default_factory=uuid4, primary_key=True)
    banked_id: UUID = SQLField(foreign_key="distillation_banked.id")
    
    # The extracted structure
    schema_name: str = SQLField(max_length=100)  # 'qa_pair', 'instruction', 'summary'
    structured_data: Dict[str, Any] = SQLField(default={}, sa_column=Column(JSONB))
    
    # Extraction metadata
    extraction_method: Optional[str] = SQLField(default=None, max_length=50)
    extracted_by: Optional[str] = SQLField(default=None, max_length=100)
    extracted_at: datetime = SQLField(default_factory=datetime.utcnow)


# ============================================
# Comparisons & Voting
# ============================================

class DistillationComparison(SQLModel, table=True):
    """Model comparison session."""
    __tablename__ = "distillation_comparisons"
    
    id: Optional[UUID] = SQLField(default_factory=uuid4, primary_key=True)
    run_id: Optional[UUID] = SQLField(default=None, foreign_key="distillation_runs.id")
    
    comparison_type: str = SQLField(max_length=20)  # 'side_by_side', 'blind', 'ab_preference'
    prompt_used: str
    
    status: str = SQLField(default="pending", max_length=20)
    
    created_by: Optional[str] = SQLField(default=None, max_length=100)
    created_at: datetime = SQLField(default_factory=datetime.utcnow)


class DistillationComparisonResponse(SQLModel, table=True):
    """Response included in a comparison."""
    __tablename__ = "distillation_comparison_responses"
    
    comparison_id: UUID = SQLField(foreign_key="distillation_comparisons.id", primary_key=True)
    response_id: UUID = SQLField(foreign_key="distillation_responses.id", primary_key=True)
    display_order: Optional[int] = None
    display_label: Optional[str] = SQLField(default=None, max_length=10)


class DistillationVote(SQLModel, table=True):
    """Vote/preference on a comparison."""
    __tablename__ = "distillation_votes"
    
    id: Optional[UUID] = SQLField(default_factory=uuid4, primary_key=True)
    comparison_id: UUID = SQLField(foreign_key="distillation_comparisons.id")
    
    winner_response_id: Optional[UUID] = SQLField(default=None, foreign_key="distillation_responses.id")
    vote_type: str = SQLField(max_length=20)  # 'winner', 'ranking', 'rating'
    rankings: Optional[List[Dict[str, Any]]] = SQLField(default=None, sa_column=Column(JSONB))
    ratings: Optional[List[Dict[str, Any]]] = SQLField(default=None, sa_column=Column(JSONB))
    
    voter: Optional[str] = SQLField(default=None, max_length=100)
    voter_type: str = SQLField(default="user", max_length=20)
    notes: Optional[str] = None
    
    created_at: datetime = SQLField(default_factory=datetime.utcnow)


# ============================================
# Datasets
# ============================================

class DistillationDataset(SQLModel, table=True):
    """Curated dataset for training/evaluation."""
    __tablename__ = "distillation_datasets"
    
    id: Optional[UUID] = SQLField(default_factory=uuid4, primary_key=True)
    name: str = SQLField(max_length=255)
    version: str = SQLField(max_length=50)
    description: Optional[str] = None
    
    dataset_type: str = SQLField(max_length=50)  # 'training', 'evaluation', 'benchmark'
    
    domain_id: Optional[UUID] = SQLField(default=None, foreign_key="distillation_domains.id")
    
    selection_criteria: Dict[str, Any] = SQLField(default={}, sa_column=Column(JSONB))
    
    item_count: int = SQLField(default=0)
    
    export_format: Optional[str] = SQLField(default=None, max_length=20)
    export_path: Optional[str] = SQLField(default=None, max_length=500)
    
    status: str = SQLField(default="draft", max_length=20)
    
    created_by: Optional[str] = SQLField(default=None, max_length=100)
    created_at: datetime = SQLField(default_factory=datetime.utcnow)
    updated_at: datetime = SQLField(default_factory=datetime.utcnow)


class DistillationDatasetItem(SQLModel, table=True):
    """Item in a dataset."""
    __tablename__ = "distillation_dataset_items"
    
    id: Optional[UUID] = SQLField(default_factory=uuid4, primary_key=True)
    dataset_id: UUID = SQLField(foreign_key="distillation_datasets.id")
    banked_id: Optional[UUID] = SQLField(default=None, foreign_key="distillation_banked.id")
    structured_id: Optional[UUID] = SQLField(default=None, foreign_key="distillation_structured.id")
    
    split: str = SQLField(default="train", max_length=20)
    sequence_order: Optional[int] = None
    
    added_at: datetime = SQLField(default_factory=datetime.utcnow)


# ============================================
# Expert Review (Phase 6)
# ============================================

class DistillationReviewQueue(SQLModel, table=True):
    """Review queue for expert evaluation."""
    __tablename__ = "distillation_review_queues"
    
    id: Optional[UUID] = SQLField(default_factory=uuid4, primary_key=True)
    name: str = SQLField(max_length=255)
    description: Optional[str] = None
    
    # Filtering criteria for auto-populating
    domain_id: Optional[UUID] = SQLField(default=None, foreign_key="distillation_domains.id")
    topic_id: Optional[UUID] = SQLField(default=None, foreign_key="distillation_topics.id")
    min_quality_score: Optional[float] = None
    
    # Assignment
    assigned_experts: List[str] = SQLField(default=[], sa_column=Column(ARRAY(String)))
    
    # Status
    is_active: bool = SQLField(default=True)
    
    created_by: Optional[str] = SQLField(default=None, max_length=100)
    created_at: datetime = SQLField(default_factory=datetime.utcnow)
    updated_at: datetime = SQLField(default_factory=datetime.utcnow)


class DistillationReviewItem(SQLModel, table=True):
    """Item in a review queue."""
    __tablename__ = "distillation_review_items"
    
    id: Optional[UUID] = SQLField(default_factory=uuid4, primary_key=True)
    queue_id: UUID = SQLField(foreign_key="distillation_review_queues.id")
    banked_id: UUID = SQLField(foreign_key="distillation_banked.id")
    
    # Review status
    status: str = SQLField(default="pending", max_length=20)  # 'pending', 'in_review', 'approved', 'rejected', 'needs_revision'
    assigned_to: Optional[str] = SQLField(default=None, max_length=100)
    
    # Review outcome
    review_notes: Optional[str] = None
    review_score: Optional[float] = None
    reviewed_by: Optional[str] = SQLField(default=None, max_length=100)
    reviewed_at: Optional[datetime] = None
    
    # Priority for ordering
    priority: int = SQLField(default=0)
    
    created_at: datetime = SQLField(default_factory=datetime.utcnow)


class DistillationReviewExport(SQLModel, table=True):
    """Export/import tracking for offline review."""
    __tablename__ = "distillation_review_exports"
    
    id: Optional[UUID] = SQLField(default_factory=uuid4, primary_key=True)
    queue_id: UUID = SQLField(foreign_key="distillation_review_queues.id")
    
    # Export details
    export_format: str = SQLField(max_length=20)  # 'csv', 'json', 'xlsx'
    file_path: Optional[str] = SQLField(default=None, max_length=500)
    item_count: int = SQLField(default=0)
    
    # Import tracking
    imported_at: Optional[datetime] = None
    items_updated: Optional[int] = None
    
    exported_by: Optional[str] = SQLField(default=None, max_length=100)
    exported_at: datetime = SQLField(default_factory=datetime.utcnow)
