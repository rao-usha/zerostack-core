"""
ConfigProvider - Unified configuration access.

Provides a single interface for accessing configuration values with fallback:
1. Database (encrypted settings)
2. Environment variables (.env)
3. Pydantic settings defaults

Usage:
    from domains.settings.config_provider import config

    # Get a value (DB -> env -> default)
    api_key = config.get("OPENAI_API_KEY", category="llm")

    # Get with explicit default
    api_key = config.get("OPENAI_API_KEY", category="llm", default="")

    # Set a value (stores in DB)
    config.set("OPENAI_API_KEY", "sk-...", category="llm")
"""

import os
import logging
from typing import Optional, Any
from functools import lru_cache

logger = logging.getLogger(__name__)


class ConfigProvider:
    """
    Unified configuration provider with fallback chain:
    1. Database (encrypted)
    2. Environment variable
    3. Pydantic settings
    4. Default value
    """

    # Mapping of setting keys to environment variable names
    # Most are 1:1 but this allows for flexibility
    KEY_ENV_MAP = {
        "OPENAI_API_KEY": "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY": "ANTHROPIC_API_KEY",
        "GOOGLE_API_KEY": "GOOGLE_API_KEY",
        "XAI_API_KEY": "XAI_API_KEY",
        "RUNPOD_API_KEY": "RUNPOD_API_KEY",
        "RUNPOD_DEFAULT_GPU": "RUNPOD_DEFAULT_GPU",
        "RUNPOD_ENDPOINT_ID": "RUNPOD_ENDPOINT_ID",
        "S3_ENDPOINT": "S3_ENDPOINT",
        "S3_ACCESS_KEY": "S3_ACCESS_KEY",
        "S3_SECRET_KEY": "S3_SECRET_KEY",
        "S3_BUCKET": "S3_BUCKET",
        "GOOGLE_OAUTH_CLIENT_ID": "GOOGLE_OAUTH_CLIENT_ID",
        "GOOGLE_OAUTH_CLIENT_SECRET": "GOOGLE_OAUTH_CLIENT_SECRET",
    }

    # Mapping of setting keys to Pydantic settings attributes
    KEY_SETTINGS_MAP = {
        "OPENAI_API_KEY": "openai_api_key",
        "RUNPOD_API_KEY": "runpod_api_key",
        "RUNPOD_DEFAULT_GPU": "runpod_default_gpu",
        "RUNPOD_ENDPOINT_ID": "runpod_endpoint_id",
        "S3_ENDPOINT": "s3_endpoint",
        "S3_ACCESS_KEY": "s3_access_key",
        "S3_SECRET_KEY": "s3_secret_key",
        "S3_BUCKET": "s3_bucket",
    }

    def __init__(self):
        self._cache = {}
        self._cache_enabled = True

    def get(
        self,
        key: str,
        category: Optional[str] = None,
        default: Optional[str] = None,
        org_id: Optional[str] = None
    ) -> Optional[str]:
        """
        Get a configuration value with fallback chain.

        Args:
            key: The setting key (e.g., "OPENAI_API_KEY")
            category: Optional category hint (e.g., "llm")
            default: Default value if not found anywhere
            org_id: Organization ID for multi-tenant settings

        Returns:
            The configuration value or default
        """
        cache_key = f"{org_id or 'global'}:{category or 'any'}:{key}"

        # Check cache first
        if self._cache_enabled and cache_key in self._cache:
            return self._cache[cache_key]

        value = None

        # 1. Try database
        value = self._get_from_db(key, category, org_id)

        # 2. Fall back to environment variable
        if value is None:
            value = self._get_from_env(key)

        # 3. Fall back to Pydantic settings
        if value is None:
            value = self._get_from_settings(key)

        # 4. Use default
        if value is None:
            value = default

        # Cache the result
        if self._cache_enabled and value is not None:
            self._cache[cache_key] = value

        return value

    def set(
        self,
        key: str,
        value: str,
        category: str,
        org_id: Optional[str] = None,
        is_secret: bool = True,
        updated_by: Optional[str] = None
    ) -> bool:
        """
        Set a configuration value in the database.

        Args:
            key: The setting key
            value: The value to store (will be encrypted if is_secret)
            category: The category (e.g., "llm", "compute")
            org_id: Organization ID for multi-tenant settings
            is_secret: Whether to encrypt the value
            updated_by: Who is making the change

        Returns:
            True if successful
        """
        try:
            from db_session import get_session_context
            from .service import SettingsService

            with get_session_context() as session:
                SettingsService.upsert_setting(
                    session, category, key, value,
                    is_secret=is_secret,
                    org_id=org_id,
                    updated_by=updated_by
                )

            # Invalidate cache
            cache_key = f"{org_id or 'global'}:{category}:{key}"
            self._cache.pop(cache_key, None)

            return True
        except Exception as e:
            logger.error(f"Failed to set config {key}: {e}")
            return False

    def invalidate_cache(self, key: Optional[str] = None):
        """Invalidate the config cache."""
        if key:
            # Invalidate specific key across all orgs/categories
            keys_to_remove = [k for k in self._cache if k.endswith(f":{key}")]
            for k in keys_to_remove:
                del self._cache[k]
        else:
            # Invalidate everything
            self._cache.clear()

    def _get_from_db(
        self,
        key: str,
        category: Optional[str],
        org_id: Optional[str]
    ) -> Optional[str]:
        """Get value from database."""
        try:
            from db_session import get_session_context
            from .service import SettingsService

            with get_session_context() as session:
                # If category is specified, use it directly
                if category:
                    return SettingsService.get_setting_value(
                        session, category, key, org_id
                    )

                # Otherwise, try common categories
                for cat in ["llm", "compute", "storage", "oauth", "feature"]:
                    value = SettingsService.get_setting_value(
                        session, cat, key, org_id
                    )
                    if value:
                        return value

                return None
        except Exception as e:
            # Database might not be available (e.g., during migrations)
            logger.debug(f"Could not read {key} from DB: {e}")
            return None

    def _get_from_env(self, key: str) -> Optional[str]:
        """Get value from environment variable."""
        env_key = self.KEY_ENV_MAP.get(key, key)
        return os.getenv(env_key)

    def _get_from_settings(self, key: str) -> Optional[str]:
        """Get value from Pydantic settings."""
        try:
            from core.config import settings

            attr_name = self.KEY_SETTINGS_MAP.get(key)
            if attr_name and hasattr(settings, attr_name):
                value = getattr(settings, attr_name)
                return str(value) if value is not None else None

            return None
        except Exception:
            return None

    def has_value(self, key: str, category: Optional[str] = None) -> bool:
        """Check if a configuration value exists (non-empty)."""
        value = self.get(key, category)
        return value is not None and len(value) > 0


# Global singleton instance
config = ConfigProvider()
