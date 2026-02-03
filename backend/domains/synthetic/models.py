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
    TABDIT = "tabdit"


class ConditionOperator(str, Enum):
    """Operators for conditional generation."""
    EQ = "eq"           # Equal to value
    NE = "ne"           # Not equal to value
    GT = "gt"           # Greater than
    GTE = "gte"         # Greater than or equal
    LT = "lt"           # Less than
    LTE = "lte"         # Less than or equal
    IN = "in"           # Value in list
    NOT_IN = "not_in"   # Value not in list
    BETWEEN = "between" # Between min and max (value should be [min, max])


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

class GenerationCondition(BaseModel):
    """A condition for conditional synthetic data generation."""
    column: str = Field(..., description="Column name to apply condition to")
    operator: ConditionOperator = Field(..., description="Comparison operator")
    value: Any = Field(
        ...,
        description="Value for comparison. Single value for eq/ne/gt/gte/lt/lte, "
                    "list for in/not_in, [min, max] for between"
    )


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


class TabDiTVAEConfig(BaseModel):
    """Configuration for TabDiT VAE phase."""
    latent_dim: int = Field(default=128, ge=32, le=512)
    encoder_layers: List[int] = Field(default=[512, 256, 128])
    decoder_layers: List[int] = Field(default=[128, 256, 512])
    epochs: int = Field(default=100, ge=10, le=500)
    batch_size: int = Field(default=512, ge=32, le=4096)
    learning_rate: float = Field(default=1e-3, ge=1e-6, le=1e-1)
    kl_weight: float = Field(default=0.1, ge=0.0, le=1.0)


class TabDiTDiffusionConfig(BaseModel):
    """Configuration for TabDiT diffusion phase."""
    num_layers: int = Field(default=6, ge=2, le=12)
    hidden_dim: int = Field(default=256, ge=64, le=1024)
    num_heads: int = Field(default=8, ge=2, le=16)
    epochs: int = Field(default=200, ge=50, le=1000)
    batch_size: int = Field(default=256, ge=32, le=2048)
    learning_rate: float = Field(default=1e-4, ge=1e-6, le=1e-2)
    num_inference_steps: int = Field(default=50, ge=10, le=200)
    beta_schedule: str = Field(default="cosine", pattern="^(linear|cosine)$")


class TabDiTConfig(BaseModel):
    """Configuration for TabDiT synthesizer."""
    vae: Optional[TabDiTVAEConfig] = None
    diffusion: Optional[TabDiTDiffusionConfig] = None
    random_seed: Optional[int] = None
    device: str = Field(default="auto", pattern="^(auto|cuda|cpu)$")


class TabDiTModelStatus(str, Enum):
    """Status values for TabDiT models."""
    PENDING = "pending"
    TRAINING_VAE = "training_vae"
    TRAINING_DIFFUSION = "training_diffusion"
    COMPLETED = "completed"
    FAILED = "failed"


class TabDiTModelCreateRequest(BaseModel):
    """Request to create a new TabDiT model."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    source_table_ref: Optional[str] = None  # "schema.table" for DB tables
    source_dataset_id: Optional[UUID] = None  # For uploaded datasets
    config: Optional[TabDiTConfig] = None


class TabDiTModelResponse(BaseModel):
    """Response with TabDiT model details."""
    id: UUID
    name: str
    description: Optional[str] = None
    status: TabDiTModelStatus
    current_phase: Optional[str] = None

    # VAE training info
    vae_epochs_completed: int = 0
    vae_metrics: Optional[Dict[str, Any]] = None

    # Diffusion training info
    diffusion_epochs_completed: int = 0
    diffusion_metrics: Optional[Dict[str, Any]] = None

    # Quality
    overall_quality_score: Optional[float] = None

    # Timing
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime

    # Config
    vae_config: Optional[Dict[str, Any]] = None
    diffusion_config: Optional[Dict[str, Any]] = None


class TabDiTModelListResponse(BaseModel):
    """List of TabDiT models."""
    models: List[TabDiTModelResponse]
    total: int


class TabDiTGenerateRequest(BaseModel):
    """Request to generate synthetic data from a TabDiT model."""
    num_rows: int = Field(default=1000, ge=10, le=1000000)
    output_name: Optional[str] = None
    output_format: str = Field(default="parquet", pattern="^(parquet|csv)$")


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


class ConditionalGenerateRequest(BaseModel):
    """Request to generate synthetic data with conditions.

    Allows specifying conditions like:
    - Generate customers where region='US' and age > 25
    - Generate transactions where amount between 100 and 1000
    """
    source: SourceConfig

    # Generation settings
    num_rows: int = Field(default=1000, ge=10, le=1000000)
    random_seed: Optional[int] = None

    # Synthesizer selection (GaussianCopula recommended for conditional sampling)
    synthesizer: SynthesizerType = SynthesizerType.GAUSSIAN_COPULA

    # Conditions for generation
    conditions: List[GenerationCondition] = Field(
        default_factory=list,
        description="Conditions that generated data must satisfy"
    )

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

    # Conditional generation settings
    max_tries_per_batch: int = Field(
        default=100,
        ge=10,
        le=1000,
        description="Max sampling attempts per batch for reject sampling"
    )
    oversample_factor: float = Field(
        default=2.0,
        ge=1.1,
        le=10.0,
        description="Oversample factor for range conditions (generate more, then filter)"
    )


class JobResponse(BaseModel):
    """Response when job is created."""
    job_id: UUID
    status: JobStatus
    message: str
    estimated_seconds: Optional[int] = None


class ColumnInfo(BaseModel):
    """Column information."""
    name: str
    dtype: str


class GenerationResultResponse(BaseModel):
    """Enhanced response for completed generation with preview and quality info."""
    job_id: UUID
    status: JobStatus
    message: str

    # Dataset info
    synthetic_dataset_id: Optional[UUID] = None
    num_rows: int = 0
    columns: List[ColumnInfo] = Field(default_factory=list)

    # Preview data
    preview: List[Dict[str, Any]] = Field(default_factory=list)

    # Quality info (basic, call quality endpoints for full report)
    quality_score: Optional[float] = None

    # Warnings from condition validation
    warnings: List[str] = Field(default_factory=list)


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
