"""
Seed settings from .env file to database.

Usage:
    python scripts/seed_settings.py
"""

import os
import sys

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine, text
from sqlmodel import Session

from core.config import settings
from domains.settings.models import SETTING_DEFINITIONS, SettingCategory
from domains.settings.service import SettingsService
from domains.settings.db_models import AppSetting


def create_table_if_not_exists(engine):
    """Create the app_settings table if it doesn't exist."""
    create_sql = """
    CREATE TABLE IF NOT EXISTS app_settings (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        org_id VARCHAR(100),
        category VARCHAR(64) NOT NULL,
        key VARCHAR(255) NOT NULL,
        value_encrypted TEXT,
        is_secret BOOLEAN DEFAULT true NOT NULL,
        description TEXT,
        display_name VARCHAR(255),
        validation_pattern VARCHAR(255),
        created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
        updated_by VARCHAR(100)
    );

    CREATE INDEX IF NOT EXISTS ix_app_settings_category ON app_settings (category);
    CREATE UNIQUE INDEX IF NOT EXISTS ix_app_settings_unique_key
        ON app_settings (org_id, category, key)
        WHERE org_id IS NOT NULL;
    CREATE UNIQUE INDEX IF NOT EXISTS ix_app_settings_unique_key_global
        ON app_settings (category, key)
        WHERE org_id IS NULL;
    """

    with engine.connect() as conn:
        for statement in create_sql.split(';'):
            statement = statement.strip()
            if statement:
                try:
                    conn.execute(text(statement))
                except Exception as e:
                    # Index might already exist
                    if 'already exists' not in str(e).lower():
                        print(f"Warning: {e}")
        conn.commit()

    print("[OK] app_settings table ready")


def seed_from_env(session: Session):
    """Seed settings from environment variables."""

    # Mapping of setting keys to env var names (with fallbacks)
    env_mappings = {
        "OPENAI_API_KEY": ["OPENAI_API_KEY"],
        "ANTHROPIC_API_KEY": ["ANTHROPIC_API_KEY"],
        "GOOGLE_API_KEY": ["GOOGLE_API_KEY", "GEMINI_API_KEY"],  # Try both
        "XAI_API_KEY": ["XAI_API_KEY", "X_AI_API_KEY"],  # Try both
        "RUNPOD_API_KEY": ["RUNPOD_API_KEY"],
        "RUNPOD_DEFAULT_GPU": ["RUNPOD_DEFAULT_GPU"],
        "RUNPOD_ENDPOINT_ID": ["RUNPOD_ENDPOINT_ID"],
        "S3_ENDPOINT": ["S3_ENDPOINT"],
        "S3_ACCESS_KEY": ["S3_ACCESS_KEY"],
        "S3_SECRET_KEY": ["S3_SECRET_KEY"],
        "S3_BUCKET": ["S3_BUCKET"],
        "GOOGLE_OAUTH_CLIENT_ID": ["GOOGLE_OAUTH_CLIENT_ID"],
        "GOOGLE_OAUTH_CLIENT_SECRET": ["GOOGLE_OAUTH_CLIENT_SECRET"],
    }

    seeded = []
    skipped = []

    for category, definition in SETTING_DEFINITIONS.items():
        for setting_def in definition.get("settings", []):
            key = setting_def["key"]
            env_keys = env_mappings.get(key, [key])

            # Try each possible env var name
            env_value = None
            for env_key in env_keys:
                env_value = os.getenv(env_key)
                if env_value:
                    break

            if not env_value:
                skipped.append(key)
                continue

            # Check if already exists
            existing = SettingsService.get_setting(session, category.value, key)
            if existing and existing.value_encrypted:
                print(f"  [SKIP] {key} already configured, skipping")
                skipped.append(key)
                continue

            # Upsert the setting
            try:
                SettingsService.upsert_setting(
                    session,
                    category.value,
                    key,
                    env_value,
                    is_secret=setting_def.get("is_secret", True),
                    description=setting_def.get("description"),
                    display_name=setting_def.get("display_name"),
                    updated_by="seed_script"
                )
                print(f"  [OK] {key} seeded from .env")
                seeded.append(key)
            except Exception as e:
                print(f"  [ERR] {key} failed: {e}")

    return seeded, skipped


def main():
    print("[*] Setting up app_settings table and seeding from .env\n")

    # Create engine
    engine = create_engine(settings.database_url)

    # Create table if needed
    create_table_if_not_exists(engine)

    # Seed from .env
    print("\n[*] Seeding settings from .env...")
    with Session(engine) as session:
        seeded, skipped = seed_from_env(session)

    print(f"\n[OK] Done! Seeded {len(seeded)} settings, skipped {len(skipped)}")

    if seeded:
        print(f"\nSeeded: {', '.join(seeded)}")


if __name__ == "__main__":
    main()
