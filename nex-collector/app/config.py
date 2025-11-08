"""Configuration management."""
from pydantic import BaseModel, Field
import os
from typing import List


class Settings(BaseModel):
    """Application settings."""
    
    # Database
    DATABASE_URL: str = Field(
        default=os.getenv("DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/nex_collector")
    )
    
    # Redis
    REDIS_URL: str = Field(
        default=os.getenv("REDIS_URL", "redis://localhost:6379/0")
    )
    
    # Authentication
    NEX_WRITE_TOKEN: str = Field(
        default=os.getenv("NEX_WRITE_TOKEN", "dev-secret")
    )
    
    # Integration mode
    MODE_INTEGRATION: str = Field(
        default=os.getenv("MODE_INTEGRATION", "separate")
    )
    
    # NEX API integration (optional)
    NEX_API_BASE: str = Field(
        default=os.getenv("NEX_API_BASE", "")
    )
    NEX_TOKEN: str = Field(
        default=os.getenv("NEX_TOKEN", "")
    )
    
    # Provider configuration
    PROVIDERS_ENABLED: str = Field(
        default=os.getenv("PROVIDERS_ENABLED", "openai")
    )
    DEFAULT_PROVIDER: str = Field(
        default=os.getenv("DEFAULT_PROVIDER", "openai")
    )
    
    # OpenAI
    OPENAI_API_KEY: str = Field(
        default=os.getenv("OPENAI_API_KEY", "")
    )
    
    # Anthropic (for future)
    ANTHROPIC_API_KEY: str = Field(
        default=os.getenv("ANTHROPIC_API_KEY", "")
    )
    
    # Google (for future)
    GOOGLE_API_KEY: str = Field(
        default=os.getenv("GOOGLE_API_KEY", "")
    )
    
    # Data directory
    DATA_DIR: str = Field(
        default=os.getenv("DATA_DIR", "./data")
    )
    
    # Aggregator settings
    AGGREGATOR_INTERVAL_SECS: int = Field(
        default=int(os.getenv("AGGREGATOR_INTERVAL_SECS", "3600"))
    )
    REQUIRE_APPROVAL: bool = Field(
        default=os.getenv("REQUIRE_APPROVAL", "true").lower() == "true"
    )
    
    # Embeddings
    EMBEDDINGS_ENABLED: bool = Field(
        default=os.getenv("EMBEDDINGS_ENABLED", "false").lower() == "true"
    )
    
    @property
    def providers_list(self) -> List[str]:
        """Parse providers enabled."""
        return [p.strip() for p in self.PROVIDERS_ENABLED.split(",") if p.strip()]
    
    @property
    def is_integrated(self) -> bool:
        """Check if integration mode is enabled."""
        return self.MODE_INTEGRATION == "integrated" and bool(self.NEX_API_BASE)


settings = Settings()

