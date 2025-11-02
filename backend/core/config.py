"""Application configuration."""
from pydantic_settings import BaseSettings
from typing import Optional
from pathlib import Path


class Settings(BaseSettings):
    """Application settings."""
    
    # App
    app_name: str = "NEX.AI - AI Native Data Platform"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # API
    api_prefix: str = "/api/v1"
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]
    
    # Database
    database_url: Optional[str] = None  # TODO: Set default SQLite path
    
    # Security
    secret_key: Optional[str] = None  # TODO: Generate or load from env
    access_token_expire_minutes: int = 30
    
    # Logging
    log_level: str = "INFO"
    log_file: Optional[Path] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

