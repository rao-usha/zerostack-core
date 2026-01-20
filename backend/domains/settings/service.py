"""
Settings service with encryption support.

Handles CRUD operations for settings with automatic encryption/decryption
of secret values.
"""

import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID

from sqlmodel import Session, select

from .db_models import AppSetting
from .models import (
    SettingCreate, SettingUpdate, SettingCategory,
    SETTING_DEFINITIONS, SettingTestResult
)
from core.encryption import encrypt_password, decrypt_password, is_encrypted

logger = logging.getLogger(__name__)


class SettingsService:
    """Service for managing application settings."""

    @staticmethod
    def mask_value(value: str, is_secret: bool = True) -> str:
        """Mask a value for display (e.g., 'sk-abc...xyz')."""
        if not value or not is_secret:
            return value

        if len(value) <= 8:
            return "***"

        # Show first 4 and last 4 characters
        return f"{value[:4]}...{value[-4:]}"

    @staticmethod
    def get_setting(
        session: Session,
        category: str,
        key: str,
        org_id: Optional[str] = None
    ) -> Optional[AppSetting]:
        """Get a single setting by category and key."""
        query = select(AppSetting).where(
            AppSetting.category == category,
            AppSetting.key == key
        )
        if org_id:
            query = query.where(AppSetting.org_id == org_id)
        else:
            query = query.where(AppSetting.org_id.is_(None))

        return session.exec(query).first()

    @staticmethod
    def get_setting_value(
        session: Session,
        category: str,
        key: str,
        org_id: Optional[str] = None,
        decrypt: bool = True
    ) -> Optional[str]:
        """Get the decrypted value of a setting."""
        setting = SettingsService.get_setting(session, category, key, org_id)
        if not setting or not setting.value_encrypted:
            return None

        if decrypt and setting.is_secret:
            try:
                return decrypt_password(setting.value_encrypted)
            except Exception as e:
                logger.error(f"Failed to decrypt setting {key}: {e}")
                return None
        return setting.value_encrypted

    @staticmethod
    def list_settings(
        session: Session,
        category: Optional[str] = None,
        org_id: Optional[str] = None
    ) -> List[AppSetting]:
        """List settings, optionally filtered by category."""
        query = select(AppSetting)

        if category:
            query = query.where(AppSetting.category == category)

        if org_id:
            query = query.where(AppSetting.org_id == org_id)
        else:
            query = query.where(AppSetting.org_id.is_(None))

        query = query.order_by(AppSetting.category, AppSetting.key)
        return list(session.exec(query).all())

    @staticmethod
    def create_setting(
        session: Session,
        data: SettingCreate,
        org_id: Optional[str] = None,
        updated_by: Optional[str] = None
    ) -> AppSetting:
        """Create a new setting."""
        # Encrypt the value if it's a secret
        encrypted_value = None
        if data.value:
            if data.is_secret:
                encrypted_value = encrypt_password(data.value)
            else:
                encrypted_value = data.value

        setting = AppSetting(
            org_id=org_id,
            category=data.category.value,
            key=data.key,
            value_encrypted=encrypted_value,
            is_secret=data.is_secret,
            description=data.description,
            display_name=data.display_name,
            validation_pattern=data.validation_pattern,
            updated_by=updated_by
        )

        session.add(setting)
        session.commit()
        session.refresh(setting)

        logger.info(f"Created setting {data.category}/{data.key}")
        return setting

    @staticmethod
    def update_setting(
        session: Session,
        category: str,
        key: str,
        data: SettingUpdate,
        org_id: Optional[str] = None,
        updated_by: Optional[str] = None
    ) -> Optional[AppSetting]:
        """Update an existing setting."""
        setting = SettingsService.get_setting(session, category, key, org_id)
        if not setting:
            return None

        # Update value if provided
        if data.value is not None:
            is_secret = data.is_secret if data.is_secret is not None else setting.is_secret
            if is_secret:
                setting.value_encrypted = encrypt_password(data.value)
            else:
                setting.value_encrypted = data.value

        # Update other fields
        if data.description is not None:
            setting.description = data.description
        if data.display_name is not None:
            setting.display_name = data.display_name
        if data.is_secret is not None:
            setting.is_secret = data.is_secret

        setting.updated_at = datetime.utcnow()
        setting.updated_by = updated_by

        session.add(setting)
        session.commit()
        session.refresh(setting)

        logger.info(f"Updated setting {category}/{key}")
        return setting

    @staticmethod
    def delete_setting(
        session: Session,
        category: str,
        key: str,
        org_id: Optional[str] = None
    ) -> bool:
        """Delete a setting."""
        setting = SettingsService.get_setting(session, category, key, org_id)
        if not setting:
            return False

        session.delete(setting)
        session.commit()

        logger.info(f"Deleted setting {category}/{key}")
        return True

    @staticmethod
    def upsert_setting(
        session: Session,
        category: str,
        key: str,
        value: str,
        is_secret: bool = True,
        org_id: Optional[str] = None,
        updated_by: Optional[str] = None,
        description: Optional[str] = None,
        display_name: Optional[str] = None
    ) -> AppSetting:
        """Create or update a setting."""
        existing = SettingsService.get_setting(session, category, key, org_id)

        if existing:
            update_data = SettingUpdate(value=value)
            if description:
                update_data.description = description
            if display_name:
                update_data.display_name = display_name
            return SettingsService.update_setting(
                session, category, key, update_data, org_id, updated_by
            )
        else:
            create_data = SettingCreate(
                category=SettingCategory(category),
                key=key,
                value=value,
                is_secret=is_secret,
                description=description,
                display_name=display_name
            )
            return SettingsService.create_setting(
                session, create_data, org_id, updated_by
            )

    @staticmethod
    def get_category_summary(
        session: Session,
        org_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get summary of all categories with configured counts."""
        settings = SettingsService.list_settings(session, org_id=org_id)

        # Build a map of configured settings
        configured_keys = set()
        for s in settings:
            if s.value_encrypted:
                configured_keys.add(f"{s.category}:{s.key}")

        summaries = []
        for category, definition in SETTING_DEFINITIONS.items():
            expected_settings = definition.get("settings", [])
            configured_count = sum(
                1 for s in expected_settings
                if f"{category.value}:{s['key']}" in configured_keys
            )

            summaries.append({
                "category": category.value,
                "display_name": definition["display_name"],
                "description": definition["description"],
                "icon": definition.get("icon"),
                "total_settings": len(expected_settings),
                "configured_count": configured_count
            })

        return summaries

    @staticmethod
    def ensure_setting_definitions(
        session: Session,
        org_id: Optional[str] = None
    ) -> int:
        """Ensure all predefined settings exist in the database (without values)."""
        created_count = 0

        for category, definition in SETTING_DEFINITIONS.items():
            for setting_def in definition.get("settings", []):
                existing = SettingsService.get_setting(
                    session, category.value, setting_def["key"], org_id
                )

                if not existing:
                    # Create the setting definition without a value
                    setting = AppSetting(
                        org_id=org_id,
                        category=category.value,
                        key=setting_def["key"],
                        value_encrypted=None,
                        is_secret=setting_def.get("is_secret", True),
                        description=setting_def.get("description"),
                        display_name=setting_def.get("display_name"),
                        validation_pattern=setting_def.get("validation_pattern")
                    )
                    session.add(setting)
                    created_count += 1

        if created_count > 0:
            session.commit()
            logger.info(f"Created {created_count} setting definitions")

        return created_count

    @staticmethod
    async def test_api_key(
        session: Session,
        category: str,
        key: str,
        org_id: Optional[str] = None
    ) -> SettingTestResult:
        """Test if an API key is valid by making a test request."""
        value = SettingsService.get_setting_value(session, category, key, org_id)

        if not value:
            return SettingTestResult(
                key=key,
                valid=False,
                message="No value configured"
            )

        try:
            if key == "OPENAI_API_KEY":
                return await SettingsService._test_openai_key(value)
            elif key == "ANTHROPIC_API_KEY":
                return await SettingsService._test_anthropic_key(value)
            elif key == "RUNPOD_API_KEY":
                return await SettingsService._test_runpod_key(value)
            else:
                return SettingTestResult(
                    key=key,
                    valid=True,
                    message="Key is configured (validation not implemented)"
                )
        except Exception as e:
            return SettingTestResult(
                key=key,
                valid=False,
                message=f"Test failed: {str(e)}"
            )

    @staticmethod
    async def _test_openai_key(api_key: str) -> SettingTestResult:
        """Test OpenAI API key."""
        import httpx

        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.openai.com/v1/models",
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=10.0
            )

            if response.status_code == 200:
                models = response.json().get("data", [])
                return SettingTestResult(
                    key="OPENAI_API_KEY",
                    valid=True,
                    message=f"Valid key with access to {len(models)} models",
                    details={"model_count": len(models)}
                )
            elif response.status_code == 401:
                return SettingTestResult(
                    key="OPENAI_API_KEY",
                    valid=False,
                    message="Invalid API key"
                )
            else:
                return SettingTestResult(
                    key="OPENAI_API_KEY",
                    valid=False,
                    message=f"API returned status {response.status_code}"
                )

    @staticmethod
    async def _test_anthropic_key(api_key: str) -> SettingTestResult:
        """Test Anthropic API key."""
        import httpx

        async with httpx.AsyncClient() as client:
            # Anthropic doesn't have a simple test endpoint, try messages with minimal payload
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json"
                },
                json={
                    "model": "claude-3-haiku-20240307",
                    "max_tokens": 1,
                    "messages": [{"role": "user", "content": "Hi"}]
                },
                timeout=10.0
            )

            if response.status_code == 200:
                return SettingTestResult(
                    key="ANTHROPIC_API_KEY",
                    valid=True,
                    message="Valid API key"
                )
            elif response.status_code == 401:
                return SettingTestResult(
                    key="ANTHROPIC_API_KEY",
                    valid=False,
                    message="Invalid API key"
                )
            else:
                error = response.json().get("error", {})
                return SettingTestResult(
                    key="ANTHROPIC_API_KEY",
                    valid=False,
                    message=error.get("message", f"Status {response.status_code}")
                )

    @staticmethod
    async def _test_runpod_key(api_key: str) -> SettingTestResult:
        """Test RunPod API key."""
        import httpx

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.runpod.io/graphql",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={"query": "{ myself { id email } }"},
                timeout=10.0
            )

            if response.status_code == 200:
                data = response.json()
                if "data" in data and data["data"].get("myself"):
                    user = data["data"]["myself"]
                    return SettingTestResult(
                        key="RUNPOD_API_KEY",
                        valid=True,
                        message=f"Valid key for {user.get('email', 'user')}",
                        details={"user_id": user.get("id")}
                    )
                return SettingTestResult(
                    key="RUNPOD_API_KEY",
                    valid=False,
                    message="Invalid response from API"
                )
            else:
                return SettingTestResult(
                    key="RUNPOD_API_KEY",
                    valid=False,
                    message=f"API returned status {response.status_code}"
                )
