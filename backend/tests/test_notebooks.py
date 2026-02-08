"""Tests for notebooks domain - notebook management, cell execution, and datasets."""
import pytest
from uuid import uuid4
from datetime import datetime

from domains.notebooks.models import (
    CellType, RunStatus,
    CellCreate, CellUpdate, CellResponse, CellExecuteRequest, CellExecuteResponse,
    PythonExecuteRequest, PythonExecuteResponse, PythonOutput, VariableInfo,
    SessionVariablesResponse,
    NotebookCreate, NotebookUpdate, NotebookResponse, NotebookDetailResponse,
    NotebookListResponse,
    DatasetCreate, DatasetResponse, DatasetListResponse
)


class TestCellModels:
    """Test cell Pydantic models."""

    def test_cell_types(self):
        """Test cell type enum values."""
        assert CellType.SQL.value == "sql"
        assert CellType.PYTHON.value == "python"
        assert CellType.MARKDOWN.value == "markdown"

    def test_run_status(self):
        """Test run status enum values."""
        assert RunStatus.SUCCESS.value == "success"
        assert RunStatus.ERROR.value == "error"
        assert RunStatus.RUNNING.value == "running"

    def test_cell_create_minimal(self):
        """Test creating a cell with minimal fields."""
        cell = CellCreate(content="SELECT * FROM users")
        assert cell.content == "SELECT * FROM users"
        assert cell.cell_type == CellType.SQL
        assert cell.position is None

    def test_cell_create_full(self):
        """Test creating a cell with all fields."""
        conn_id = uuid4()
        cell = CellCreate(
            cell_type=CellType.PYTHON,
            content="import pandas as pd\ndf = pd.read_csv('data.csv')",
            position=5,
            connection_id=conn_id,
            settings={"timeout": 120}
        )
        assert cell.cell_type == CellType.PYTHON
        assert cell.position == 5
        assert cell.connection_id == conn_id
        assert cell.settings["timeout"] == 120

    def test_cell_update_partial(self):
        """Test partial cell update."""
        update = CellUpdate(content="SELECT id FROM users")
        assert update.content == "SELECT id FROM users"
        assert update.position is None

    def test_cell_response(self):
        """Test cell response model."""
        cell = CellResponse(
            id=uuid4(),
            notebook_id=uuid4(),
            cell_type="sql",
            content="SELECT * FROM orders",
            position=0,
            last_run_at=datetime.utcnow(),
            last_run_duration_ms=150,
            last_run_status="success",
            last_run_row_count=1000,
            cached_results=[{"id": 1, "name": "Test"}],
            settings={},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        assert cell.last_run_status == "success"
        assert cell.last_run_row_count == 1000

    def test_cell_execute_request(self):
        """Test cell execute request with limits."""
        request = CellExecuteRequest(limit=500, timeout_seconds=30)
        assert request.limit == 500
        assert request.timeout_seconds == 30

    def test_cell_execute_response(self):
        """Test cell execute response."""
        response = CellExecuteResponse(
            cell_id=uuid4(),
            status="success",
            duration_ms=250,
            row_count=100,
            columns=[{"name": "id", "type": "integer"}, {"name": "name", "type": "string"}],
            rows=[{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}],
            truncated=False
        )
        assert response.status == "success"
        assert len(response.columns) == 2
        assert len(response.rows) == 2


class TestPythonExecutionModels:
    """Test Python execution models."""

    def test_python_execute_request(self):
        """Test Python execute request."""
        request = PythonExecuteRequest(timeout_seconds=120)
        assert request.timeout_seconds == 120

    def test_python_output_text(self):
        """Test Python text output."""
        output = PythonOutput(
            type="text",
            data="Hello, World!"
        )
        assert output.type == "text"
        assert output.data == "Hello, World!"

    def test_python_output_dataframe(self):
        """Test Python dataframe output."""
        output = PythonOutput(
            type="dataframe",
            data=[{"a": 1, "b": 2}],
            name="df",
            columns=["a", "b"],
            shape=[100, 2],
            truncated=True
        )
        assert output.type == "dataframe"
        assert output.shape == [100, 2]
        assert output.truncated is True

    def test_python_output_image(self):
        """Test Python image output."""
        output = PythonOutput(
            type="image",
            data="base64encodeddata...",
            format="png"
        )
        assert output.type == "image"
        assert output.format == "png"

    def test_python_execute_response_success(self):
        """Test Python execute response on success."""
        response = PythonExecuteResponse(
            cell_id=uuid4(),
            status="success",
            duration_ms=500,
            stdout="Processing...\nDone!",
            stderr="",
            result=42,
            outputs=[{"type": "text", "data": "Result: 42"}],
            variables=["x", "y", "df"]
        )
        assert response.status == "success"
        assert response.result == 42
        assert "x" in response.variables

    def test_python_execute_response_error(self):
        """Test Python execute response on error."""
        response = PythonExecuteResponse(
            cell_id=uuid4(),
            status="error",
            duration_ms=100,
            stdout="",
            stderr="NameError: name 'undefined' is not defined",
            error="NameError",
            traceback="Traceback (most recent call last):\n  ..."
        )
        assert response.status == "error"
        assert response.error == "NameError"

    def test_variable_info(self):
        """Test variable info model."""
        var = VariableInfo(
            name="df",
            type="DataFrame",
            preview="<DataFrame 100x5>",
            shape=[100, 5]
        )
        assert var.name == "df"
        assert var.type == "DataFrame"

    def test_session_variables_response(self):
        """Test session variables response."""
        response = SessionVariablesResponse(
            notebook_id=uuid4(),
            variables=[
                VariableInfo(name="x", type="int", preview="42"),
                VariableInfo(name="df", type="DataFrame", preview="<100x5>", shape=[100, 5])
            ]
        )
        assert len(response.variables) == 2


class TestNotebookModels:
    """Test notebook Pydantic models."""

    def test_notebook_create_minimal(self):
        """Test creating a notebook with minimal fields."""
        notebook = NotebookCreate(name="My Analysis")
        assert notebook.name == "My Analysis"
        assert notebook.description is None
        assert notebook.folder == ""
        assert notebook.tags == []

    def test_notebook_create_full(self):
        """Test creating a notebook with all fields."""
        conn_id = uuid4()
        notebook = NotebookCreate(
            name="Sales Analysis Q4",
            description="Quarterly sales analysis notebook",
            folder="reports/sales",
            tags=["sales", "quarterly", "analysis"],
            default_connection_id=conn_id
        )
        assert notebook.name == "Sales Analysis Q4"
        assert notebook.folder == "reports/sales"
        assert "sales" in notebook.tags
        assert notebook.default_connection_id == conn_id

    def test_notebook_update_partial(self):
        """Test partial notebook update."""
        update = NotebookUpdate(name="Updated Name")
        assert update.name == "Updated Name"
        assert update.description is None
        assert update.folder is None

    def test_notebook_response(self):
        """Test notebook response model."""
        response = NotebookResponse(
            id=uuid4(),
            name="Test Notebook",
            folder="test",
            tags=["test"],
            cell_count=5,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        assert response.cell_count == 5

    def test_notebook_detail_response(self):
        """Test notebook detail response with cells."""
        notebook_id = uuid4()
        response = NotebookDetailResponse(
            id=notebook_id,
            name="Test Notebook",
            folder="",
            tags=[],
            cells=[
                CellResponse(
                    id=uuid4(),
                    notebook_id=notebook_id,
                    cell_type="sql",
                    content="SELECT 1",
                    position=0,
                    settings={},
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
            ],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        assert len(response.cells) == 1

    def test_notebook_list_response(self):
        """Test notebook list response."""
        response = NotebookListResponse(notebooks=[], total=0)
        assert response.total == 0


class TestDatasetModels:
    """Test dataset models for saving cell results."""

    def test_dataset_create(self):
        """Test dataset create model."""
        dataset = DatasetCreate(
            name="customer_segments",
            description="Customer segmentation results",
            format="parquet"
        )
        assert dataset.name == "customer_segments"
        assert dataset.format == "parquet"

    def test_dataset_create_csv(self):
        """Test dataset create with CSV format."""
        dataset = DatasetCreate(name="export", format="csv")
        assert dataset.format == "csv"

    def test_dataset_response(self):
        """Test dataset response model."""
        response = DatasetResponse(
            id=uuid4(),
            name="results",
            source_notebook_id=uuid4(),
            source_cell_id=uuid4(),
            source_query="SELECT * FROM analysis",
            storage_uri="s3://bucket/datasets/results.parquet",
            storage_format="parquet",
            row_count=10000,
            column_count=15,
            size_bytes=1024000,
            columns=[{"name": "id", "type": "int64"}, {"name": "value", "type": "float64"}],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        assert response.row_count == 10000
        assert response.storage_format == "parquet"

    def test_dataset_list_response(self):
        """Test dataset list response."""
        response = DatasetListResponse(datasets=[], total=0)
        assert response.total == 0


class TestRouterImports:
    """Test that notebook router and services import correctly."""

    def test_router_imports(self):
        """Verify router can be imported."""
        from domains.notebooks.router import router
        assert router is not None
        assert router.prefix == "/notebooks"

    def test_db_models_imports(self):
        """Verify db models can be imported."""
        from domains.notebooks.db_models import notebooks, notebook_cells
        assert notebooks is not None
        assert notebook_cells is not None

    def test_executor_imports(self):
        """Verify executor can be imported."""
        from domains.notebooks.executor import SQLExecutor
        assert SQLExecutor is not None

    def test_python_executor_imports(self):
        """Verify Python executor can be imported."""
        from domains.notebooks.python_executor import PythonExecutor
        assert PythonExecutor is not None

    def test_dataset_exporter_imports(self):
        """Verify dataset exporter can be imported."""
        from domains.notebooks.dataset_exporter import DatasetExporter
        assert DatasetExporter is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
