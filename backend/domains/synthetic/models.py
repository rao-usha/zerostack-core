"""Pydantic models for synthetic data API."""
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from enum import Enum

from pydantic import BaseModel, Field


class SynthesizerType(str, Enum):
    """Available synthesizer types."""
    GAUSSIAN_COPULA = "gaussian_copula"
    CTGAN = "ctgan"
    TVAE = "tvae"


class JobStatus(str, Enum):
    """Job status values."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class PrivacyLevel(str, Enum):
    """Privacy protection levels."""
    STANDARD = "standard"  # Basic synthesis
    ENHANCED = "enhanced"  # PII detection + replacement
    STRICT = "strict"  # DP + full PII handling


class PIIType(str, Enum):
    """Types of PII that can be detected/generated."""
    EMAIL = "email"
    NAME = "name"
    FIRST_NAME = "first_name"
    LAST_NAME = "last_name"
    PHONE = "phone"
    SSN = "ssn"
    ADDRESS = "address"
    CITY = "city"
    STATE = "state"
    ZIP_CODE = "zip_code"
    CREDIT_CARD = "credit_card"
    DATE_OF_BIRTH = "date_of_birth"
    IP_ADDRESS = "ip_address"


# ============================================================================
# COLUMN CONFIGURATION
# ============================================================================

class ColumnConstraints(BaseModel):
    """Constraints for a column."""
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    regex: Optional[str] = None
    allowed_values: Optional[List[Any]] = None


class ColumnConfig(BaseModel):
    """Configuration for a single column."""
    is_pii: bool = False
    pii_type: Optional[PIIType] = None
    faker_provider: Optional[str] = None  # e.g., "faker.email", "faker.name"
    sdtype: Optional[str] = None  # SDV semantic type override
    constraints: Optional[ColumnConstraints] = None


# ============================================================================
# PRIVACY CONFIGURATION
# ============================================================================

class PrivacyConfig(BaseModel):
    """Privacy settings for synthesis."""
    level: PrivacyLevel = PrivacyLevel.STANDARD
    auto_detect_pii: bool = True
    anonymize_pii: bool = True
    differential_privacy: bool = False
    epsilon: float = Field(default=1.0, ge=0.1, le=100.0, description="DP epsilon (lower = more private)")


# ============================================================================
# SYNTHESIZER CONFIGURATION
# ============================================================================

class CopulaConfig(BaseModel):
    """Configuration for Gaussian Copula synthesizer."""
    enforce_min_max: bool = True
    enforce_rounding: bool = True
    numerical_distributions: Optional[Dict[str, str]] = None  # Column -> distribution type


class CTGANConfig(BaseModel):
    """Configuration for CTGAN synthesizer."""
    epochs: int = Field(default=300, ge=1, le=1000)
    batch_size: int = Field(default=500, ge=10, le=10000)
    generator_dim: List[int] = Field(default=[256, 256])
    discriminator_dim: List[int] = Field(default=[256, 256])
    generator_lr: float = Field(default=2e-4, ge=1e-6, le=1e-2)
    discriminator_lr: float = Field(default=2e-4, ge=1e-6, le=1e-2)
    discriminator_steps: int = Field(default=1, ge=1, le=10)
    verbose: bool = False


class TVAEConfig(BaseModel):
    """Configuration for TVAE synthesizer."""
    epochs: int = Field(default=300, ge=1, le=1000)
    batch_size: int = Field(default=500, ge=10, le=10000)
    encoder_dim: List[int] = Field(default=[128, 128])
    decoder_dim: List[int] = Field(default=[128, 128])
    l2_scale: float = Field(default=1e-5, ge=0, le=1)
    loss_factor: float = Field(default=2, ge=0.1, le=10)


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class SourceConfig(BaseModel):
    """Source data configuration."""
    type: str = Field(..., pattern="^(dataset|table)$")  # "dataset" or "table"
    dataset_id: Optional[UUID] = None  # For uploaded datasets
    connection_id: Optional[UUID] = None  # For DB tables
    table_ref: Optional[str] = None  # "schema.table" for DB tables


class SyntheticGenerateRequest(BaseModel):
    """Request to generate synthetic data."""
    source: SourceConfig
    
    # Generation settings
    num_rows: int = Field(default=1000, ge=10, le=1000000)
    random_seed: Optional[int] = None
    
    # Synthesizer selection
    synthesizer: SynthesizerType = SynthesizerType.GAUSSIAN_COPULA
    
    # Synthesizer-specific config (optional)
    copula_config: Optional[CopulaConfig] = None
    ctgan_config: Optional[CTGANConfig] = None
    tvae_config: Optional[TVAEConfig] = None
    
    # Privacy settings
    privacy: Optional[PrivacyConfig] = None
    
    # Column-specific settings
    columns: Optional[Dict[str, ColumnConfig]] = None
    
    # Output settings
    output_name: Optional[str] = None
    output_format: str = Field(default="parquet", pattern="^(parquet|csv)$")


class JobResponse(BaseModel):
    """Response when job is created."""
    job_id: UUID
    status: JobStatus
    message: str
    estimated_seconds: Optional[int] = None


class JobStatusResponse(BaseModel):
    """Detailed job status."""
    job_id: UUID
    status: JobStatus
    progress: int = 0
    status_message: Optional[str] = None
    
    # Source info
    source_type: Optional[str] = None
    synthesizer_type: Optional[str] = None
    num_rows_requested: int
    
    # Results (if completed)
    synthetic_dataset_id: Optional[UUID] = None
    num_rows_generated: Optional[int] = None
    quality_score: Optional[float] = None
    
    # Timing
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    
    # Error (if failed)
    error_message: Optional[str] = None
    
    created_at: datetime


class QualityColumnScore(BaseModel):
    """Quality score for a single column."""
    column_name: str
    dtype: str
    ks_statistic: Optional[float] = None  # Kolmogorov-Smirnov stat
    p_value: Optional[float] = None
    score: float
    rating: str  # excellent, good, fair, poor


class QualityReportResponse(BaseModel):
    """Quality evaluation report."""
    report_id: UUID
    synthetic_dataset_id: UUID
    job_id: UUID
    
    # Overall scores
    overall_score: float
    statistical_fidelity_score: float
    correlation_score: float
    
    # Column-level details
    column_scores: List[QualityColumnScore]
    
    # Privacy metrics (if computed)
    privacy_score: Optional[float] = None
    privacy_metrics: Optional[Dict[str, Any]] = None
    
    # Recommendations
    recommendations: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    
    created_at: datetime


class SyntheticDatasetResponse(BaseModel):
    """Synthetic dataset info."""
    id: UUID
    job_id: UUID
    name: str
    description: Optional[str] = None
    
    # Storage
    storage_uri: Optional[str] = None
    storage_format: str = "parquet"
    
    # Stats
    num_rows: int
    num_columns: int
    file_size_bytes: Optional[int] = None
    columns: Optional[List[Dict[str, Any]]] = None
    
    # Quality
    quality_score: Optional[float] = None
    
    created_at: datetime


class SyntheticDatasetListResponse(BaseModel):
    """List of synthetic datasets."""
    datasets: List[SyntheticDatasetResponse]
    total: int


class SynthesizerInfo(BaseModel):
    """Information about a synthesizer."""
    id: str
    name: str
    description: str
    speed: str  # fast, medium, slow
    quality: str  # good, very_good, excellent
    gpu_required: bool
    best_for: List[str]
    config_schema: Optional[Dict[str, Any]] = None


class SynthesizersListResponse(BaseModel):
    """List of available synthesizers."""
    synthesizers: List[SynthesizerInfo]


# ============================================================================
# PREVIEW MODELS
# ============================================================================

class PreviewRequest(BaseModel):
    """Request to preview source data before synthesis."""
    source: SourceConfig
    limit: int = Field(default=100, le=1000)


class PreviewResponse(BaseModel):
    """Preview of source data with metadata."""
    columns: List[Dict[str, Any]]  # [{name, dtype, nullable, sample_values}, ...]
    row_count: int
    preview_rows: List[Dict[str, Any]]
    detected_pii: Dict[str, str] = Field(default_factory=dict)  # column -> pii_type
    recommendations: List[str] = Field(default_factory=list)
