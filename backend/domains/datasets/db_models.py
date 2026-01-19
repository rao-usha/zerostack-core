"""Database models for datasets."""
from sqlalchemy import Table, Column, String, Text, Integer, BigInteger, TIMESTAMP, ForeignKey, JSON, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from db.models import METADATA


# Main datasets table
datasets = Table(
    "datasets",
    METADATA,
    Column("id", UUID, primary_key=True),
    Column("name", String(255), nullable=False),
    Column("description", Text),

    # Organization
    Column("org_id", String(100), server_default="default"),
    Column("tags", JSON, server_default="[]"),

    # Source info
    Column("source_type", String(32), nullable=False),  # upload, notebook, connection, synthetic
    Column("source_id", UUID, nullable=True),  # ID of source notebook/connection/synthetic job

    # Current version info (denormalized for quick access)
    Column("current_version_id", UUID, nullable=True),
    Column("current_version_number", Integer, server_default="0"),

    # Storage location
    Column("storage_uri", String(500)),  # s3://bucket/datasets/{id}/...
    Column("storage_format", String(32), server_default="parquet"),  # parquet, csv, json

    # Schema and stats (from current version)
    Column("schema", JSON, server_default="{}"),  # {columns: [{name, type, nullable}, ...]}
    Column("row_count", BigInteger),
    Column("column_count", Integer),
    Column("size_bytes", BigInteger),

    # Status
    Column("status", String(32), server_default="active"),  # active, processing, error, archived
    Column("error_message", Text),

    # Metadata
    Column("created_by", String(100)),
    Column("created_at", TIMESTAMP(timezone=True), server_default=func.now()),
    Column("updated_at", TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now()),
)


# Dataset versions table
dataset_versions = Table(
    "dataset_versions",
    METADATA,
    Column("id", UUID, primary_key=True),
    Column("dataset_id", UUID, ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False),

    # Version info
    Column("version_number", Integer, nullable=False),
    Column("sha256", String(64), nullable=False),  # Content hash for deduplication

    # Storage
    Column("storage_uri", String(500), nullable=False),  # s3://bucket/datasets/{dataset_id}/v{n}/data.parquet
    Column("storage_format", String(32), nullable=False),  # parquet, csv, json
    Column("original_filename", String(255)),  # Original uploaded filename

    # Stats
    Column("row_count", BigInteger),
    Column("column_count", Integer),
    Column("size_bytes", BigInteger),

    # Schema for this version
    Column("schema", JSON, server_default="{}"),

    # Quality profile
    Column("quality_profile", JSON, server_default="{}"),  # completeness, uniqueness, etc.

    # Metadata
    Column("created_by", String(100)),
    Column("created_at", TIMESTAMP(timezone=True), server_default=func.now()),
    Column("notes", Text),  # Version notes/changelog
)


# Index for fast version lookup by hash
# This allows detecting duplicate uploads
# CREATE INDEX idx_dataset_versions_sha256 ON dataset_versions(sha256);
