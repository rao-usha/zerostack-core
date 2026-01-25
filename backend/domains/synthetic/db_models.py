"""Database models for synthetic data generation."""
from sqlalchemy import Table, Column, String, Text, Integer, TIMESTAMP, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.sql import func

from db.models import METADATA

# Synthetic generation jobs
synthetic_jobs = Table(
    "synthetic_jobs",
    METADATA,
    Column("id", UUID, primary_key=True),
    
    # Source - either a dataset ID or a table reference
    Column("source_dataset_id", UUID, nullable=True),  # For uploaded datasets
    Column("source_table_ref", String(255), nullable=True),  # For DB tables (schema.table)
    Column("source_connection_id", UUID, ForeignKey("data_connections.id", ondelete="SET NULL"), nullable=True),
    
    # Synthesizer configuration
    Column("synthesizer_type", String(50), nullable=False),  # gaussian_copula, ctgan, tvae
    Column("config", JSON, server_default="{}"),  # Synthesizer-specific config
    Column("privacy_config", JSON, server_default="{}"),  # Privacy settings
    Column("column_configs", JSON, server_default="{}"),  # Per-column settings
    
    # Request parameters
    Column("num_rows_requested", Integer, nullable=False),
    Column("random_seed", Integer, nullable=True),
    
    # Job status
    Column("status", String(32), nullable=False, server_default="pending"),  # pending, running, completed, failed
    Column("progress", Integer, server_default="0"),  # 0-100
    Column("status_message", Text, nullable=True),
    
    # Results
    Column("num_rows_generated", Integer, nullable=True),
    Column("synthetic_dataset_id", UUID, nullable=True),  # Reference to generated dataset
    Column("quality_report_id", UUID, nullable=True),
    
    # Timing
    Column("started_at", TIMESTAMP(timezone=True), nullable=True),
    Column("completed_at", TIMESTAMP(timezone=True), nullable=True),
    Column("duration_seconds", Numeric(10, 2), nullable=True),
    
    # Error handling
    Column("error_message", Text, nullable=True),
    Column("error_details", JSON, nullable=True),
    
    # Metadata
    Column("created_by", String(100)),
    Column("created_at", TIMESTAMP(timezone=True), server_default=func.now()),
    Column("updated_at", TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now()),
)

# Synthetic datasets (output)
synthetic_datasets = Table(
    "synthetic_datasets",
    METADATA,
    Column("id", UUID, primary_key=True),
    Column("job_id", UUID, ForeignKey("synthetic_jobs.id", ondelete="CASCADE"), nullable=False),
    
    # Dataset info
    Column("name", String(255), nullable=False),
    Column("description", Text, nullable=True),
    
    # Storage
    Column("storage_uri", String(500), nullable=True),  # s3://bucket/synthetic/...
    Column("storage_format", String(32), server_default="parquet"),
    
    # Stats
    Column("num_rows", Integer, nullable=False),
    Column("num_columns", Integer, nullable=False),
    Column("file_size_bytes", Integer, nullable=True),
    Column("columns", JSON, nullable=True),  # Column metadata [{name, dtype}, ...]
    
    # Metadata
    Column("created_at", TIMESTAMP(timezone=True), server_default=func.now()),
    Column("updated_at", TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now()),
)

# Quality evaluation reports
synthetic_quality_reports = Table(
    "synthetic_quality_reports",
    METADATA,
    Column("id", UUID, primary_key=True),
    Column("synthetic_dataset_id", UUID, ForeignKey("synthetic_datasets.id", ondelete="CASCADE"), nullable=False),
    Column("job_id", UUID, ForeignKey("synthetic_jobs.id", ondelete="CASCADE"), nullable=False),
    
    # Overall scores
    Column("overall_score", Numeric(4, 3), nullable=True),  # 0.000 - 1.000
    Column("statistical_fidelity_score", Numeric(4, 3), nullable=True),
    Column("correlation_score", Numeric(4, 3), nullable=True),
    Column("privacy_score", Numeric(4, 3), nullable=True),
    
    # Detailed metrics
    Column("column_scores", JSON, nullable=True),  # Per-column quality metrics
    Column("statistical_metrics", JSON, nullable=True),  # KS stats, distributions
    Column("correlation_metrics", JSON, nullable=True),  # Correlation preservation
    Column("privacy_metrics", JSON, nullable=True),  # Privacy risk metrics
    
    # Recommendations
    Column("recommendations", JSON, nullable=True),  # List of improvement suggestions
    Column("warnings", JSON, nullable=True),  # Any warnings about the data
    
    # Metadata
    Column("created_at", TIMESTAMP(timezone=True), server_default=func.now()),
)

# Column-level configuration for synthesis
synthetic_column_configs = Table(
    "synthetic_column_configs",
    METADATA,
    Column("id", UUID, primary_key=True),
    Column("job_id", UUID, ForeignKey("synthetic_jobs.id", ondelete="CASCADE"), nullable=False),

    # Column identification
    Column("column_name", String(255), nullable=False),
    Column("column_dtype", String(50), nullable=True),

    # PII settings
    Column("is_pii", Integer, server_default="0"),  # Boolean as int
    Column("pii_type", String(50), nullable=True),  # email, name, ssn, phone, address, etc.
    Column("faker_provider", String(100), nullable=True),  # Faker method to use

    # Constraints
    Column("constraints", JSON, server_default="{}"),  # min, max, regex, etc.

    # SDV metadata override
    Column("sdtype", String(50), nullable=True),  # SDV semantic data type

    Column("created_at", TIMESTAMP(timezone=True), server_default=func.now()),
)


# TabDiT models for diffusion-based synthetic data generation
tabdit_models = Table(
    "tabdit_models",
    METADATA,
    Column("id", UUID, primary_key=True),
    Column("name", String(255), nullable=False),
    Column("description", Text, nullable=True),

    # Source data
    Column("source_dataset_id", UUID, nullable=True),
    Column("source_table_ref", String(255), nullable=True),

    # Configuration (JSON)
    Column("vae_config", JSON, nullable=False, server_default="{}"),
    Column("diffusion_config", JSON, nullable=False, server_default="{}"),
    Column("tokenizer_config", JSON, server_default="{}"),

    # Status
    Column("status", String(32), server_default="pending"),  # pending/training_vae/training_diffusion/completed/failed
    Column("current_phase", String(32), nullable=True),

    # VAE training
    Column("vae_run_id", String(64), nullable=True),
    Column("vae_checkpoint_uri", String(500), nullable=True),
    Column("vae_metrics", JSON, nullable=True),
    Column("vae_epochs_completed", Integer, server_default="0"),

    # Diffusion training
    Column("diffusion_run_id", String(64), nullable=True),
    Column("diffusion_checkpoint_uri", String(500), nullable=True),
    Column("diffusion_metrics", JSON, nullable=True),
    Column("diffusion_epochs_completed", Integer, server_default="0"),

    # Quality
    Column("overall_quality_score", Numeric(4, 3), nullable=True),

    # Timing
    Column("started_at", TIMESTAMP(timezone=True), nullable=True),
    Column("completed_at", TIMESTAMP(timezone=True), nullable=True),

    # Metadata
    Column("created_by", String(100), nullable=True),
    Column("created_at", TIMESTAMP(timezone=True), server_default=func.now()),
    Column("updated_at", TIMESTAMP(timezone=True), server_default=func.now()),
)
