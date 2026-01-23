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
    secret_key: Optional[str] = None
    access_token_expire_minutes: int = 30

    # Logging
    log_level: str = "INFO"
    log_file: Optional[Path] = None

    # OpenAI
    openai_api_key: Optional[str] = None

    # ========================================
    # Explorer Database (external data sources)
    # Defaults match primary DATABASE_URL for easy local setup
    # ========================================
    explorer_db_host: str = "localhost"
    explorer_db_port: int = 5432
    explorer_db_user: str = "nex"
    explorer_db_password: str = "nex"
    explorer_db_name: str = "nex"

    # ========================================
    # Object Storage (MinIO/S3)
    # ========================================
    s3_endpoint: str = "http://localhost:9000"
    s3_access_key: str = "minioadmin"
    s3_secret_key: str = "minioadmin"
    s3_bucket: str = "nex-data"
    s3_use_ssl: bool = False

    # ========================================
    # Compute Adapter Configuration
    # ========================================
    compute_adapter: str = "local"  # "local" | "ssh" | "runpod" | "k8s_gateway" | "disabled"

    # SSH Adapter settings
    ssh_host: Optional[str] = None
    ssh_port: int = 22
    ssh_user: str = "ubuntu"
    ssh_key_path: Optional[str] = None
    ssh_docker_runtime: str = "nvidia"  # For GPU support

    # RunPod Adapter settings
    runpod_api_key: Optional[str] = None
    runpod_default_gpu: str = "NVIDIA RTX A5000"
    runpod_template_id: Optional[str] = None
    runpod_endpoint_id: Optional[str] = None
    runpod_pod_id: Optional[str] = None
    runpod_ssh_key_path: Optional[str] = None

    # K8s Gateway settings
    k8s_gateway_url: Optional[str] = None
    k8s_namespace: str = "nex-compute"
    k8s_gpu_node_selector: Optional[str] = None

    # ========================================
    # GPU Runner Settings
    # ========================================
    gpu_count_default: int = 1
    run_timeout_seconds: int = 3600  # 1 hour default
    derived_asset_ttl_days: int = 14
    finalizer_poll_interval_seconds: int = 30

    # ========================================
    # Container Registry
    # ========================================
    container_registry: str = "localhost:5000"

    # ========================================
    # Codat Integration (Accounting Systems)
    # ========================================
    codat_api_key: Optional[str] = None
    codat_webhook_secret: Optional[str] = None

    # ========================================
    # Merge.dev Integration (HR/CRM)
    # ========================================
    merge_api_key: Optional[str] = None
    merge_webhook_secret: Optional[str] = None

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.cors_origins.split(",")]

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "allow",
    }


settings = Settings()
