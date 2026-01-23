"""Object Store service for S3-compatible storage."""
from .client import ObjectStoreClient
from .paths import ObjectStorePaths

__all__ = ["ObjectStoreClient", "ObjectStorePaths"]
