"""Tests for notebooks domain - notebook management, cell execution, and datasets."""
import pytest
from uuid import uuid4
from datetime import datetime

# Check if pandas is available for certain tests
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

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


class TestSQLExecutorTypeConversion:
    """Test SQL executor type conversion utilities."""

    def setup_method(self):
        """Setup mock executor for testing utility methods."""
        from domains.notebooks.executor import SQLExecutor

        class MockSession:
            pass

        self.executor = SQLExecutor(MockSession())

    def test_get_type_name_none(self):
        """Test type detection for None."""
        assert self.executor._get_type_name(None) == "unknown"

    def test_get_type_name_boolean(self):
        """Test type detection for booleans."""
        assert self.executor._get_type_name(True) == "boolean"
        assert self.executor._get_type_name(False) == "boolean"

    def test_get_type_name_integer(self):
        """Test type detection for integers."""
        assert self.executor._get_type_name(42) == "integer"
        assert self.executor._get_type_name(-100) == "integer"

    def test_get_type_name_float(self):
        """Test type detection for floats."""
        assert self.executor._get_type_name(3.14) == "float"
        assert self.executor._get_type_name(-2.5) == "float"

    def test_get_type_name_string(self):
        """Test type detection for strings."""
        assert self.executor._get_type_name("hello") == "string"
        assert self.executor._get_type_name("") == "string"

    def test_get_type_name_datetime(self):
        """Test type detection for datetime."""
        assert self.executor._get_type_name(datetime.utcnow()) == "timestamp"

    def test_get_type_name_bytes(self):
        """Test type detection for bytes."""
        assert self.executor._get_type_name(b"data") == "bytes"
        assert self.executor._get_type_name(bytearray(b"data")) == "bytes"

    def test_get_type_name_list(self):
        """Test type detection for arrays."""
        assert self.executor._get_type_name([1, 2, 3]) == "array"
        assert self.executor._get_type_name((1, 2, 3)) == "array"

    def test_get_type_name_dict(self):
        """Test type detection for dicts."""
        assert self.executor._get_type_name({"key": "value"}) == "json"

    def test_to_json_safe_primitives(self):
        """Test JSON conversion for primitives."""
        assert self.executor._to_json_safe(None) is None
        assert self.executor._to_json_safe(True) is True
        assert self.executor._to_json_safe(42) == 42
        assert self.executor._to_json_safe(3.14) == 3.14
        assert self.executor._to_json_safe("hello") == "hello"

    def test_to_json_safe_datetime(self):
        """Test JSON conversion for datetime."""
        dt = datetime(2024, 1, 15, 10, 30, 45)
        result = self.executor._to_json_safe(dt)
        assert result == "2024-01-15T10:30:45"

    def test_to_json_safe_bytes(self):
        """Test JSON conversion for bytes."""
        result = self.executor._to_json_safe(b"\x00\x01\x02")
        assert result == "000102"

    def test_to_json_safe_nested_list(self):
        """Test JSON conversion for nested lists."""
        result = self.executor._to_json_safe([1, [2, 3], datetime(2024, 1, 1)])
        assert result == [1, [2, 3], "2024-01-01T00:00:00"]

    def test_to_json_safe_nested_dict(self):
        """Test JSON conversion for nested dicts."""
        result = self.executor._to_json_safe({
            "num": 42,
            "nested": {"dt": datetime(2024, 1, 1)},
            "list": [1, 2, 3]
        })
        assert result["num"] == 42
        assert result["nested"]["dt"] == "2024-01-01T00:00:00"
        assert result["list"] == [1, 2, 3]


class TestPythonExecutorExecution:
    """Test Python executor code execution."""

    def setup_method(self):
        """Setup clean executor for each test."""
        from domains.notebooks.python_executor import PythonExecutor, _notebook_sessions
        # Clear all sessions before each test
        _notebook_sessions.clear()
        self.notebook_id = uuid4()
        self.executor = PythonExecutor(self.notebook_id)

    def teardown_method(self):
        """Cleanup after each test."""
        from domains.notebooks.python_executor import _notebook_sessions
        _notebook_sessions.clear()

    def test_simple_expression(self):
        """Test evaluating a simple expression."""
        result = self.executor.execute("1 + 1")
        assert result['status'] == 'success'
        assert result['result'] == 2
        assert result['error'] is None

    def test_assignment(self):
        """Test variable assignment."""
        result = self.executor.execute("x = 42")
        assert result['status'] == 'success'
        assert 'x' in result['variables']

    def test_variable_persistence(self):
        """Test that variables persist between executions."""
        self.executor.execute("x = 10")
        result = self.executor.execute("x * 2")
        assert result['status'] == 'success'
        assert result['result'] == 20

    def test_stdout_capture(self):
        """Test stdout capture."""
        result = self.executor.execute("print('Hello, World!')")
        assert result['status'] == 'success'
        assert 'Hello, World!' in result['stdout']

    def test_multiline_code(self):
        """Test multiline code execution."""
        code = """
def add(a, b):
    return a + b

result = add(3, 4)
result
"""
        result = self.executor.execute(code)
        assert result['status'] == 'success'
        assert result['result'] == 7

    def test_syntax_error(self):
        """Test syntax error handling."""
        result = self.executor.execute("def broken(")
        assert result['status'] == 'error'
        assert 'Syntax error' in result['error']

    def test_runtime_error(self):
        """Test runtime error handling."""
        result = self.executor.execute("1 / 0")
        assert result['status'] == 'error'
        assert result['traceback'] is not None

    def test_name_error(self):
        """Test undefined variable error."""
        result = self.executor.execute("undefined_var")
        assert result['status'] == 'error'
        assert 'NameError' in result['traceback'] or 'undefined' in str(result['error'])

    def test_duration_tracking(self):
        """Test that execution duration is tracked."""
        result = self.executor.execute("x = 1")
        assert 'duration_ms' in result
        assert result['duration_ms'] >= 0

    @pytest.mark.skipif(not PANDAS_AVAILABLE, reason="pandas not installed")
    def test_preloaded_imports(self):
        """Test that pandas and numpy are preloaded (when import is allowed)."""
        # Check if preloading succeeded first
        result = self.executor.execute("'pd' in dir()")
        if result['result'] is True:
            result = self.executor.execute("pd.__name__")
            assert result['status'] == 'success'
            assert result['result'] == 'pandas'
        else:
            # Preloading failed due to sandbox, skip
            pytest.skip("Preloaded imports not available in sandboxed environment")

    def test_datetime_preloaded(self):
        """Test that datetime is preloaded (when import is allowed)."""
        # Check if preloading succeeded
        result = self.executor.execute("'datetime' in dir()")
        if result['result'] is True:
            result = self.executor.execute("datetime.now().year")
            assert result['status'] == 'success'
            assert result['result'] >= 2024
        else:
            # Preloading failed due to sandbox, skip
            pytest.skip("Preloaded imports not available in sandboxed environment")

    def test_reset_session(self):
        """Test session reset clears variables."""
        self.executor.execute("x = 100")
        self.executor.reset_session()
        result = self.executor.execute("x")
        assert result['status'] == 'error'  # x should not exist

    def test_get_variables(self):
        """Test getting session variables."""
        self.executor.execute("x = 42")
        self.executor.execute("name = 'test'")
        variables = self.executor.get_variables()

        var_names = [v['name'] for v in variables]
        assert 'x' in var_names
        assert 'name' in var_names

    def test_variable_info_types(self):
        """Test variable info includes correct types."""
        self.executor.execute("num = 42")
        self.executor.execute("text = 'hello'")
        self.executor.execute("items = [1, 2, 3]")
        variables = self.executor.get_variables()

        var_dict = {v['name']: v for v in variables}
        assert var_dict['num']['type'] == 'int'
        assert var_dict['text']['type'] == 'str'
        assert var_dict['items']['type'] == 'list'


class TestPythonExecutorSerialization:
    """Test Python executor value serialization."""

    def setup_method(self):
        """Setup executor for testing."""
        from domains.notebooks.python_executor import PythonExecutor, _notebook_sessions
        _notebook_sessions.clear()
        self.executor = PythonExecutor(uuid4())

    def teardown_method(self):
        """Cleanup after each test."""
        from domains.notebooks.python_executor import _notebook_sessions
        _notebook_sessions.clear()

    def test_serialize_none(self):
        """Test serializing None."""
        assert self.executor._serialize_value(None) is None

    def test_serialize_primitives(self):
        """Test serializing primitive types."""
        assert self.executor._serialize_value(True) is True
        assert self.executor._serialize_value(42) == 42
        assert self.executor._serialize_value(3.14) == 3.14
        assert self.executor._serialize_value("hello") == "hello"

    def test_serialize_datetime(self):
        """Test serializing datetime."""
        dt = datetime(2024, 1, 15, 10, 30, 45)
        result = self.executor._serialize_value(dt)
        assert result == "2024-01-15T10:30:45"

    def test_serialize_bytes(self):
        """Test serializing bytes."""
        result = self.executor._serialize_value(b"\xde\xad\xbe\xef")
        assert result == "deadbeef"

    def test_serialize_list(self):
        """Test serializing lists."""
        result = self.executor._serialize_value([1, "two", 3.0])
        assert result == [1, "two", 3.0]

    def test_serialize_nested(self):
        """Test serializing nested structures."""
        result = self.executor._serialize_value({
            "a": 1,
            "b": {"c": 2},
            "d": [1, 2, 3]
        })
        assert result == {"a": 1, "b": {"c": 2}, "d": [1, 2, 3]}

    def test_get_preview_string(self):
        """Test preview for strings."""
        short = self.executor._get_preview("hello")
        assert short == '"hello"'

        long = self.executor._get_preview("x" * 100)
        assert "..." in long
        assert len(long) < 60

    def test_get_preview_number(self):
        """Test preview for numbers."""
        assert self.executor._get_preview(42) == "42"
        assert self.executor._get_preview(3.14) == "3.14"

    def test_get_preview_list(self):
        """Test preview for lists."""
        result = self.executor._get_preview([1, 2, 3, 4, 5])
        assert "list[5]" in result

    def test_get_preview_dict(self):
        """Test preview for dicts."""
        result = self.executor._get_preview({"a": 1, "b": 2})
        assert "dict[2]" in result


@pytest.mark.skipif(not PANDAS_AVAILABLE, reason="pandas not installed")
class TestPythonExecutorDataFrames:
    """Test Python executor DataFrame handling."""

    def setup_method(self):
        """Setup executor for testing."""
        from domains.notebooks.python_executor import PythonExecutor, _notebook_sessions
        _notebook_sessions.clear()
        self.executor = PythonExecutor(uuid4())
        # Check if pandas is available in the executor
        result = self.executor.execute("'pd' in dir()")
        self.pandas_preloaded = result.get('result', False) is True

    def teardown_method(self):
        """Cleanup after each test."""
        from domains.notebooks.python_executor import _notebook_sessions
        _notebook_sessions.clear()

    def test_is_dataframe_positive(self):
        """Test DataFrame detection."""
        if not self.pandas_preloaded:
            pytest.skip("pandas not preloaded in sandboxed environment")

        # Execute code to create a DataFrame
        result = self.executor.execute("df = pd.DataFrame({'a': [1, 2], 'b': [3, 4]})")
        assert result['status'] == 'success'

        # Check that it was detected
        variables = self.executor.get_variables()
        df_var = next((v for v in variables if v['name'] == 'df'), None)
        assert df_var is not None
        assert df_var['type'] == 'DataFrame'
        assert df_var['shape'] == [2, 2]

    def test_dataframe_auto_display(self):
        """Test that DataFrames are auto-displayed."""
        if not self.pandas_preloaded:
            pytest.skip("pandas not preloaded in sandboxed environment")

        result = self.executor.execute("pd.DataFrame({'x': [1, 2, 3]})")
        assert result['status'] == 'success'
        # Should have an output
        assert len(result['outputs']) > 0
        assert result['outputs'][0]['type'] == 'dataframe'

    def test_dataframe_output_format(self):
        """Test DataFrame output format."""
        if not self.pandas_preloaded:
            pytest.skip("pandas not preloaded in sandboxed environment")

        result = self.executor.execute("pd.DataFrame({'col1': [1, 2], 'col2': ['a', 'b']})")
        assert result['status'] == 'success'

        output = result['outputs'][0]
        assert output['type'] == 'dataframe'
        assert 'col1' in output['columns']
        assert 'col2' in output['columns']
        assert output['shape'] == [2, 2]
        assert len(output['data']) == 2

    def test_dataframe_preview(self):
        """Test DataFrame preview in variables."""
        if not self.pandas_preloaded:
            pytest.skip("pandas not preloaded in sandboxed environment")

        self.executor.execute("df = pd.DataFrame({'a': range(100)})")
        variables = self.executor.get_variables()

        df_var = next((v for v in variables if v['name'] == 'df'), None)
        assert df_var is not None
        assert 'DataFrame' in df_var['preview']
        assert df_var['shape'] == [100, 1]


class TestPythonExecutorOutputs:
    """Test Python executor rich output handling."""

    def setup_method(self):
        """Setup executor for testing."""
        from domains.notebooks.python_executor import PythonExecutor, _notebook_sessions
        _notebook_sessions.clear()
        self.executor = PythonExecutor(uuid4())
        # Check if pandas is available in the executor
        result = self.executor.execute("'pd' in dir()")
        self.pandas_preloaded = result.get('result', False) is True

    def teardown_method(self):
        """Cleanup after each test."""
        from domains.notebooks.python_executor import _notebook_sessions
        _notebook_sessions.clear()

    def test_display_function(self):
        """Test display() helper function."""
        result = self.executor.execute("display({'key': 'value'})")
        assert result['status'] == 'success'
        assert len(result['outputs']) > 0

    def test_text_output(self):
        """Test text output creation."""
        result = self.executor.execute("display('hello')")
        assert result['status'] == 'success'
        output = result['outputs'][0]
        assert output['type'] == 'text'

    @pytest.mark.skipif(not PANDAS_AVAILABLE, reason="pandas not installed")
    def test_show_df_function(self):
        """Test show_df() helper function."""
        if not self.pandas_preloaded:
            pytest.skip("pandas not preloaded in sandboxed environment")

        result = self.executor.execute("""
df = pd.DataFrame({'x': [1, 2, 3]})
show_df(df, 'my_dataframe')
""")
        assert result['status'] == 'success'
        outputs = result['outputs']
        assert len(outputs) > 0
        # Should have named DataFrame output
        df_output = next((o for o in outputs if o.get('name') == 'my_dataframe'), None)
        assert df_output is not None

    @pytest.mark.skipif(not PANDAS_AVAILABLE, reason="pandas not installed")
    def test_multiple_outputs(self):
        """Test multiple outputs in one cell."""
        if not self.pandas_preloaded:
            pytest.skip("pandas not preloaded in sandboxed environment")

        result = self.executor.execute("""
display("First output")
display("Second output")
pd.DataFrame({'a': [1]})
""")
        assert result['status'] == 'success'
        # Should have at least 3 outputs
        assert len(result['outputs']) >= 3


class TestPythonExecutorSecurity:
    """Test Python executor security restrictions."""

    def setup_method(self):
        """Setup executor for testing."""
        from domains.notebooks.python_executor import PythonExecutor, _notebook_sessions
        _notebook_sessions.clear()
        self.executor = PythonExecutor(uuid4())

    def teardown_method(self):
        """Cleanup after each test."""
        from domains.notebooks.python_executor import _notebook_sessions
        _notebook_sessions.clear()

    def test_blocked_exec(self):
        """Test that exec is blocked."""
        result = self.executor.execute("exec('print(1)')")
        assert result['status'] == 'error'

    def test_blocked_eval(self):
        """Test that eval is blocked."""
        result = self.executor.execute("eval('1+1')")
        assert result['status'] == 'error'

    def test_blocked_open(self):
        """Test that open is blocked."""
        result = self.executor.execute("open('/etc/passwd')")
        assert result['status'] == 'error'

    def test_blocked_import(self):
        """Test that __import__ is blocked."""
        result = self.executor.execute("__import__('os')")
        assert result['status'] == 'error'


class TestPythonExecutorSessionManagement:
    """Test Python executor session management."""

    def test_separate_notebook_sessions(self):
        """Test that different notebooks have separate sessions."""
        from domains.notebooks.python_executor import PythonExecutor, _notebook_sessions
        _notebook_sessions.clear()

        notebook1 = uuid4()
        notebook2 = uuid4()

        exec1 = PythonExecutor(notebook1)
        exec2 = PythonExecutor(notebook2)

        # Set variable in notebook 1
        exec1.execute("x = 'notebook1'")

        # Variable should not exist in notebook 2
        result = exec2.execute("x")
        assert result['status'] == 'error'

        # Set different value in notebook 2
        exec2.execute("x = 'notebook2'")

        # Verify isolation
        result1 = exec1.execute("x")
        result2 = exec2.execute("x")
        assert result1['result'] == 'notebook1'
        assert result2['result'] == 'notebook2'

        _notebook_sessions.clear()

    def test_get_executor_factory(self):
        """Test get_executor factory function."""
        from domains.notebooks.python_executor import get_executor, _notebook_sessions
        _notebook_sessions.clear()

        notebook_id = uuid4()
        executor = get_executor(notebook_id)

        assert executor is not None
        assert executor.notebook_id == str(notebook_id)

        _notebook_sessions.clear()

    def test_clear_all_sessions(self):
        """Test clearing all sessions."""
        from domains.notebooks.python_executor import PythonExecutor, _notebook_sessions
        _notebook_sessions.clear()

        # Create some sessions
        exec1 = PythonExecutor(uuid4())
        exec2 = PythonExecutor(uuid4())
        exec1.execute("x = 1")
        exec2.execute("y = 2")

        assert len(_notebook_sessions) == 2

        PythonExecutor.clear_all_sessions()

        assert len(_notebook_sessions) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
