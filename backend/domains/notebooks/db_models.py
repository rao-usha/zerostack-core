"""Database models for notebooks."""
from sqlalchemy import Table, Column, String, Text, Integer, TIMESTAMP, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from db.models import METADATA

# Notebooks table
notebooks = Table(
    "notebooks",
    METADATA,
    Column("id", UUID, primary_key=True),
    Column("name", String(255), nullable=False),
    Column("description", Text),
    
    # Organization
    Column("folder", String(255), server_default=""),
    Column("tags", JSON, server_default="[]"),
    
    # Default data source for cells
    Column("default_connection_id", UUID, ForeignKey("data_connections.id", ondelete="SET NULL"), nullable=True),
    
    # Metadata
    Column("created_by", String(100)),
    Column("created_at", TIMESTAMP(timezone=True), server_default=func.now()),
    Column("updated_at", TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now()),
)

# Notebook cells table
notebook_cells = Table(
    "notebook_cells",
    METADATA,
    Column("id", UUID, primary_key=True),
    Column("notebook_id", UUID, ForeignKey("notebooks.id", ondelete="CASCADE"), nullable=False),
    
    # Cell content
    Column("cell_type", String(32), nullable=False),  # sql, markdown, python (future)
    Column("content", Text, nullable=False, server_default=""),
    Column("position", Integer, nullable=False),  # Order in notebook
    
    # Execution state
    Column("last_run_at", TIMESTAMP(timezone=True)),
    Column("last_run_duration_ms", Integer),
    Column("last_run_status", String(32)),  # success, error, running
    Column("last_run_error", Text),
    Column("last_run_row_count", Integer),
    
    # Results cache (stored as JSON for small results, or reference to object storage)
    Column("cached_results", JSON),  # For small results (< 1000 rows)
    Column("cached_results_uri", String(500)),  # For large results stored in S3
    
    # Cell-specific settings
    Column("connection_id", UUID, ForeignKey("data_connections.id", ondelete="SET NULL"), nullable=True),
    Column("settings", JSON, server_default="{}"),  # limit, timeout, etc.
    
    Column("created_at", TIMESTAMP(timezone=True), server_default=func.now()),
    Column("updated_at", TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now()),
)

# Saved datasets from notebook outputs
notebook_datasets = Table(
    "notebook_datasets",
    METADATA,
    Column("id", UUID, primary_key=True),
    Column("name", String(255), nullable=False),
    Column("description", Text),
    
    # Source
    Column("source_notebook_id", UUID, ForeignKey("notebooks.id", ondelete="SET NULL"), nullable=True),
    Column("source_cell_id", UUID, ForeignKey("notebook_cells.id", ondelete="SET NULL"), nullable=True),
    Column("source_query", Text),  # The SQL that generated this
    
    # Storage
    Column("storage_uri", String(500)),  # s3://bucket/datasets/...
    Column("storage_format", String(32), server_default="parquet"),  # parquet, csv, json
    
    # Stats
    Column("row_count", Integer),
    Column("column_count", Integer),
    Column("size_bytes", Integer),
    Column("columns", JSON),  # [{name, type}, ...]
    
    # Metadata
    Column("created_by", String(100)),
    Column("created_at", TIMESTAMP(timezone=True), server_default=func.now()),
    Column("updated_at", TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now()),
)
