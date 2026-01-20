"""
Settings SQLModel database models.

Maps to the app_settings table created in migration 029.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4
from sqlmodel import SQLModel, Field as SQLField


class AppSetting(SQLModel, table=True):
    """Application setting stored in database with encryption support."""
    __tablename__ = "app_settings"

    id: Optional[UUID] = SQLField(default_factory=uuid4, primary_key=True)

    # Organization (NULL = global setting)
    org_id: Optional[str] = SQLField(default=None, max_length=100)

    # Categorization
    category: str = SQLField(max_length=64)  # 'llm', 'compute', 'storage', 'oauth', 'feature'
    key: str = SQLField(max_length=255)

    # Value (encrypted for secrets)
    value_encrypted: Optional[str] = None
    is_secret: bool = SQLField(default=True)

    # Metadata
    description: Optional[str] = None
    display_name: Optional[str] = SQLField(default=None, max_length=255)
    validation_pattern: Optional[str] = SQLField(default=None, max_length=255)

    # Audit
    created_at: datetime = SQLField(default_factory=datetime.utcnow)
    updated_at: datetime = SQLField(default_factory=datetime.utcnow)
    updated_by: Optional[str] = SQLField(default=None, max_length=100)
