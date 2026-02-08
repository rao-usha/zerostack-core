"""Tests for data_connections domain - connection management, scanning, and compatibility."""
import pytest
from uuid import uuid4
from datetime import datetime

from domains.data_connections.models import (
    ConnectionType, ConnectionStatus, ScanStatus, CompatibilityStatus,
    ColumnScan, QualityIssue, TableScanSummary, TableScanDetail,
    DataConnectionCreate, DataConnectionUpdate, DataConnectionResponse,
    DataConnectionListResponse, ScanRequest, ConnectionScanResponse,
    TableScanResponse, RequirementCheck, RecipeCompatibilityResponse,
    TableCompatibilityResponse
)


class TestConnectionEnums:
    """Test connection enum values."""

    def test_connection_types(self):
        """Test all connection types are available."""
        assert ConnectionType.POSTGRESQL.value == "postgresql"
        assert ConnectionType.MYSQL.value == "mysql"
        assert ConnectionType.SQLSERVER.value == "sqlserver"
        assert ConnectionType.SNOWFLAKE.value == "snowflake"
        assert ConnectionType.BIGQUERY.value == "bigquery"
        assert ConnectionType.S3.value == "s3"
        assert ConnectionType.FILE.value == "file"

    def test_connection_status(self):
        """Test connection status values."""
        assert ConnectionStatus.PENDING.value == "pending"
        assert ConnectionStatus.CONNECTED.value == "connected"
        assert ConnectionStatus.FAILED.value == "failed"
        assert ConnectionStatus.SCANNING.value == "scanning"

    def test_scan_status(self):
        """Test scan status values."""
        assert ScanStatus.NEVER.value == "never"
        assert ScanStatus.SCANNING.value == "scanning"
        assert ScanStatus.COMPLETED.value == "completed"
        assert ScanStatus.FAILED.value == "failed"

    def test_compatibility_status(self):
        """Test compatibility status values."""
        assert CompatibilityStatus.READY.value == "ready"
        assert CompatibilityStatus.PARTIAL.value == "partial"
        assert CompatibilityStatus.INCOMPATIBLE.value == "incompatible"


class TestColumnScanModels:
    """Test column scan models."""

    def test_column_scan_minimal(self):
        """Test column scan with minimal fields."""
        col = ColumnScan(name="id", data_type="integer")
        assert col.name == "id"
        assert col.data_type == "integer"
        assert col.nullable is True
        assert col.nulls_count == 0
        assert col.cardinality == 0

    def test_column_scan_full(self):
        """Test column scan with all fields."""
        col = ColumnScan(
            name="price",
            data_type="numeric",
            nullable=False,
            nulls_count=0,
            nulls_pct=0.0,
            cardinality=1500,
            min_value=0.99,
            max_value=999.99,
            mean_value=45.67,
            sample_values=[10.99, 25.00, 100.00],
            is_date=False,
            is_numeric=True,
            is_categorical=False,
            is_text=False,
            is_boolean=False
        )
        assert col.is_numeric is True
        assert col.min_value == 0.99
        assert col.mean_value == 45.67
        assert len(col.sample_values) == 3

    def test_column_scan_date_column(self):
        """Test date column detection."""
        col = ColumnScan(
            name="created_at",
            data_type="timestamp with time zone",
            is_date=True,
            min_value="2024-01-01",
            max_value="2024-12-31"
        )
        assert col.is_date is True
        assert col.is_numeric is False

    def test_column_scan_categorical(self):
        """Test categorical column."""
        col = ColumnScan(
            name="status",
            data_type="character varying",
            is_text=True,
            is_categorical=True,
            cardinality=5,
            sample_values=["active", "pending", "completed"]
        )
        assert col.is_categorical is True
        assert col.cardinality == 5


class TestQualityIssueModel:
    """Test quality issue model."""

    def test_quality_issue_warning(self):
        """Test quality issue warning."""
        issue = QualityIssue(
            severity="warning",
            issue_type="high_nulls",
            column="description",
            message="Column description has 65.2% null values",
            recommendation="Consider imputation or removal"
        )
        assert issue.severity == "warning"
        assert issue.issue_type == "high_nulls"
        assert issue.column == "description"

    def test_quality_issue_error(self):
        """Test quality issue error."""
        issue = QualityIssue(
            severity="error",
            issue_type="all_nulls",
            column="deprecated_field",
            message="Column has 100% null values"
        )
        assert issue.severity == "error"
        assert issue.recommendation is None


class TestTableScanModels:
    """Test table scan models."""

    def test_table_scan_summary(self):
        """Test table scan summary model."""
        summary = TableScanSummary(
            id=uuid4(),
            connection_id=uuid4(),
            schema_name="public",
            table_name="orders",
            full_name="public.orders",
            row_count=50000,
            column_count=12,
            date_column="order_date",
            date_span_days=365,
            completeness_score=0.95,
            scanned_at=datetime.utcnow()
        )
        assert summary.row_count == 50000
        assert summary.completeness_score == 0.95
        assert summary.date_span_days == 365

    def test_table_scan_summary_with_issues(self):
        """Test table scan summary with quality issues."""
        summary = TableScanSummary(
            id=uuid4(),
            connection_id=uuid4(),
            table_name="customers",
            full_name="public.customers",
            quality_issues=[
                QualityIssue(
                    severity="warning",
                    issue_type="low_cardinality",
                    column="status",
                    message="Low cardinality column"
                )
            ]
        )
        assert len(summary.quality_issues) == 1
        assert summary.quality_issues[0].issue_type == "low_cardinality"

    def test_table_scan_detail(self):
        """Test table scan detail model."""
        detail = TableScanDetail(
            id=uuid4(),
            connection_id=uuid4(),
            schema_name="analytics",
            table_name="events",
            full_name="analytics.events",
            row_count=1000000,
            column_count=8,
            size_bytes=104857600,
            columns=[
                ColumnScan(name="id", data_type="bigint", is_numeric=True),
                ColumnScan(name="event_type", data_type="varchar", is_text=True, is_categorical=True),
                ColumnScan(name="created_at", data_type="timestamp", is_date=True)
            ],
            date_column="created_at",
            date_min=datetime(2024, 1, 1),
            date_max=datetime(2024, 12, 31),
            date_span_days=365,
            completeness_score=0.98,
            sample_rows=[{"id": 1, "event_type": "click"}]
        )
        assert detail.row_count == 1000000
        assert len(detail.columns) == 3
        assert detail.size_bytes == 104857600


class TestDataConnectionModels:
    """Test data connection CRUD models."""

    def test_connection_create_minimal(self):
        """Test creating connection with minimal fields."""
        conn = DataConnectionCreate(
            name="My Database",
            connection_type=ConnectionType.POSTGRESQL
        )
        assert conn.name == "My Database"
        assert conn.connection_type == ConnectionType.POSTGRESQL
        assert conn.host is None

    def test_connection_create_full(self):
        """Test creating connection with all fields."""
        conn = DataConnectionCreate(
            name="Production PostgreSQL",
            description="Main production database",
            connection_type=ConnectionType.POSTGRESQL,
            host="db.example.com",
            port=5432,
            database="production",
            username="app_user",
            password="secret123",
            extra_config={"ssl": True, "pool_size": 10}
        )
        assert conn.host == "db.example.com"
        assert conn.port == 5432
        assert conn.extra_config["ssl"] is True

    def test_connection_update_partial(self):
        """Test partial connection update."""
        update = DataConnectionUpdate(name="Updated Name")
        assert update.name == "Updated Name"
        assert update.host is None
        assert update.password is None

    def test_connection_response(self):
        """Test connection response model."""
        response = DataConnectionResponse(
            id=uuid4(),
            name="Test Connection",
            connection_type="postgresql",
            host="localhost",
            port=5432,
            database="testdb",
            username="test_user",
            status="connected",
            last_connected_at=datetime.utcnow(),
            last_scan_at=datetime.utcnow(),
            scan_status="completed",
            tables_count=25,
            total_rows=100000,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        assert response.status == "connected"
        assert response.tables_count == 25
        assert response.total_rows == 100000

    def test_connection_list_response(self):
        """Test connection list response."""
        response = DataConnectionListResponse(connections=[], total=0)
        assert response.total == 0


class TestScanModels:
    """Test scan request/response models."""

    def test_scan_request_defaults(self):
        """Test scan request default values."""
        request = ScanRequest()
        assert request.full_scan is False
        assert request.sample_size == 1000
        assert request.include_sample_data is True

    def test_scan_request_custom(self):
        """Test scan request with custom values."""
        request = ScanRequest(
            full_scan=True,
            sample_size=5000,
            include_sample_data=False
        )
        assert request.full_scan is True
        assert request.sample_size == 5000

    def test_connection_scan_response(self):
        """Test connection scan response."""
        response = ConnectionScanResponse(
            connection_id=uuid4(),
            tables_found=15,
            tables_scanned=15,
            total_rows=500000,
            scan_duration_seconds=12.5,
            tables=[]
        )
        assert response.tables_found == 15
        assert response.scan_duration_seconds == 12.5

    def test_table_scan_response(self):
        """Test table scan response."""
        detail = TableScanDetail(
            id=uuid4(),
            connection_id=uuid4(),
            table_name="test",
            full_name="public.test"
        )
        response = TableScanResponse(
            table=detail,
            scan_duration_seconds=2.3
        )
        assert response.scan_duration_seconds == 2.3


class TestRecipeCompatibilityModels:
    """Test recipe compatibility models."""

    def test_requirement_check_met(self):
        """Test requirement check - met."""
        check = RequirementCheck(
            requirement="date_column",
            status="met",
            column="created_at",
            notes="Valid timestamp column"
        )
        assert check.status == "met"
        assert check.column == "created_at"

    def test_requirement_check_missing(self):
        """Test requirement check - missing."""
        check = RequirementCheck(
            requirement="target_numeric",
            status="missing",
            notes="No numeric columns found"
        )
        assert check.status == "missing"
        assert check.column is None

    def test_requirement_check_partial(self):
        """Test requirement check - partial."""
        check = RequirementCheck(
            requirement="sufficient_history",
            status="partial",
            column="order_date",
            notes="Only 45 days of history (need 90+)"
        )
        assert check.status == "partial"

    def test_recipe_compatibility_response(self):
        """Test recipe compatibility response."""
        response = RecipeCompatibilityResponse(
            table_scan_id=uuid4(),
            recipe_id="recipe_forecasting_base",
            recipe_name="M5 Sales Forecasting",
            compatibility_score=85.5,
            status="partial",
            requirements_met=[
                RequirementCheck(requirement="date_column", status="met", column="date"),
                RequirementCheck(requirement="sufficient_rows", status="met", notes="50000 rows")
            ],
            requirements_missing=[],
            requirements_partial=[
                RequirementCheck(requirement="target_numeric", status="partial", column="value")
            ],
            recommendations=["Consider cleaning null values in target column"],
            can_run=True,
            estimated_quality="good"
        )
        assert response.compatibility_score == 85.5
        assert response.can_run is True
        assert len(response.requirements_met) == 2

    def test_table_compatibility_response(self):
        """Test table compatibility response."""
        response = TableCompatibilityResponse(
            table_scan_id=uuid4(),
            table_name="public.sales",
            recipes=[
                RecipeCompatibilityResponse(
                    table_scan_id=uuid4(),
                    recipe_id="recipe_forecasting_base",
                    recipe_name="M5 Sales Forecasting",
                    compatibility_score=90.0,
                    status="ready",
                    requirements_met=[],
                    requirements_missing=[],
                    requirements_partial=[],
                    recommendations=[],
                    can_run=True,
                    estimated_quality="excellent"
                )
            ]
        )
        assert len(response.recipes) == 1
        assert response.recipes[0].status == "ready"


class TestRouterImports:
    """Test that router and services import correctly."""

    def test_router_imports(self):
        """Verify router can be imported."""
        from domains.data_connections.router import router
        assert router is not None
        assert router.prefix == "/data-connections"

    def test_db_models_imports(self):
        """Verify db models can be imported."""
        from domains.data_connections.db_models import (
            data_connections, table_scans, recipe_compatibility
        )
        assert data_connections is not None
        assert table_scans is not None
        assert recipe_compatibility is not None

    def test_scanner_imports(self):
        """Verify scanner can be imported."""
        from domains.data_connections.scanner import DataScanner
        assert DataScanner is not None

    def test_compatibility_imports(self):
        """Verify compatibility checker can be imported."""
        from domains.data_connections.compatibility import (
            RecipeCompatibilityChecker, RECIPE_REQUIREMENTS
        )
        assert RecipeCompatibilityChecker is not None
        assert RECIPE_REQUIREMENTS is not None
        assert "recipe_forecasting_base" in RECIPE_REQUIREMENTS


class TestRecipeRequirements:
    """Test recipe requirement definitions."""

    def test_forecasting_recipe_exists(self):
        """Test forecasting recipe is defined."""
        from domains.data_connections.compatibility import RECIPE_REQUIREMENTS
        recipe = RECIPE_REQUIREMENTS.get("recipe_forecasting_base")
        assert recipe is not None
        assert recipe["name"] == "M5 Sales Forecasting"
        assert len(recipe["requirements"]) > 0

    def test_classification_recipe_exists(self):
        """Test classification recipe is defined."""
        from domains.data_connections.compatibility import RECIPE_REQUIREMENTS
        recipe = RECIPE_REQUIREMENTS.get("recipe_classification_base")
        assert recipe is not None
        assert recipe["name"] == "Classification Model"

    def test_anomaly_detection_recipe_exists(self):
        """Test anomaly detection recipe is defined."""
        from domains.data_connections.compatibility import RECIPE_REQUIREMENTS
        recipe = RECIPE_REQUIREMENTS.get("recipe_anomaly_detection")
        assert recipe is not None
        assert recipe["name"] == "Anomaly Detection"

    def test_recipe_has_required_fields(self):
        """Test recipes have required structure."""
        from domains.data_connections.compatibility import RECIPE_REQUIREMENTS
        for recipe_id, recipe in RECIPE_REQUIREMENTS.items():
            assert "name" in recipe
            assert "description" in recipe
            assert "requirements" in recipe
            assert "min_compatibility_score" in recipe
            for req in recipe["requirements"]:
                assert "id" in req
                assert "name" in req
                assert "type" in req
                assert "required" in req


class TestCompatibilityCheckerLogic:
    """Test compatibility checker logic without database."""

    def test_get_available_recipes(self):
        """Test getting available recipes list."""
        from domains.data_connections.compatibility import RecipeCompatibilityChecker
        checker = RecipeCompatibilityChecker(None)
        recipes = checker.get_available_recipes()
        assert len(recipes) >= 3
        for recipe in recipes:
            assert "id" in recipe
            assert "name" in recipe
            assert "description" in recipe
            assert "requirements_count" in recipe
            assert "required_count" in recipe

    def test_requirement_check_types(self):
        """Test various requirement check type handling."""
        from domains.data_connections.compatibility import RecipeCompatibilityChecker

        # Create a mock table scan detail
        detail = TableScanDetail(
            id=uuid4(),
            connection_id=uuid4(),
            table_name="test_table",
            full_name="public.test_table",
            row_count=5000,
            column_count=8,
            date_column="created_at",
            date_span_days=120,
            columns=[
                ColumnScan(name="id", data_type="integer", is_numeric=True, cardinality=5000),
                ColumnScan(name="value", data_type="numeric", is_numeric=True, cardinality=1000),
                ColumnScan(name="created_at", data_type="timestamp", is_date=True),
                ColumnScan(name="category", data_type="varchar", is_text=True, is_categorical=True, cardinality=10)
            ]
        )

        checker = RecipeCompatibilityChecker(None)

        # Test date requirement
        date_req = {"id": "date_column", "type": "date", "required": True, "match_patterns": ["date", "time"]}
        result = checker._check_requirement(date_req, detail)
        assert result.status == "met"
        assert result.column == "created_at"

        # Test row count requirement
        row_req = {"id": "sufficient_rows", "type": "row_count", "required": True, "min_rows": 1000}
        result = checker._check_requirement(row_req, detail)
        assert result.status == "met"

        # Test row count - insufficient
        row_req_high = {"id": "sufficient_rows", "type": "row_count", "required": True, "min_rows": 10000}
        result = checker._check_requirement(row_req_high, detail)
        assert result.status == "partial"

        # Test date range
        date_range_req = {"id": "history", "type": "date_range", "required": True, "min_days": 90}
        result = checker._check_requirement(date_range_req, detail)
        assert result.status == "met"

        # Test min numeric columns
        numeric_req = {"id": "numeric_cols", "type": "min_numeric", "required": True, "min_count": 2}
        result = checker._check_requirement(numeric_req, detail)
        assert result.status == "met"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
