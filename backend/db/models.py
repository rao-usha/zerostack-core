"""Database table definitions using SQLAlchemy Core."""
from sqlalchemy import Table, Column, ForeignKey, Boolean, Integer, BigInteger, String, JSON, Text, TIMESTAMP, Numeric
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.sql import func
from .meta import METADATA


# tenants/orgs
orgs = Table(
    "orgs",
    METADATA,
    Column("id", UUID, primary_key=True),
    Column("name", String(255), nullable=False, unique=True),
    Column("created_at", TIMESTAMP(timezone=True), server_default=func.now()),
)


users = Table(
    "users",
    METADATA,
    Column("id", UUID, primary_key=True),
    Column("org_id", UUID, ForeignKey("orgs.id"), nullable=False),
    Column("email", String(320), unique=True, nullable=False),
    Column("role", String(64), nullable=False, default="member"),
    Column("created_at", TIMESTAMP(timezone=True), server_default=func.now()),
)


# connectors
connectors = Table(
    "connectors",
    METADATA,
    Column("id", UUID, primary_key=True),
    Column("org_id", UUID, ForeignKey("orgs.id"), nullable=False),
    Column("type", String(64), nullable=False),  # postgres/snowflake/s3/http
    Column("name", String(255), nullable=False),
    Column("config", JSON, nullable=False, server_default="{}"),
    Column("created_at", TIMESTAMP(timezone=True), server_default=func.now()),
)


# NOTE: datasets and dataset_versions tables are defined in domains/datasets/db_models.py


# contexts & personas
contexts = Table(
    "contexts",
    METADATA,
    Column("id", UUID, primary_key=True),
    Column("org_id", UUID, ForeignKey("orgs.id"), nullable=False),
    Column("name", String(255), nullable=False),
    Column("description", Text),
    Column("metadata", JSON, nullable=False, server_default="{}"),
    Column("created_at", TIMESTAMP(timezone=True), server_default=func.now()),
)


context_versions = Table(
    "context_versions",
    METADATA,
    Column("id", UUID, primary_key=True),
    Column("context_id", UUID, ForeignKey("contexts.id"), nullable=False),
    Column("version", String(64), nullable=False),
    Column("digest", String(64), nullable=False),  # content-addressed hash
    Column("data_refs", JSON, nullable=False, server_default="[]"),  # dataset_version ids, MCP tools, personas
    Column("layers", JSON, nullable=False, server_default="[]"),  # layer definitions
    Column("diff_summary", Text),
    Column("created_at", TIMESTAMP(timezone=True), server_default=func.now()),
)

context_layers = Table(
    "context_layers",
    METADATA,
    Column("id", UUID, primary_key=True),
    Column("context_id", UUID, ForeignKey("contexts.id"), nullable=False),
    Column("kind", String(64), nullable=False),  # "select" | "transform" | "dictionary" | "persona" | "mcp" | "rule"
    Column("name", String(255), nullable=False),
    Column("spec", JSON, nullable=False, server_default="{}"),
    Column("enabled", Boolean, nullable=False, default=True),
    Column("order", Integer, nullable=False, default=0),
    Column("created_at", TIMESTAMP(timezone=True), server_default=func.now()),
)

context_dictionaries = Table(
    "context_dictionaries",
    METADATA,
    Column("id", UUID, primary_key=True),
    Column("context_id", UUID, ForeignKey("contexts.id"), nullable=False),
    Column("name", String(255), nullable=False),
    Column("entries", JSON, nullable=False, server_default="{}"),  # term -> definition mapping
    Column("created_at", TIMESTAMP(timezone=True), server_default=func.now()),
    Column("updated_at", TIMESTAMP(timezone=True), server_default=func.now()),
)

context_documents = Table(
    "context_documents",
    METADATA,
    Column("id", UUID, primary_key=True),
    Column("context_id", UUID, ForeignKey("contexts.id"), nullable=False),
    Column("name", String(255), nullable=False),
    Column("filename", String(512), nullable=False),
    Column("storage_path", String(512), nullable=False),  # path in ObjectStore
    Column("content_type", String(128), nullable=False),
    Column("file_size", Integer, nullable=False),
    Column("sha256", String(64), nullable=True),  # content hash
    Column("summary", Text),  # AI-generated summary
    Column("text_content", Text),  # extracted text content (for text files)
    Column("metadata", JSON, nullable=False, server_default="{}"),
    Column("created_at", TIMESTAMP(timezone=True), server_default=func.now()),
)


personas = Table(
    "personas",
    METADATA,
    Column("id", UUID, primary_key=True),
    Column("org_id", UUID, ForeignKey("orgs.id"), nullable=False),
    Column("name", String(255), nullable=False),
    Column("description", Text),
    Column("constraints", JSON, nullable=False, server_default="{}"),
    Column("created_at", TIMESTAMP(timezone=True), server_default=func.now()),
)


# evals
eval_scenarios = Table(
    "eval_scenarios",
    METADATA,
    Column("id", UUID, primary_key=True),
    Column("org_id", UUID, ForeignKey("orgs.id"), nullable=False),
    Column("name", String(255), nullable=False),
    Column("description", Text),
    Column("inputs", JSON, nullable=False, server_default="[]"),
    Column("expected", JSON, nullable=False, server_default="[]"),
    Column("created_at", TIMESTAMP(timezone=True), server_default=func.now()),
)


eval_runs = Table(
    "eval_runs",
    METADATA,
    Column("id", UUID, primary_key=True),
    Column("org_id", UUID, ForeignKey("orgs.id"), nullable=False),
    Column("scenario_id", UUID, ForeignKey("eval_scenarios.id"), nullable=False),
    Column("context_version_id", UUID, ForeignKey("context_versions.id"), nullable=True),
    Column("metrics", JSON, nullable=False, server_default="{}"),
    Column("status", String(32), nullable=False, default="queued"),
    Column("created_at", TIMESTAMP(timezone=True), server_default=func.now()),
)


# governance & audit
policies = Table(
    "policies",
    METADATA,
    Column("id", UUID, primary_key=True),
    Column("org_id", UUID, ForeignKey("orgs.id"), nullable=False),
    Column("name", String(255), nullable=False),
    Column("rules", JSON, nullable=False, server_default="{}"),
    Column("active", Boolean, nullable=False, default=True),
    Column("created_at", TIMESTAMP(timezone=True), server_default=func.now()),
)


audit_log = Table(
    "audit_log",
    METADATA,
    Column("id", UUID, primary_key=True),
    Column("org_id", UUID, ForeignKey("orgs.id"), nullable=False),
    Column("actor", String(255), nullable=False),
    Column("action", String(255), nullable=False),
    Column("payload", JSON, nullable=False, server_default="{}"),
    Column("created_at", TIMESTAMP(timezone=True), server_default=func.now()),
)


# jobs
jobs = Table(
    "jobs",
    METADATA,
    Column("id", UUID, primary_key=True),
    Column("org_id", UUID, ForeignKey("orgs.id"), nullable=False),
    Column("task", String(255), nullable=False),  # "eval.run", "synthetic.generate"
    Column("payload", JSON, nullable=False, server_default="{}"),
    Column("status", String(32), nullable=False, default="queued"),
    Column("created_at", TIMESTAMP(timezone=True), server_default=func.now()),
)


# ML Model Development tables
ml_recipe = Table(
    "ml_recipe",
    METADATA,
    Column("id", String(255), primary_key=True),
    Column("name", Text, nullable=False),
    Column("model_family", String(64), nullable=False),  # pricing|next_best_action|location_scoring|forecasting
    Column("level", String(32), nullable=False),  # baseline|industry|client
    Column("status", String(32), nullable=False, default="draft"),  # draft|approved|archived
    Column("parent_id", String(255), nullable=True),  # for inheritance
    Column("tags", JSON, nullable=False, server_default="[]"),
    # GPU Runner support (migration 020)
    Column("container_image", String(500), nullable=True),
    Column("container_entrypoint", ARRAY(String), nullable=True),
    Column("default_compute_target", String(50), nullable=True, server_default="local"),
    Column("gpu_required", Boolean, nullable=False, server_default="false"),
    Column("created_at", TIMESTAMP(timezone=True), server_default=func.now()),
    Column("updated_at", TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now()),
)


ml_recipe_version = Table(
    "ml_recipe_version",
    METADATA,
    Column("version_id", String(255), primary_key=True),
    Column("recipe_id", String(255), ForeignKey("ml_recipe.id"), nullable=False),
    Column("version_number", String(64), nullable=False),
    Column("manifest_json", JSON, nullable=False, server_default="{}"),
    Column("diff_from_prev", JSON, nullable=True),
    Column("created_by", Text, nullable=True),
    Column("created_at", TIMESTAMP(timezone=True), server_default=func.now()),
    Column("change_note", Text, nullable=True),
)


ml_model = Table(
    "ml_model",
    METADATA,
    Column("id", String(255), primary_key=True),
    Column("name", Text, nullable=False),
    Column("model_family", String(64), nullable=False),
    Column("recipe_id", String(255), ForeignKey("ml_recipe.id"), nullable=False),
    Column("recipe_version_id", String(255), ForeignKey("ml_recipe_version.version_id"), nullable=False),
    Column("status", String(32), nullable=False, default="draft"),  # draft|staging|production|retired
    Column("owner", Text, nullable=True),
    Column("created_at", TIMESTAMP(timezone=True), server_default=func.now()),
    Column("updated_at", TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now()),
)


ml_run = Table(
    "ml_run",
    METADATA,
    Column("id", String(255), primary_key=True),
    Column("model_id", String(255), ForeignKey("ml_model.id"), nullable=True),
    Column("recipe_id", String(255), ForeignKey("ml_recipe.id"), nullable=False),
    Column("recipe_version_id", String(255), ForeignKey("ml_recipe_version.version_id"), nullable=False),
    Column("run_type", String(32), nullable=False),  # train|eval|backtest
    Column("status", String(32), nullable=False, default="queued"),  # queued|running|succeeded|failed
    Column("started_at", TIMESTAMP(timezone=True), nullable=True),
    Column("finished_at", TIMESTAMP(timezone=True), nullable=True),
    Column("metrics_json", JSON, nullable=False, server_default="{}"),
    Column("artifacts_json", JSON, nullable=False, server_default="{}"),
    Column("logs_text", Text, nullable=True),
    # GPU Runner support (migration 020)
    Column("compute_target", String(50), nullable=True, server_default="local"),
    Column("remote_job_id", String(255), nullable=True),
    Column("input_dataset_version_id", UUID, nullable=True),
    Column("parameters", JSON, nullable=False, server_default="{}"),
    Column("logs_uri", String(500), nullable=True),
    Column("output_manifest_uri", String(500), nullable=True),
    Column("status_reason", Text, nullable=True),
    Column("created_by", String(100), nullable=True),
    Column("chat_session_id", String(100), nullable=True),
    # Phase B: Cost tracking (migration 021)
    Column("estimated_cost_usd", Numeric(10, 4), nullable=True),
    Column("actual_cost_usd", Numeric(10, 4), nullable=True),
    Column("gpu_type", String(100), nullable=True),
    Column("runtime_seconds", Integer, nullable=True),
    # Phase B: Reuse tracking (migration 021)
    Column("similarity_hash", String(64), nullable=True),
    Column("reused_from_run_id", String(255), nullable=True),
    # Phase B: Retry tracking (migration 021)
    Column("retry_count", Integer, server_default="0", nullable=False),
    Column("max_retries", Integer, server_default="2", nullable=False),
    Column("failure_reason", Text, nullable=True),
    Column("failure_type", String(50), nullable=True),  # 'infra' or 'model'
    # Phase B: Lineage (migration 021)
    Column("parent_run_id", String(255), nullable=True),
)


ml_monitor_snapshot = Table(
    "ml_monitor_snapshot",
    METADATA,
    Column("id", String(255), primary_key=True),
    Column("model_id", String(255), ForeignKey("ml_model.id"), nullable=False),
    Column("captured_at", TIMESTAMP(timezone=True), server_default=func.now()),
    Column("performance_metrics_json", JSON, nullable=False, server_default="{}"),
    Column("drift_metrics_json", JSON, nullable=False, server_default="{}"),
    Column("data_freshness_json", JSON, nullable=False, server_default="{}"),
    Column("alerts_json", JSON, nullable=False, server_default="{}"),
)


ml_synthetic_example = Table(
    "ml_synthetic_example",
    METADATA,
    Column("id", String(255), primary_key=True),
    Column("recipe_id", String(255), ForeignKey("ml_recipe.id"), nullable=False),
    Column("dataset_schema_json", JSON, nullable=False, server_default="{}"),
    Column("sample_rows_json", JSON, nullable=False, server_default="[]"),
    Column("example_run_json", JSON, nullable=False, server_default="{}"),
    Column("created_at", TIMESTAMP(timezone=True), server_default=func.now()),
)


# ML Evaluation Packs
evaluation_pack = Table(
    "evaluation_pack",
    METADATA,
    Column("id", String(255), primary_key=True),
    Column("name", Text, nullable=False),
    Column("model_family", String(64), nullable=False),  # pricing|next_best_action|location_scoring|forecasting
    Column("status", String(32), nullable=False, default="draft"),  # draft|approved|archived
    Column("tags", JSON, nullable=False, server_default="[]"),
    Column("created_at", TIMESTAMP(timezone=True), server_default=func.now()),
    Column("updated_at", TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now()),
)


evaluation_pack_version = Table(
    "evaluation_pack_version",
    METADATA,
    Column("version_id", String(255), primary_key=True),
    Column("pack_id", String(255), ForeignKey("evaluation_pack.id"), nullable=False),
    Column("version_number", String(64), nullable=False),
    Column("pack_json", JSON, nullable=False, server_default="{}"),
    Column("diff_from_prev", JSON, nullable=True),
    Column("created_by", String(255), nullable=True),
    Column("created_at", TIMESTAMP(timezone=True), server_default=func.now()),
    Column("change_note", Text, nullable=True),
)


recipe_evaluation_pack = Table(
    "recipe_evaluation_pack",
    METADATA,
    Column("recipe_id", String(255), ForeignKey("ml_recipe.id"), nullable=False),
    Column("pack_id", String(255), ForeignKey("evaluation_pack.id"), nullable=False),
    Column("created_at", TIMESTAMP(timezone=True), server_default=func.now()),
)


evaluation_result = Table(
    "evaluation_result",
    METADATA,
    Column("id", String(255), primary_key=True),
    Column("run_id", String(255), ForeignKey("ml_run.id"), nullable=False),
    Column("pack_id", String(255), ForeignKey("evaluation_pack.id"), nullable=False),
    Column("pack_version_id", String(255), ForeignKey("evaluation_pack_version.version_id"), nullable=False),
    Column("executed_at", TIMESTAMP(timezone=True), server_default=func.now()),
    Column("status", String(32), nullable=False),  # pass|warn|fail
    Column("results_json", JSON, nullable=False, server_default="{}"),
    Column("summary_text", Text, nullable=True),
)


monitor_evaluation_snapshot = Table(
    "monitor_evaluation_snapshot",
    METADATA,
    Column("id", String(255), primary_key=True),
    Column("model_id", String(255), ForeignKey("ml_model.id"), nullable=False),
    Column("captured_at", TIMESTAMP(timezone=True), server_default=func.now()),
    Column("pack_id", String(255), ForeignKey("evaluation_pack.id"), nullable=False),
    Column("pack_version_id", String(255), ForeignKey("evaluation_pack_version.version_id"), nullable=False),
    Column("status", String(32), nullable=False),  # pass|warn|fail
    Column("results_json", JSON, nullable=False, server_default="{}"),
)


# ============================================================================
# Relationship Intelligence Tables
# ============================================================================

dictionary_relationships = Table(
    "dictionary_relationships",
    METADATA,
    Column("id", String(255), primary_key=True),
    
    # Source asset
    Column("from_asset_type", String(32), nullable=False),  # table | column
    Column("from_database", String(255), nullable=False),
    Column("from_schema", String(255), nullable=False),
    Column("from_table", String(255), nullable=False),
    Column("from_column", String(255), nullable=True),
    
    # Target asset
    Column("to_asset_type", String(32), nullable=False),  # table | column
    Column("to_database", String(255), nullable=False),
    Column("to_schema", String(255), nullable=False),
    Column("to_table", String(255), nullable=False),
    Column("to_column", String(255), nullable=True),
    
    # Relationship metadata
    Column("relationship_type", String(64), nullable=False),
    Column("confidence", Integer, nullable=False),  # 0-10000 (representing 0.0000-1.0000)
    
    # Evidence and provenance
    Column("evidence", JSON, nullable=False, server_default="{}"),
    Column("explanation", Text, nullable=True),
    Column("generated_by", String(255), nullable=False, server_default="system"),
    
    # Workflow status
    Column("status", String(32), nullable=False, server_default="suggested"),
    Column("reviewed_by", String(255), nullable=True),
    Column("reviewed_at", TIMESTAMP(timezone=True), nullable=True),
    
    # Timestamps
    Column("created_at", TIMESTAMP(timezone=True), server_default=func.now()),
    Column("updated_at", TIMESTAMP(timezone=True), server_default=func.now()),
)


dictionary_relationship_discovery_jobs = Table(
    "dictionary_relationship_discovery_jobs",
    METADATA,
    Column("id", String(255), primary_key=True),
    Column("connection_id", String(255), nullable=False),
    Column("scope_database", String(255), nullable=True),
    Column("scope_schema", String(255), nullable=True),
    Column("scope_tables", JSON, nullable=True),
    
    Column("status", String(32), nullable=False, server_default="pending"),
    Column("progress", Integer, nullable=False, server_default="0"),
    
    Column("config", JSON, nullable=False, server_default="{}"),
    Column("results_summary", JSON, nullable=True),
    Column("error_message", Text, nullable=True),
    
    Column("started_by", String(255), nullable=True),
    Column("started_at", TIMESTAMP(timezone=True), nullable=True),
    Column("completed_at", TIMESTAMP(timezone=True), nullable=True),
    Column("created_at", TIMESTAMP(timezone=True), server_default=func.now()),
    Column("updated_at", TIMESTAMP(timezone=True), server_default=func.now()),
)


# ============================================================================
# GPU Runner / Highlighted Datasets Tables
# ============================================================================

highlighted_datasets = Table(
    "highlighted_datasets",
    METADATA,
    Column("id", String(100), primary_key=True),
    Column("display_name", String(255), nullable=False),
    Column("description", Text, nullable=True),
    Column("tags", JSON, nullable=False, server_default="[]"),
    Column("source_type", String(50), nullable=False),
    Column("default_location_uri", String(500), nullable=True),
    Column("availability_state", String(30), nullable=False, server_default="NOT_PRESENT"),
    Column("resolver_config", JSON, nullable=False, server_default="{}"),
    Column("license_notes", Text, nullable=True),
    Column("created_at", TIMESTAMP(timezone=True), server_default=func.now()),
    Column("updated_at", TIMESTAMP(timezone=True), server_default=func.now()),
)


highlighted_dataset_versions = Table(
    "highlighted_dataset_versions",
    METADATA,
    Column("id", UUID, primary_key=True),
    Column("highlighted_dataset_id", String(100), ForeignKey("highlighted_datasets.id", ondelete="CASCADE"), nullable=False),
    Column("version_label", String(64), nullable=False),
    Column("manifest_uri", String(500), nullable=False),
    Column("storage_uri", String(500), nullable=False),
    Column("file_count", Integer, nullable=True),
    Column("total_bytes", Integer, nullable=True),
    Column("schema_json", JSON, nullable=True),
    Column("created_at", TIMESTAMP(timezone=True), server_default=func.now()),
    Column("created_by", String(100), nullable=True),
)


ml_derived_assets = Table(
    "ml_derived_assets",
    METADATA,
    Column("id", UUID, primary_key=True),
    Column("source_run_id", String(255), ForeignKey("ml_run.id", ondelete="CASCADE"), nullable=False),
    Column("name", String(255), nullable=True),
    Column("asset_type", String(20), nullable=False, server_default="temporal"),
    Column("storage_uri", String(500), nullable=False),
    Column("manifest_uri", String(500), nullable=False),
    Column("ttl_expires_at", TIMESTAMP(timezone=True), nullable=True),
    Column("schema_json", JSON, nullable=True),
    Column("metrics_json", JSON, nullable=False, server_default="{}"),
    Column("tags", JSON, nullable=False, server_default="[]"),
    Column("approval_state", String(20), nullable=False, server_default="draft"),
    Column("notes", Text, nullable=True),
    # Phase B: Version tracking (migration 021)
    Column("confidence_score", Numeric(5, 4), nullable=True),
    Column("replaced_by_asset_id", UUID, nullable=True),
    Column("version_number", Integer, server_default="1", nullable=False),
    Column("created_at", TIMESTAMP(timezone=True), server_default=func.now()),
    Column("created_by", String(100), nullable=True),
    Column("promoted_at", TIMESTAMP(timezone=True), nullable=True),
    Column("promoted_by", String(100), nullable=True),
)


interaction_logs = Table(
    "interaction_logs",
    METADATA,
    Column("id", UUID, primary_key=True),
    Column("chat_session_id", String(100), nullable=True),
    Column("actor", String(50), nullable=False),
    Column("event_type", String(50), nullable=False),
    Column("message", Text, nullable=True),
    Column("refs", JSON, nullable=False, server_default="{}"),
    Column("metadata", JSON, nullable=False, server_default="{}"),
    Column("created_at", TIMESTAMP(timezone=True), server_default=func.now()),
)


# ============================================================================
# GPU Pricing & Scheduling Tables (Phase B - migration 021)
# ============================================================================

gpu_pricing = Table(
    "gpu_pricing",
    METADATA,
    Column("id", String(100), primary_key=True),
    Column("provider", String(50), nullable=False),  # 'modal', 'runpod', 'aws', etc.
    Column("gpu_type", String(100), nullable=False),
    Column("price_per_hour_usd", Numeric(10, 4), nullable=False),
    Column("memory_gb", Integer, nullable=True),
    Column("spot_available", Boolean, server_default="false", nullable=False),
    Column("spot_price_per_hour_usd", Numeric(10, 4), nullable=True),
    Column("created_at", TIMESTAMP(timezone=True), server_default=func.now()),
    Column("updated_at", TIMESTAMP(timezone=True), server_default=func.now()),
)


run_schedules = Table(
    "run_schedules",
    METADATA,
    Column("id", UUID, primary_key=True, server_default=func.gen_random_uuid()),
    Column("name", String(255), nullable=False),
    Column("recipe_id", String(255), ForeignKey("ml_recipe.id", ondelete="CASCADE"), nullable=False),
    Column("cron_expression", String(100), nullable=False),
    Column("input_dataset_id", String(100), ForeignKey("highlighted_datasets.id"), nullable=True),
    Column("compute_target", String(50), server_default="local", nullable=False),
    Column("parameters", JSON, nullable=False, server_default="{}"),
    Column("enabled", Boolean, server_default="true", nullable=False),
    Column("last_run_at", TIMESTAMP(timezone=True), nullable=True),
    Column("next_run_at", TIMESTAMP(timezone=True), nullable=True),
    Column("created_by", String(100), nullable=True),
    Column("created_at", TIMESTAMP(timezone=True), server_default=func.now()),
    Column("updated_at", TIMESTAMP(timezone=True), server_default=func.now()),
)