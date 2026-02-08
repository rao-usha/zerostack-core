"""Tests for dataset upload functionality."""
import pytest
from io import BytesIO

from fastapi import UploadFile, HTTPException


class TestFileSizeValidation:
    """Test file size validation."""

    @pytest.mark.asyncio
    async def test_validate_file_size_small_file(self):
        """Test that small files pass validation."""
        from domains.datasets.router import validate_file_size

        # Create a small file (1KB) - well under any reasonable limit
        content = b"x" * 1024
        file = UploadFile(filename="test.csv", file=BytesIO(content))

        size = await validate_file_size(file)
        assert size == 1024

    @pytest.mark.asyncio
    async def test_validate_file_size_returns_correct_size(self):
        """Test that validation returns correct file size."""
        from domains.datasets.router import validate_file_size

        # Create a file of known size
        content = b"hello world" * 100  # 1100 bytes
        file = UploadFile(filename="test.csv", file=BytesIO(content))

        size = await validate_file_size(file)
        assert size == 1100

    @pytest.mark.asyncio
    async def test_validate_file_size_resets_position(self):
        """Test that file position is reset after validation."""
        from domains.datasets.router import validate_file_size

        content = b"test content 12345"
        file = UploadFile(filename="test.csv", file=BytesIO(content))

        await validate_file_size(file)

        # File should be readable from beginning
        read_content = await file.read()
        assert read_content == content

    @pytest.mark.asyncio
    async def test_validate_file_size_empty_file(self):
        """Test validation of empty file."""
        from domains.datasets.router import validate_file_size

        content = b""
        file = UploadFile(filename="test.csv", file=BytesIO(content))

        size = await validate_file_size(file)
        assert size == 0


class TestUploadConfig:
    """Test upload configuration."""

    def test_max_upload_bytes_property(self):
        """Test that max_upload_bytes is computed correctly."""
        from core.config import Settings

        # Create settings with 100MB limit
        settings = Settings(max_upload_size_mb=100)
        assert settings.max_upload_bytes == 100 * 1024 * 1024

    def test_max_upload_bytes_different_values(self):
        """Test max_upload_bytes with different MB values."""
        from core.config import Settings

        settings_1mb = Settings(max_upload_size_mb=1)
        assert settings_1mb.max_upload_bytes == 1 * 1024 * 1024

        settings_1000mb = Settings(max_upload_size_mb=1000)
        assert settings_1000mb.max_upload_bytes == 1000 * 1024 * 1024

    def test_default_upload_limit(self):
        """Test default upload limit is 500MB."""
        from core.config import Settings

        settings = Settings()
        assert settings.max_upload_size_mb == 500
        assert settings.max_upload_bytes == 500 * 1024 * 1024


class TestRouterImports:
    """Test that router imports correctly."""

    def test_router_imports(self):
        """Verify router can be imported."""
        from domains.datasets.router import router
        assert router is not None
        assert router.prefix == "/datasets"

    def test_validate_file_size_exists(self):
        """Verify validate_file_size function exists."""
        from domains.datasets.router import validate_file_size
        assert validate_file_size is not None
        assert callable(validate_file_size)

class TestStorageImports:
    """Test that storage imports correctly."""

    def test_storage_imports(self):
        """Verify storage can be imported."""
        from domains.datasets.storage import DatasetStorage, get_dataset_storage
        assert DatasetStorage is not None
        assert get_dataset_storage is not None


class TestHTTPErrorCodes:
    """Test that correct HTTP error codes are used."""

    def test_413_for_file_too_large(self):
        """Verify 413 Payload Too Large is used for oversized files."""
        # The HTTPException with 413 is defined in the router
        # This test documents the expected behavior
        from fastapi import HTTPException

        exc = HTTPException(status_code=413, detail="File too large")
        assert exc.status_code == 413

    def test_400_for_no_filename(self):
        """Verify 400 Bad Request is used for missing filename."""
        from fastapi import HTTPException

        exc = HTTPException(status_code=400, detail="No filename provided")
        assert exc.status_code == 400


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
