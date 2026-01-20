"""
Pydantic models for settings API.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field
from enum import Enum


class SettingCategory(str, Enum):
    """Categories for grouping settings."""
    LLM = "llm"
    COMPUTE = "compute"
    STORAGE = "storage"
    OAUTH = "oauth"
    FEATURE = "feature"


# ============================================
# Setting Schemas
# ============================================

class SettingCreate(BaseModel):
    """Schema for creating a new setting."""
    category: SettingCategory
    key: str = Field(..., min_length=1, max_length=255)
    value: str = Field(..., min_length=0)  # Will be encrypted
    is_secret: bool = True
    description: Optional[str] = None
    display_name: Optional[str] = None
    validation_pattern: Optional[str] = None


class SettingUpdate(BaseModel):
    """Schema for updating a setting."""
    value: Optional[str] = None  # Will be encrypted
    description: Optional[str] = None
    display_name: Optional[str] = None
    is_secret: Optional[bool] = None


class SettingResponse(BaseModel):
    """Response schema for a single setting (value masked for secrets)."""
    id: UUID
    category: str
    key: str
    value_masked: Optional[str] = None  # e.g., "sk-...xyz" for secrets
    is_secret: bool
    description: Optional[str] = None
    display_name: Optional[str] = None
    has_value: bool = False  # Whether a value is set
    updated_at: Optional[datetime] = None
    updated_by: Optional[str] = None

    model_config = {"from_attributes": True}


class SettingListResponse(BaseModel):
    """Response schema for listing settings."""
    settings: List[SettingResponse]
    total: int


class SettingTestResult(BaseModel):
    """Result of testing a setting (e.g., API key validation)."""
    key: str
    valid: bool
    message: str
    details: Optional[Dict[str, Any]] = None


class CategorySummary(BaseModel):
    """Summary of settings in a category."""
    category: str
    display_name: str
    description: str
    total_settings: int
    configured_count: int
    icon: Optional[str] = None


class CategoriesResponse(BaseModel):
    """Response schema for listing categories."""
    categories: List[CategorySummary]


# ============================================
# Predefined Settings (what we expect to exist)
# ============================================

# Define expected settings per category
SETTING_DEFINITIONS = {
    SettingCategory.LLM: {
        "display_name": "LLM API Keys",
        "description": "API keys for language model providers",
        "icon": "brain",
        "settings": [
            {
                "key": "OPENAI_API_KEY",
                "display_name": "OpenAI API Key",
                "description": "API key for OpenAI (GPT-4, GPT-4o, etc.)",
                "validation_pattern": r"^sk-[a-zA-Z0-9_-]+$"
            },
            {
                "key": "ANTHROPIC_API_KEY",
                "display_name": "Anthropic API Key",
                "description": "API key for Anthropic (Claude models)",
                "validation_pattern": r"^sk-ant-[a-zA-Z0-9_-]+$"
            },
            {
                "key": "GOOGLE_API_KEY",
                "display_name": "Google AI API Key",
                "description": "API key for Google AI (Gemini models)",
                "validation_pattern": None
            },
            {
                "key": "XAI_API_KEY",
                "display_name": "xAI API Key",
                "description": "API key for xAI (Grok models)",
                "validation_pattern": None
            },
        ]
    },
    SettingCategory.COMPUTE: {
        "display_name": "Compute & GPU",
        "description": "Configuration for GPU runners and compute resources",
        "icon": "cpu",
        "settings": [
            {
                "key": "RUNPOD_API_KEY",
                "display_name": "RunPod API Key",
                "description": "API key for RunPod GPU instances",
                "validation_pattern": None
            },
            {
                "key": "RUNPOD_DEFAULT_GPU",
                "display_name": "Default GPU Type",
                "description": "Default GPU type for RunPod (e.g., 'NVIDIA RTX A5000')",
                "validation_pattern": None,
                "is_secret": False
            },
            {
                "key": "RUNPOD_ENDPOINT_ID",
                "display_name": "RunPod Endpoint ID",
                "description": "Serverless endpoint ID for RunPod",
                "validation_pattern": None,
                "is_secret": False
            },
        ]
    },
    SettingCategory.STORAGE: {
        "display_name": "Storage (S3/MinIO)",
        "description": "Object storage configuration for datasets and artifacts",
        "icon": "database",
        "settings": [
            {
                "key": "S3_ENDPOINT",
                "display_name": "S3 Endpoint URL",
                "description": "S3-compatible endpoint URL (e.g., http://localhost:9000)",
                "validation_pattern": None,
                "is_secret": False
            },
            {
                "key": "S3_ACCESS_KEY",
                "display_name": "S3 Access Key",
                "description": "Access key for S3/MinIO",
                "validation_pattern": None
            },
            {
                "key": "S3_SECRET_KEY",
                "display_name": "S3 Secret Key",
                "description": "Secret key for S3/MinIO",
                "validation_pattern": None
            },
            {
                "key": "S3_BUCKET",
                "display_name": "S3 Bucket Name",
                "description": "Default bucket name for storage",
                "validation_pattern": None,
                "is_secret": False
            },
        ]
    },
    SettingCategory.OAUTH: {
        "display_name": "OAuth & Integrations",
        "description": "OAuth credentials for third-party integrations",
        "icon": "key",
        "settings": [
            {
                "key": "GOOGLE_OAUTH_CLIENT_ID",
                "display_name": "Google OAuth Client ID",
                "description": "OAuth client ID for Google Drive integration",
                "validation_pattern": None
            },
            {
                "key": "GOOGLE_OAUTH_CLIENT_SECRET",
                "display_name": "Google OAuth Client Secret",
                "description": "OAuth client secret for Google Drive integration",
                "validation_pattern": None
            },
        ]
    },
    SettingCategory.FEATURE: {
        "display_name": "Feature Flags",
        "description": "Toggle features on/off",
        "icon": "toggle",
        "settings": [
            {
                "key": "ENABLE_GPU_RUNNER",
                "display_name": "Enable GPU Runner",
                "description": "Enable GPU-accelerated model training",
                "validation_pattern": r"^(true|false)$",
                "is_secret": False
            },
            {
                "key": "ENABLE_GDRIVE_INTEGRATION",
                "display_name": "Enable Google Drive",
                "description": "Enable Google Drive file import",
                "validation_pattern": r"^(true|false)$",
                "is_secret": False
            },
        ]
    },
}
