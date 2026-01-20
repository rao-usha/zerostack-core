"""
Settings API router.

Provides endpoints for managing application settings:
- List categories and settings
- Get/update individual settings
- Test API key validity
"""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlmodel import Session

from .models import (
    SettingCreate, SettingUpdate, SettingResponse, SettingListResponse,
    SettingTestResult, CategorySummary, CategoriesResponse,
    SETTING_DEFINITIONS, SettingCategory
)
from .service import SettingsService
from db_session import get_session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/settings", tags=["settings"])


def _to_response(setting, mask: bool = True) -> SettingResponse:
    """Convert a database setting to response schema."""
    value_masked = None
    has_value = bool(setting.value_encrypted)

    if has_value and mask:
        # Decrypt for masking (we need the actual value to mask it properly)
        from core.encryption import decrypt_password
        try:
            if setting.is_secret:
                decrypted = decrypt_password(setting.value_encrypted)
                value_masked = SettingsService.mask_value(decrypted, setting.is_secret)
            else:
                value_masked = setting.value_encrypted
        except Exception:
            value_masked = "***"
    elif has_value and not mask:
        value_masked = setting.value_encrypted if not setting.is_secret else "***"

    return SettingResponse(
        id=setting.id,
        category=setting.category,
        key=setting.key,
        value_masked=value_masked,
        is_secret=setting.is_secret,
        description=setting.description,
        display_name=setting.display_name,
        has_value=has_value,
        updated_at=setting.updated_at,
        updated_by=setting.updated_by
    )


# ============================================
# Category Endpoints
# ============================================

@router.get("", response_model=CategoriesResponse)
async def list_categories(
    session: Session = Depends(get_session)
):
    """
    List all setting categories with configuration status.

    Returns a summary of each category showing how many settings
    are configured vs expected.
    """
    # Ensure setting definitions exist
    SettingsService.ensure_setting_definitions(session)

    summaries = SettingsService.get_category_summary(session)
    return CategoriesResponse(
        categories=[CategorySummary(**s) for s in summaries]
    )


# ============================================
# Settings by Category
# ============================================

@router.get("/{category}", response_model=SettingListResponse)
async def list_settings_by_category(
    category: SettingCategory,
    session: Session = Depends(get_session)
):
    """
    List all settings in a category.

    Values are masked for secrets (e.g., "sk-...xyz").
    """
    # Ensure definitions exist
    SettingsService.ensure_setting_definitions(session)

    settings = SettingsService.list_settings(session, category=category.value)

    # Also include expected settings that aren't in DB yet
    expected_keys = {
        s["key"] for s in SETTING_DEFINITIONS.get(category, {}).get("settings", [])
    }
    existing_keys = {s.key for s in settings}

    # Add placeholders for missing settings
    results = [_to_response(s) for s in settings]

    for key in expected_keys - existing_keys:
        # Find the definition
        for s_def in SETTING_DEFINITIONS.get(category, {}).get("settings", []):
            if s_def["key"] == key:
                results.append(SettingResponse(
                    id=None,
                    category=category.value,
                    key=key,
                    value_masked=None,
                    is_secret=s_def.get("is_secret", True),
                    description=s_def.get("description"),
                    display_name=s_def.get("display_name"),
                    has_value=False,
                    updated_at=None,
                    updated_by=None
                ))
                break

    return SettingListResponse(
        settings=sorted(results, key=lambda x: x.key),
        total=len(results)
    )


@router.get("/{category}/{key}", response_model=SettingResponse)
async def get_setting(
    category: SettingCategory,
    key: str,
    session: Session = Depends(get_session)
):
    """
    Get a single setting by category and key.

    Value is masked for secrets.
    """
    setting = SettingsService.get_setting(session, category.value, key)
    if not setting:
        # Check if it's a known setting
        known_keys = {
            s["key"] for s in SETTING_DEFINITIONS.get(category, {}).get("settings", [])
        }
        if key not in known_keys:
            raise HTTPException(status_code=404, detail="Setting not found")

        # Return a placeholder
        for s_def in SETTING_DEFINITIONS.get(category, {}).get("settings", []):
            if s_def["key"] == key:
                return SettingResponse(
                    id=None,
                    category=category.value,
                    key=key,
                    value_masked=None,
                    is_secret=s_def.get("is_secret", True),
                    description=s_def.get("description"),
                    display_name=s_def.get("display_name"),
                    has_value=False,
                    updated_at=None,
                    updated_by=None
                )

        raise HTTPException(status_code=404, detail="Setting not found")

    return _to_response(setting)


@router.put("/{category}/{key}", response_model=SettingResponse)
async def update_setting(
    category: SettingCategory,
    key: str,
    data: SettingUpdate,
    session: Session = Depends(get_session)
):
    """
    Update a setting value.

    If the setting doesn't exist, it will be created.
    The value will be encrypted if the setting is marked as secret.
    """
    # Find existing or create
    setting = SettingsService.get_setting(session, category.value, key)

    if setting:
        updated = SettingsService.update_setting(
            session, category.value, key, data
        )
        return _to_response(updated)
    else:
        # Get definition for this key
        setting_def = None
        for s_def in SETTING_DEFINITIONS.get(category, {}).get("settings", []):
            if s_def["key"] == key:
                setting_def = s_def
                break

        is_secret = True
        description = None
        display_name = None

        if setting_def:
            is_secret = setting_def.get("is_secret", True)
            description = setting_def.get("description")
            display_name = setting_def.get("display_name")

        if data.is_secret is not None:
            is_secret = data.is_secret
        if data.description is not None:
            description = data.description
        if data.display_name is not None:
            display_name = data.display_name

        create_data = SettingCreate(
            category=category,
            key=key,
            value=data.value or "",
            is_secret=is_secret,
            description=description,
            display_name=display_name
        )

        created = SettingsService.create_setting(session, create_data)
        return _to_response(created)


@router.delete("/{category}/{key}", status_code=204)
async def delete_setting(
    category: SettingCategory,
    key: str,
    session: Session = Depends(get_session)
):
    """
    Delete a setting (clear its value).

    The setting definition remains but the value is removed.
    """
    setting = SettingsService.get_setting(session, category.value, key)
    if not setting:
        raise HTTPException(status_code=404, detail="Setting not found")

    # Clear the value instead of deleting entirely
    setting.value_encrypted = None
    session.add(setting)
    session.commit()

    return None


# ============================================
# Testing Endpoints
# ============================================

@router.post("/test/{category}/{key}", response_model=SettingTestResult)
async def test_setting(
    category: SettingCategory,
    key: str,
    session: Session = Depends(get_session)
):
    """
    Test if an API key or setting is valid.

    Makes a test request to the appropriate service to verify
    the key works. Currently supports:
    - OPENAI_API_KEY
    - ANTHROPIC_API_KEY
    - RUNPOD_API_KEY
    """
    result = await SettingsService.test_api_key(session, category.value, key)
    return result


@router.post("/test/{category}", response_model=dict)
async def test_category(
    category: SettingCategory,
    session: Session = Depends(get_session)
):
    """
    Test all settings in a category.

    Returns a map of key -> test result.
    """
    settings = SettingsService.list_settings(session, category=category.value)
    results = {}

    for setting in settings:
        if setting.value_encrypted:
            result = await SettingsService.test_api_key(
                session, category.value, setting.key
            )
            results[setting.key] = {
                "valid": result.valid,
                "message": result.message
            }
        else:
            results[setting.key] = {
                "valid": False,
                "message": "No value configured"
            }

    return {"results": results}


# ============================================
# Bulk Operations
# ============================================

@router.post("/seed-from-env", response_model=dict)
async def seed_from_env(
    overwrite: bool = Query(default=False, description="Overwrite existing values"),
    session: Session = Depends(get_session)
):
    """
    Seed database settings from environment variables.

    Copies values from .env/environment to the database.
    Use overwrite=true to replace existing values.
    """
    import os
    from .config_provider import ConfigProvider

    seeded = []
    skipped = []

    for category, definition in SETTING_DEFINITIONS.items():
        for s_def in definition.get("settings", []):
            key = s_def["key"]
            env_key = ConfigProvider.KEY_ENV_MAP.get(key, key)
            env_value = os.getenv(env_key)

            if not env_value:
                skipped.append(key)
                continue

            existing = SettingsService.get_setting(session, category.value, key)

            if existing and existing.value_encrypted and not overwrite:
                skipped.append(key)
                continue

            # Create or update
            SettingsService.upsert_setting(
                session,
                category.value,
                key,
                env_value,
                is_secret=s_def.get("is_secret", True),
                description=s_def.get("description"),
                display_name=s_def.get("display_name"),
                updated_by="system:seed"
            )
            seeded.append(key)

    return {
        "seeded": seeded,
        "skipped": skipped,
        "seeded_count": len(seeded),
        "skipped_count": len(skipped)
    }
