"""Database table definitions using SQLAlchemy Core."""
from sqlalchemy import Table, Column, ForeignKey, Boolean, Integer, String, JSON, Text, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID
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


# connectors & datasets
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


datasets = Table(
    "datasets",
    METADATA,
    Column("id", UUID, primary_key=True),
    Column("org_id", UUID, ForeignKey("orgs.id"), nullable=False),
    Column("name", String(255), nullable=False),
    Column("connector_id", UUID, ForeignKey("connectors.id"), nullable=True),
    Column("resource", String(512), nullable=True),  # table/bucket/path
    Column("tags", JSON, nullable=False, server_default="[]"),
    Column("pii_flags", JSON, nullable=False, server_default="[]"),
    Column("created_at", TIMESTAMP(timezone=True), server_default=func.now()),
)


dataset_versions = Table(
    "dataset_versions",
    METADATA,
    Column("id", UUID, primary_key=True),
    Column("dataset_id", UUID, ForeignKey("datasets.id"), nullable=False),
    Column("version", String(64), nullable=False),
    Column("summary", Text),
    Column("created_at", TIMESTAMP(timezone=True), server_default=func.now()),
)


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
