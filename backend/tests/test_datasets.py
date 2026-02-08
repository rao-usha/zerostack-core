"""Tests for datasets domain - dataset management, versioning, and storage."""
import pytest
from datetime import datetime
from uuid import uuid4

from domains.datasets.models import (
    DatasetStatus, DatasetSourceType,
    ColumnSchema, DatasetSchema, Dataset, DatasetCreate, DatasetUpdate,
    DatasetVersion, DatasetUploadResponse, DatasetListResponse,
    DatasetVersionListResponse, DatasetPreviewResponse, DatasetDownloadResponse,
    QualityProfile, Transform, SyntheticDataRequest, SyntheticDataResult
)


class TestDatasetEnums:
    """Test dataset enum values."""

    def test_dataset_status(self):
        """Test dataset status enum values."""
        assert DatasetStatus.ACTIVE.value == "active"
        assert DatasetStatus.PROCESSING.value == "processing"
        assert DatasetStatus.ERROR.value == "error"
        assert DatasetStatus.ARCHIVED.value == "archived"

    def test_dataset_source_type(self):
        """Test dataset source type enum values."""
        assert DatasetSourceType.UPLOAD.value == "upload"
        assert DatasetSourceType.NOTEBOOK.value == "notebook"
        assert DatasetSourceType.CONNECTION.value == "connection"
        assert DatasetSourceType.SYNTHETIC.value == "synthetic"


class TestSchemaModels:
    """Test schema models."""

    def test_column_schema_minimal(self):
        """Test column schema with minimal fields."""
        column = ColumnSchema(name="id", dtype="int64")
        assert column.name == "id"
        assert column.dtype == "int64"
        assert column.nullable is True
        assert column.stats is None

    def test_column_schema_full(self):
        """Test column schema with all fields."""
        column = ColumnSchema(
            name="price",
            dtype="float64",
            nullable=False,
            stats={
                "min": 0.0,
                "max": 1000.0,
                "mean": 50.0,
                "null_count": 0
            }
        )
        assert column.nullable is False
        assert column.stats["mean"] == 50.0

    def test_dataset_schema(self):
        """Test dataset schema model."""
        schema = DatasetSchema(columns=[
            ColumnSchema(name="id", dtype="int64"),
            ColumnSchema(name="name", dtype="string"),
            ColumnSchema(name="price", dtype="float64")
        ])
        assert len(schema.columns) == 3
        assert schema.columns[0].name == "id"


class TestDatasetModels:
    """Test dataset models."""

    def test_dataset_create_minimal(self):
        """Test creating dataset with minimal fields."""
        dataset = DatasetCreate(name="My Dataset")
        assert dataset.name == "My Dataset"
        assert dataset.description is None
        assert dataset.org_id == "default"

    def test_dataset_create_full(self):
        """Test creating dataset with all fields."""
        dataset = DatasetCreate(
            name="Sales Data 2024",
            description="Quarterly sales data",
            tags=["sales", "2024", "quarterly"],
            org_id="acme_corp"
        )
        assert dataset.description == "Quarterly sales data"
        assert "sales" in dataset.tags
        assert dataset.org_id == "acme_corp"

    def test_dataset_update(self):
        """Test dataset update model."""
        update = DatasetUpdate(
            name="Updated Name",
            description="Updated description",
            tags=["updated"],
            status=DatasetStatus.ARCHIVED
        )
        assert update.status == DatasetStatus.ARCHIVED

    def test_dataset_update_partial(self):
        """Test partial dataset update."""
        update = DatasetUpdate(name="Just Name Update")
        assert update.name == "Just Name Update"
        assert update.description is None
        assert update.status is None

    def test_dataset_response(self):
        """Test dataset response model."""
        dataset = Dataset(
            id=uuid4(),
            name="Customer Data",
            description="Customer information",
            status=DatasetStatus.ACTIVE,
            source_type=DatasetSourceType.UPLOAD,
            source_id=None,
            data_schema={"columns": [{"name": "id", "dtype": "int64"}]},
            row_count=10000,
            column_count=15,
            size_bytes=1024000,
            storage_uri="s3://bucket/datasets/data.parquet",
            storage_format="parquet",
            current_version_number=3,
            tags=["customers", "pii"],
            org_id="default",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            created_by="user123"
        )
        assert dataset.row_count == 10000
        assert dataset.storage_format == "parquet"
        assert dataset.current_version_number == 3

    def test_dataset_from_notebook(self):
        """Test dataset from notebook source."""
        dataset = Dataset(
            id=uuid4(),
            name="Notebook Output",
            source_type=DatasetSourceType.NOTEBOOK,
            source_id=uuid4(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        assert dataset.source_type == DatasetSourceType.NOTEBOOK
        assert dataset.source_id is not None

    def test_dataset_synthetic(self):
        """Test synthetic dataset."""
        dataset = Dataset(
            id=uuid4(),
            name="Synthetic Customers",
            source_type=DatasetSourceType.SYNTHETIC,
            source_id=uuid4(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        assert dataset.source_type == DatasetSourceType.SYNTHETIC


class TestDatasetVersionModels:
    """Test dataset version models."""

    def test_dataset_version(self):
        """Test dataset version model."""
        version = DatasetVersion(
            id=uuid4(),
            dataset_id=uuid4(),
            version_number=2,
            sha256="abc123def456789",
            storage_uri="s3://bucket/datasets/v2/data.parquet",
            storage_format="parquet",
            original_filename="sales_q2.csv",
            row_count=50000,
            column_count=12,
            size_bytes=2048000,
            data_schema={"columns": []},
            quality_profile={"completeness": 0.98},
            created_at=datetime.utcnow(),
            created_by="user123",
            notes="Added Q2 data"
        )
        assert version.version_number == 2
        assert version.original_filename == "sales_q2.csv"
        assert version.quality_profile["completeness"] == 0.98

    def test_dataset_version_list_response(self):
        """Test dataset version list response."""
        response = DatasetVersionListResponse(
            items=[],
            total=0
        )
        assert response.total == 0


class TestDatasetResponseModels:
    """Test dataset response models."""

    def test_upload_response(self):
        """Test dataset upload response."""
        dataset = Dataset(
            id=uuid4(),
            name="Uploaded Data",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        version = DatasetVersion(
            id=uuid4(),
            dataset_id=dataset.id,
            version_number=1,
            sha256="hash123",
            storage_uri="s3://bucket/data.parquet",
            storage_format="parquet",
            created_at=datetime.utcnow()
        )
        response = DatasetUploadResponse(
            dataset=dataset,
            version=version,
            message="Successfully uploaded data.csv (10,000 rows)"
        )
        assert "10,000" in response.message

    def test_list_response(self):
        """Test dataset list response."""
        response = DatasetListResponse(
            items=[],
            total=0,
            page=1,
            page_size=20
        )
        assert response.page == 1
        assert response.page_size == 20

    def test_preview_response(self):
        """Test dataset preview response."""
        response = DatasetPreviewResponse(
            columns=["id", "name", "price"],
            rows=[
                {"id": 1, "name": "Product A", "price": 10.99},
                {"id": 2, "name": "Product B", "price": 25.00}
            ],
            total_rows=1000,
            preview_rows=2
        )
        assert len(response.columns) == 3
        assert len(response.rows) == 2
        assert response.total_rows == 1000

    def test_download_response(self):
        """Test dataset download response."""
        response = DatasetDownloadResponse(
            download_url="https://bucket.s3.amazonaws.com/data.csv?signed=true",
            expires_in=3600,
            format="csv"
        )
        assert response.expires_in == 3600
        assert response.format == "csv"


class TestQualityProfile:
    """Test quality profile model."""

    def test_quality_profile(self):
        """Test quality profile model."""
        profile = QualityProfile(
            completeness=0.95,
            uniqueness={"id": 1.0, "email": 0.98, "name": 0.85},
            row_count=10000,
            column_count=15,
            null_counts={"email": 50, "phone": 200},
            duplicate_rows=25
        )
        assert profile.completeness == 0.95
        assert profile.uniqueness["id"] == 1.0
        assert profile.duplicate_rows == 25


class TestLegacyModels:
    """Test legacy models for backward compatibility."""

    def test_transform_model(self):
        """Test transform model."""
        transform = Transform(
            id=uuid4(),
            dataset_id=uuid4(),
            name="Normalize Prices",
            transform_type="normalize",
            config={"column": "price", "method": "min-max"},
            order=1,
            created_at=datetime.utcnow()
        )
        assert transform.transform_type == "normalize"
        assert transform.order == 1

    def test_synthetic_data_request(self):
        """Test synthetic data request."""
        request = SyntheticDataRequest(
            source_dataset_id=uuid4(),
            num_rows=5000,
            preserve_distribution=True,
            privacy_level="high",
            config={"seed": 42}
        )
        assert request.num_rows == 5000
        assert request.privacy_level == "high"

    def test_synthetic_data_request_defaults(self):
        """Test synthetic data request defaults."""
        request = SyntheticDataRequest(source_dataset_id=uuid4())
        assert request.num_rows == 1000
        assert request.preserve_distribution is True
        assert request.privacy_level == "high"

    def test_synthetic_data_result(self):
        """Test synthetic data result."""
        result = SyntheticDataResult(
            synthetic_dataset_id=uuid4(),
            source_dataset_id=uuid4(),
            num_rows=5000,
            quality_score=0.92,
            created_at=datetime.utcnow()
        )
        assert result.quality_score == 0.92


class TestRouterImports:
    """Test that router and services import correctly."""

    def test_router_imports(self):
        """Verify router can be imported."""
        from domains.datasets.router import router
        assert router is not None
        assert router.prefix == "/datasets"

    def test_db_models_imports(self):
        """Verify db models can be imported."""
        from domains.datasets.db_models import datasets, dataset_versions
        assert datasets is not None
        assert dataset_versions is not None

    def test_service_imports(self):
        """Verify service can be imported."""
        from domains.datasets.service import DatasetRegistry, TransformService
        assert DatasetRegistry is not None
        assert TransformService is not None

    def test_storage_imports(self):
        """Verify storage can be imported."""
        from domains.datasets.storage import get_dataset_storage, DatasetStorage
        assert get_dataset_storage is not None
        assert DatasetStorage is not None


class TestDatasetStatusTransitions:
    """Test dataset status transitions."""

    def test_active_to_archived(self):
        """Test transition from active to archived."""
        dataset = Dataset(
            id=uuid4(),
            name="Test Dataset",
            status=DatasetStatus.ACTIVE,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        # Update to archived
        update = DatasetUpdate(status=DatasetStatus.ARCHIVED)
        assert update.status == DatasetStatus.ARCHIVED

    def test_processing_to_active(self):
        """Test transition from processing to active."""
        dataset = Dataset(
            id=uuid4(),
            name="Processing Dataset",
            status=DatasetStatus.PROCESSING,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        update = DatasetUpdate(status=DatasetStatus.ACTIVE)
        assert update.status == DatasetStatus.ACTIVE

    def test_processing_to_error(self):
        """Test transition from processing to error."""
        dataset = Dataset(
            id=uuid4(),
            name="Failed Dataset",
            status=DatasetStatus.PROCESSING,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        update = DatasetUpdate(status=DatasetStatus.ERROR)
        assert update.status == DatasetStatus.ERROR


class TestDatasetVersioning:
    """Test dataset versioning logic."""

    def test_version_numbering(self):
        """Test version numbers increment correctly."""
        version1 = DatasetVersion(
            id=uuid4(),
            dataset_id=uuid4(),
            version_number=1,
            sha256="hash1",
            storage_uri="s3://bucket/v1/data.parquet",
            storage_format="parquet",
            created_at=datetime.utcnow()
        )
        version2 = DatasetVersion(
            id=uuid4(),
            dataset_id=version1.dataset_id,
            version_number=2,
            sha256="hash2",
            storage_uri="s3://bucket/v2/data.parquet",
            storage_format="parquet",
            created_at=datetime.utcnow()
        )
        assert version2.version_number == version1.version_number + 1

    def test_version_with_different_schema(self):
        """Test versions can have different schemas."""
        version1 = DatasetVersion(
            id=uuid4(),
            dataset_id=uuid4(),
            version_number=1,
            sha256="hash1",
            storage_uri="s3://bucket/v1/data.parquet",
            storage_format="parquet",
            data_schema={"columns": [{"name": "id", "dtype": "int64"}]},
            created_at=datetime.utcnow()
        )
        version2 = DatasetVersion(
            id=uuid4(),
            dataset_id=version1.dataset_id,
            version_number=2,
            sha256="hash2",
            storage_uri="s3://bucket/v2/data.parquet",
            storage_format="parquet",
            data_schema={"columns": [
                {"name": "id", "dtype": "int64"},
                {"name": "new_column", "dtype": "string"}
            ]},
            created_at=datetime.utcnow()
        )
        assert len(version2.data_schema["columns"]) > len(version1.data_schema["columns"])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
