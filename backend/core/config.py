"""Application configuration."""
from pydantic_settings import BaseSettings
from pydantic import field_validator
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
    cors_origins: str = "http://localhost:3000,http://localhost:5173"
    
    @field_validator("cors_origins", mode="before")
    @classmethod
    def validate_cors_origins(cls, v):
        """Handle empty CORS_ORIGINS values."""
        if v is None or v == "":
            return "http://localhost:3000,http://localhost:5173"
        return v
    
    # Database
    database_url: str = "postgresql+psycopg://nex:nex@localhost:5432/nex"
    
    # Security
    secret_key: Optional[str] = None  # TODO: Generate or load from env
    access_token_expire_minutes: int = 30
    
    # Logging
    log_level: str = "INFO"
    log_file: Optional[Path] = None
    
    # OpenAI
    openai_api_key: Optional[str] = None
    
    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.cors_origins.split(",")]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        # Allow loading from environment variables (for Docker)
        extra = "allow"


settings = Settings()

