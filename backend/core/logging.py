"""Logging configuration."""
import logging
import sys
from pathlib import Path
from typing import Optional
from .config import settings


def setup_logging(log_file: Optional[Path] = None, level: Optional[str] = None) -> None:
    """
    Setup application logging.

    TODO: Implement proper logging configuration with:
    - File and console handlers
    - Rotating file handler for log files
    - Structured logging (JSON format)
    - Log levels configuration
    """
    log_level = level or settings.log_level
    resolved = getattr(logging, log_level.upper())

    # Configure root logger
    root = logging.getLogger()
    root.setLevel(resolved)
    if not root.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
        root.addHandler(handler)

    # Silence noisy third-party loggers (always WARNING regardless of app level)
    for name in ("botocore", "boto3", "urllib3", "s3transfer", "sqlalchemy"):
        logging.getLogger(name).setLevel(logging.WARNING)

    # TODO: Add file handler if log_file is provided


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for a module."""
    return logging.getLogger(name)
