"""Database models for feature store."""
from sqlalchemy import Table, Column, String, Text, Integer, TIMESTAMP, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func

from db.models import METADATA


# Feature entities - business objects that features are computed for
feature_entities = Table(
    "feature_entities",
    METADATA,
    Column("id", UUID, primary_key=True, server_default=func.gen_random_uuid()),
    Column("name", String(100), unique=True, nullable=False),
    Column("description", Text),
    Column("join_keys", JSONB, nullable=False),  # ["user_id"] or ["user_id", "product_id"]
    Column("created_at", TIMESTAMP(timezone=True), server_default=func.now()),
    Column("updated_at", TIMESTAMP(timezone=True), server_default=func.now()),
    Column("created_by", String(100)),
)


# Feature definitions - individual feature specifications with versioning
feature_definitions = Table(
    "feature_definitions",
    METADATA,
    Column("id", UUID, primary_key=True, server_default=func.gen_random_uuid()),
    Column("name", String(255), nullable=False),
    Column("entity_id", UUID, ForeignKey("feature_entities.id", ondelete="CASCADE")),
    Column("version", Integer, nullable=False, server_default="1"),

    # Data type
    Column("dtype", String(50), nullable=False),  # int64, float64, string, bool, datetime

    # Transformation
    Column("transformation_type", String(20), nullable=False),  # sql, python
    Column("transformation_code", Text, nullable=False),

    # Source (optional)
    Column("source_table", String(255)),

    # Metadata
    Column("description", Text),
    Column("owner", String(100)),
    Column("tags", JSONB, server_default="[]"),

    # Computation settings
    Column("computation_mode", String(20), server_default="on_demand"),
    Column("refresh_schedule", String(100)),
    Column("ttl_seconds", Integer),

    # Status
    Column("status", String(20), server_default="draft"),

    Column("created_at", TIMESTAMP(timezone=True), server_default=func.now()),
    Column("updated_at", TIMESTAMP(timezone=True), server_default=func.now()),
)


# Feature sets - groups of related features
feature_sets = Table(
    "feature_sets",
    METADATA,
    Column("id", UUID, primary_key=True, server_default=func.gen_random_uuid()),
    Column("name", String(255), unique=True, nullable=False),
    Column("entity_id", UUID, ForeignKey("feature_entities.id", ondelete="SET NULL")),
    Column("description", Text),
    Column("owner", String(100)),
    Column("tags", JSONB, server_default="[]"),
    Column("created_at", TIMESTAMP(timezone=True), server_default=func.now()),
    Column("updated_at", TIMESTAMP(timezone=True), server_default=func.now()),
)


# Feature set membership - join table
feature_set_features = Table(
    "feature_set_features",
    METADATA,
    Column("id", UUID, primary_key=True, server_default=func.gen_random_uuid()),
    Column("feature_set_id", UUID, ForeignKey("feature_sets.id", ondelete="CASCADE"), nullable=False),
    Column("feature_definition_id", UUID, ForeignKey("feature_definitions.id", ondelete="CASCADE"), nullable=False),
    Column("added_at", TIMESTAMP(timezone=True), server_default=func.now()),
)
