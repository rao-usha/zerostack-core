"""Database models for personas - additional tables for versioning and assignments.

Note: The main 'personas' table is defined in db/models.py.
This file adds supplementary tables for version history and user assignments.
"""
from sqlalchemy import Table, Column, ForeignKey, Index, String, JSON, Text, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from db.meta import METADATA

# Import the main personas table from central models
from db.models import personas


# Persona versions for history tracking
persona_versions = Table(
    "persona_versions",
    METADATA,
    Column("id", UUID, primary_key=True),
    Column("persona_id", UUID, ForeignKey("personas.id", ondelete="CASCADE"), nullable=False),
    Column("version", String(32), nullable=False),

    # Snapshot of persona state at this version
    Column("snapshot", JSON, nullable=False),  # Full persona data at this version

    # Change tracking
    Column("changes", JSON, server_default="{}"),  # What changed from previous version
    Column("change_reason", Text),  # Why this change was made

    # Metadata
    Column("created_by", UUID),
    Column("created_at", TIMESTAMP(timezone=True), server_default=func.now()),

    Index("ix_persona_versions_persona_id", "persona_id"),
    Index("ix_persona_versions_version", "persona_id", "version"),
)


# Persona assignments - link personas to users
persona_assignments = Table(
    "persona_assignments",
    METADATA,
    Column("id", UUID, primary_key=True),
    Column("persona_id", UUID, ForeignKey("personas.id", ondelete="CASCADE"), nullable=False),
    Column("user_id", UUID, nullable=False),  # Will link to users table when auth is implemented

    # Assignment details
    Column("is_primary", String(1), server_default="N"),  # Y/N - is this the user's primary persona
    Column("assigned_by", UUID),
    Column("assigned_at", TIMESTAMP(timezone=True), server_default=func.now()),
    Column("expires_at", TIMESTAMP(timezone=True)),  # Optional expiration

    # Metadata
    Column("notes", Text),

    Index("ix_persona_assignments_persona_id", "persona_id"),
    Index("ix_persona_assignments_user_id", "user_id"),
)
