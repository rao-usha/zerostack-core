"""
Settings domain for database-backed configuration management.

Provides:
- Encrypted storage for API keys and secrets
- Category-based organization (llm, compute, storage, oauth, feature)
- ConfigProvider for unified config access (DB -> .env -> defaults)
"""

from .router import router
from .config_provider import config

__all__ = ["router", "config"]
