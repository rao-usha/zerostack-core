"""Tests for Query Workbench feature."""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime


class TestQueryWorkbenchService:
    """Tests for QueryWorkbenchService."""

    def test_create_query(self):
        """Should create a new saved query."""
        from domains.data_explorer.query_workbench_service import QueryWorkbenchService

        with patch('domains.data_explorer.query_workbench_service.create_engine') as mock_create_engine:
            mock_engine = MagicMock()
            mock_create_engine.return_value = mock_engine
            mock_conn = MagicMock()
            mock_engine.begin.return_value.__enter__.return_value = mock_conn

            # Mock the insert result
            mock_row = MagicMock()
            mock_row._mapping = {
                'id': 'query_123',
                'name': 'Test Query',
                'sql': 'SELECT * FROM users',
                'db_id': 'default',
                'description': 'Test description',
                'folder': 'Analytics',
                'tags': ['test', 'users'],
                'parameters': None,
                'is_public': False,
                'created_by': 'user_1',
                'schedule_cron': None,
                'schedule_enabled': False,
                'cache_ttl_seconds': None,
                'run_count': 0,
                'last_run_at': None,
                'avg_execution_time_ms': None,
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            }
            mock_conn.execute.return_value.fetchone.return_value = mock_row

            service = QueryWorkbenchService(engine=mock_engine)
            result = service.create_query(
                name='Test Query',
                sql='SELECT * FROM users',
                db_id='default',
                description='Test description',
                folder='Analytics',
                tags=['test', 'users']
            )

            assert result['id'] == 'query_123'
            assert result['name'] == 'Test Query'
            assert result['folder'] == 'Analytics'

    def test_get_query(self):
        """Should retrieve a saved query by ID."""
        from domains.data_explorer.query_workbench_service import QueryWorkbenchService

        with patch('domains.data_explorer.query_workbench_service.create_engine') as mock_create_engine:
            mock_engine = MagicMock()
            mock_create_engine.return_value = mock_engine
            mock_conn = MagicMock()
            mock_engine.connect.return_value.__enter__.return_value = mock_conn

            mock_row = MagicMock()
            mock_row._mapping = {
                'id': 'query_123',
                'name': 'Test Query',
                'sql': 'SELECT * FROM users'
            }
            mock_conn.execute.return_value.fetchone.return_value = mock_row

            service = QueryWorkbenchService(engine=mock_engine)
            result = service.get_query('query_123')

            assert result['id'] == 'query_123'
            assert result['name'] == 'Test Query'

    def test_get_query_not_found(self):
        """Should return None when query not found."""
        from domains.data_explorer.query_workbench_service import QueryWorkbenchService

        with patch('domains.data_explorer.query_workbench_service.create_engine') as mock_create_engine:
            mock_engine = MagicMock()
            mock_create_engine.return_value = mock_engine
            mock_conn = MagicMock()
            mock_engine.connect.return_value.__enter__.return_value = mock_conn
            mock_conn.execute.return_value.fetchone.return_value = None

            service = QueryWorkbenchService(engine=mock_engine)
            result = service.get_query('nonexistent')

            assert result is None

    def test_update_query(self):
        """Should update a saved query."""
        from domains.data_explorer.query_workbench_service import QueryWorkbenchService

        with patch('domains.data_explorer.query_workbench_service.create_engine') as mock_create_engine:
            mock_engine = MagicMock()
            mock_create_engine.return_value = mock_engine
            mock_conn = MagicMock()
            mock_engine.begin.return_value.__enter__.return_value = mock_conn

            mock_row = MagicMock()
            mock_row._mapping = {
                'id': 'query_123',
                'name': 'Updated Query',
                'sql': 'SELECT id, name FROM users',
                'description': 'Updated description'
            }
            mock_conn.execute.return_value.fetchone.return_value = mock_row

            service = QueryWorkbenchService(engine=mock_engine)
            result = service.update_query(
                query_id='query_123',
                name='Updated Query',
                sql='SELECT id, name FROM users'
            )

            assert result['name'] == 'Updated Query'

    def test_delete_query(self):
        """Should delete a saved query."""
        from domains.data_explorer.query_workbench_service import QueryWorkbenchService

        with patch('domains.data_explorer.query_workbench_service.create_engine') as mock_create_engine:
            mock_engine = MagicMock()
            mock_create_engine.return_value = mock_engine
            mock_conn = MagicMock()
            mock_engine.begin.return_value.__enter__.return_value = mock_conn

            mock_result = MagicMock()
            mock_result.rowcount = 1
            mock_conn.execute.return_value = mock_result

            service = QueryWorkbenchService(engine=mock_engine)
            result = service.delete_query('query_123')

            assert result is True

    def test_delete_query_not_found(self):
        """Should return False when query to delete not found."""
        from domains.data_explorer.query_workbench_service import QueryWorkbenchService

        with patch('domains.data_explorer.query_workbench_service.create_engine') as mock_create_engine:
            mock_engine = MagicMock()
            mock_create_engine.return_value = mock_engine
            mock_conn = MagicMock()
            mock_engine.begin.return_value.__enter__.return_value = mock_conn

            mock_result = MagicMock()
            mock_result.rowcount = 0
            mock_conn.execute.return_value = mock_result

            service = QueryWorkbenchService(engine=mock_engine)
            result = service.delete_query('nonexistent')

            assert result is False

    def test_list_queries(self):
        """Should list saved queries with pagination."""
        from domains.data_explorer.query_workbench_service import QueryWorkbenchService

        with patch('domains.data_explorer.query_workbench_service.create_engine') as mock_create_engine:
            mock_engine = MagicMock()
            mock_create_engine.return_value = mock_engine
            mock_conn = MagicMock()
            mock_engine.connect.return_value.__enter__.return_value = mock_conn

            # Mock count query result
            mock_count_result = MagicMock()
            mock_count_result.scalar.return_value = 25

            # Mock list query result
            mock_rows = [
                MagicMock(_mapping={'id': 'q1', 'name': 'Query 1'}),
                MagicMock(_mapping={'id': 'q2', 'name': 'Query 2'})
            ]

            # First call is count, second is list
            mock_conn.execute.side_effect = [mock_count_result, mock_rows]

            service = QueryWorkbenchService(engine=mock_engine)
            queries, total = service.list_queries(page=1, page_size=10)

            assert len(queries) == 2
            assert total == 25


class TestParameterSubstitution:
    """Tests for parameter substitution in queries."""

    def test_substitute_string_parameter(self):
        """Should substitute string parameters correctly."""
        from domains.data_explorer.query_workbench_service import QueryWorkbenchService

        with patch('domains.data_explorer.query_workbench_service.create_engine'):
            service = QueryWorkbenchService.__new__(QueryWorkbenchService)

            sql = "SELECT * FROM users WHERE name = {{name}}"
            result = service._substitute_parameters(sql, {'name': 'John'})

            assert result == "SELECT * FROM users WHERE name = 'John'"

    def test_substitute_numeric_parameter(self):
        """Should substitute numeric parameters correctly."""
        from domains.data_explorer.query_workbench_service import QueryWorkbenchService

        with patch('domains.data_explorer.query_workbench_service.create_engine'):
            service = QueryWorkbenchService.__new__(QueryWorkbenchService)

            sql = "SELECT * FROM users WHERE age > {{min_age}}"
            result = service._substitute_parameters(sql, {'min_age': 21})

            assert result == "SELECT * FROM users WHERE age > 21"

    def test_substitute_null_parameter(self):
        """Should substitute NULL for None values."""
        from domains.data_explorer.query_workbench_service import QueryWorkbenchService

        with patch('domains.data_explorer.query_workbench_service.create_engine'):
            service = QueryWorkbenchService.__new__(QueryWorkbenchService)

            sql = "SELECT * FROM users WHERE deleted_at = {{deleted_at}}"
            result = service._substitute_parameters(sql, {'deleted_at': None})

            assert result == "SELECT * FROM users WHERE deleted_at = NULL"

    def test_substitute_boolean_parameter(self):
        """Should substitute boolean parameters correctly."""
        from domains.data_explorer.query_workbench_service import QueryWorkbenchService

        with patch('domains.data_explorer.query_workbench_service.create_engine'):
            service = QueryWorkbenchService.__new__(QueryWorkbenchService)

            sql = "SELECT * FROM users WHERE active = {{is_active}}"
            result = service._substitute_parameters(sql, {'is_active': True})

            assert result == "SELECT * FROM users WHERE active = TRUE"

    def test_escape_quotes_in_string(self):
        """Should escape single quotes in string values."""
        from domains.data_explorer.query_workbench_service import QueryWorkbenchService

        with patch('domains.data_explorer.query_workbench_service.create_engine'):
            service = QueryWorkbenchService.__new__(QueryWorkbenchService)

            sql = "SELECT * FROM users WHERE name = {{name}}"
            result = service._substitute_parameters(sql, {'name': "O'Brien"})

            assert result == "SELECT * FROM users WHERE name = 'O''Brien'"

    def test_substitute_multiple_parameters(self):
        """Should substitute multiple parameters."""
        from domains.data_explorer.query_workbench_service import QueryWorkbenchService

        with patch('domains.data_explorer.query_workbench_service.create_engine'):
            service = QueryWorkbenchService.__new__(QueryWorkbenchService)

            sql = "SELECT * FROM orders WHERE date >= {{start}} AND date <= {{end}} AND status = {{status}}"
            result = service._substitute_parameters(sql, {
                'start': '2024-01-01',
                'end': '2024-12-31',
                'status': 'completed'
            })

            assert "'2024-01-01'" in result
            assert "'2024-12-31'" in result
            assert "'completed'" in result


class TestQueryExecution:
    """Tests for query execution."""

    def test_execute_saved_query(self):
        """Should execute a saved query and record execution."""
        from domains.data_explorer.query_workbench_service import QueryWorkbenchService

        with patch('domains.data_explorer.query_workbench_service.create_engine') as mock_create_engine, \
             patch('domains.data_explorer.query_workbench_service.DataExplorerService') as mock_explorer:

            mock_engine = MagicMock()
            mock_create_engine.return_value = mock_engine
            mock_conn = MagicMock()
            mock_engine.connect.return_value.__enter__.return_value = mock_conn
            mock_engine.begin.return_value.__enter__.return_value = mock_conn

            # Mock get_query
            mock_query_row = MagicMock()
            mock_query_row._mapping = {
                'id': 'query_123',
                'sql': 'SELECT * FROM users',
                'db_id': 'default'
            }
            mock_conn.execute.return_value.fetchone.return_value = mock_query_row

            # Mock explorer service
            mock_explorer_instance = MagicMock()
            mock_explorer.return_value = mock_explorer_instance
            mock_explorer_instance.execute_query.return_value = {
                'columns': ['id', 'name'],
                'rows': [[1, 'Alice'], [2, 'Bob']],
                'total_rows_estimate': 2,
                'execution_time_ms': 15.5
            }

            service = QueryWorkbenchService(engine=mock_engine)
            service.explorer_service = mock_explorer_instance

            # Mock internal methods
            service._create_execution = MagicMock(return_value='exec_456')
            service._update_execution_success = MagicMock()
            service._update_query_stats = MagicMock()

            result = service.execute_query('query_123')

            assert result['execution_id'] == 'exec_456'
            assert result['columns'] == ['id', 'name']
            assert len(result['rows']) == 2

    def test_execute_adhoc_query(self):
        """Should execute an ad-hoc query."""
        from domains.data_explorer.query_workbench_service import QueryWorkbenchService

        with patch('domains.data_explorer.query_workbench_service.create_engine') as mock_create_engine, \
             patch('domains.data_explorer.query_workbench_service.DataExplorerService') as mock_explorer:

            mock_engine = MagicMock()
            mock_create_engine.return_value = mock_engine
            mock_conn = MagicMock()
            mock_engine.begin.return_value.__enter__.return_value = mock_conn

            # Mock explorer service
            mock_explorer_instance = MagicMock()
            mock_explorer.return_value = mock_explorer_instance
            mock_explorer_instance.execute_query.return_value = {
                'columns': ['count'],
                'rows': [[100]],
                'total_rows_estimate': 1,
                'execution_time_ms': 5.2
            }

            service = QueryWorkbenchService(engine=mock_engine)
            service.explorer_service = mock_explorer_instance

            # Mock internal methods
            service._create_execution = MagicMock(return_value='exec_789')
            service._update_execution_success = MagicMock()

            result = service.execute_adhoc_query(
                sql='SELECT COUNT(*) as count FROM users',
                db_id='default'
            )

            assert result['execution_id'] == 'exec_789'
            assert result['columns'] == ['count']

    def test_execute_query_with_parameters(self):
        """Should execute query with parameter substitution."""
        from domains.data_explorer.query_workbench_service import QueryWorkbenchService

        with patch('domains.data_explorer.query_workbench_service.create_engine') as mock_create_engine, \
             patch('domains.data_explorer.query_workbench_service.DataExplorerService') as mock_explorer:

            mock_engine = MagicMock()
            mock_create_engine.return_value = mock_engine
            mock_conn = MagicMock()
            mock_engine.connect.return_value.__enter__.return_value = mock_conn
            mock_engine.begin.return_value.__enter__.return_value = mock_conn

            # Mock get_query with parameterized SQL
            mock_query_row = MagicMock()
            mock_query_row._mapping = {
                'id': 'query_123',
                'sql': 'SELECT * FROM users WHERE status = {{status}}',
                'db_id': 'default'
            }
            mock_conn.execute.return_value.fetchone.return_value = mock_query_row

            # Mock explorer service
            mock_explorer_instance = MagicMock()
            mock_explorer.return_value = mock_explorer_instance
            mock_explorer_instance.execute_query.return_value = {
                'columns': ['id', 'name', 'status'],
                'rows': [[1, 'Alice', 'active']],
                'total_rows_estimate': 1,
                'execution_time_ms': 10.0
            }

            service = QueryWorkbenchService(engine=mock_engine)
            service.explorer_service = mock_explorer_instance
            service._create_execution = MagicMock(return_value='exec_123')
            service._update_execution_success = MagicMock()
            service._update_query_stats = MagicMock()

            result = service.execute_query(
                'query_123',
                parameters={'status': 'active'}
            )

            # Verify the explorer was called with substituted SQL
            mock_explorer_instance.execute_query.assert_called_once()
            call_kwargs = mock_explorer_instance.execute_query.call_args[1]
            assert call_kwargs['sql'] == "SELECT * FROM users WHERE status = 'active'"


class TestExecutionHistory:
    """Tests for execution history tracking."""

    def test_get_query_executions(self):
        """Should retrieve execution history for a query."""
        from domains.data_explorer.query_workbench_service import QueryWorkbenchService

        with patch('domains.data_explorer.query_workbench_service.create_engine') as mock_create_engine:
            mock_engine = MagicMock()
            mock_create_engine.return_value = mock_engine
            mock_conn = MagicMock()
            mock_engine.connect.return_value.__enter__.return_value = mock_conn

            mock_rows = [
                MagicMock(_mapping={
                    'id': 'exec_1',
                    'saved_query_id': 'query_123',
                    'status': 'success',
                    'execution_time_ms': 15.5
                }),
                MagicMock(_mapping={
                    'id': 'exec_2',
                    'saved_query_id': 'query_123',
                    'status': 'error',
                    'error_message': 'Syntax error'
                })
            ]
            mock_conn.execute.return_value = mock_rows

            service = QueryWorkbenchService(engine=mock_engine)
            executions = service.get_query_executions('query_123', limit=10)

            assert len(executions) == 2
            assert executions[0]['status'] == 'success'
            assert executions[1]['status'] == 'error'

    def test_get_recent_executions(self):
        """Should retrieve recent executions across all queries."""
        from domains.data_explorer.query_workbench_service import QueryWorkbenchService

        with patch('domains.data_explorer.query_workbench_service.create_engine') as mock_create_engine:
            mock_engine = MagicMock()
            mock_create_engine.return_value = mock_engine
            mock_conn = MagicMock()
            mock_engine.connect.return_value.__enter__.return_value = mock_conn

            mock_rows = [
                MagicMock(_mapping={'id': 'exec_1', 'db_id': 'default'}),
                MagicMock(_mapping={'id': 'exec_2', 'db_id': 'analytics'})
            ]
            mock_conn.execute.return_value = mock_rows

            service = QueryWorkbenchService(engine=mock_engine)
            executions = service.get_recent_executions(limit=50)

            assert len(executions) == 2


class TestCloneQuery:
    """Tests for query cloning."""

    def test_clone_query(self):
        """Should clone a saved query."""
        from domains.data_explorer.query_workbench_service import QueryWorkbenchService

        with patch('domains.data_explorer.query_workbench_service.create_engine') as mock_create_engine:
            mock_engine = MagicMock()
            mock_create_engine.return_value = mock_engine
            mock_conn = MagicMock()
            mock_engine.connect.return_value.__enter__.return_value = mock_conn
            mock_engine.begin.return_value.__enter__.return_value = mock_conn

            # Mock original query
            original_row = MagicMock()
            original_row._mapping = {
                'id': 'query_123',
                'name': 'Original Query',
                'sql': 'SELECT * FROM users',
                'db_id': 'default',
                'description': 'Original description',
                'folder': 'Analytics',
                'tags': ['test'],
                'parameters': None
            }

            # Mock cloned query
            cloned_row = MagicMock()
            cloned_row._mapping = {
                'id': 'query_456',
                'name': 'Cloned Query',
                'sql': 'SELECT * FROM users',
                'db_id': 'default',
                'is_public': False
            }

            # First call returns original, second returns cloned
            mock_conn.execute.return_value.fetchone.side_effect = [original_row, cloned_row]

            service = QueryWorkbenchService(engine=mock_engine)
            result = service.clone_query('query_123', 'Cloned Query')

            assert result['id'] == 'query_456'
            assert result['name'] == 'Cloned Query'

    def test_clone_query_not_found(self):
        """Should raise error when cloning non-existent query."""
        from domains.data_explorer.query_workbench_service import QueryWorkbenchService

        with patch('domains.data_explorer.query_workbench_service.create_engine') as mock_create_engine:
            mock_engine = MagicMock()
            mock_create_engine.return_value = mock_engine
            mock_conn = MagicMock()
            mock_engine.connect.return_value.__enter__.return_value = mock_conn
            mock_conn.execute.return_value.fetchone.return_value = None

            service = QueryWorkbenchService(engine=mock_engine)

            with pytest.raises(ValueError, match="not found"):
                service.clone_query('nonexistent', 'Clone')


class TestFolders:
    """Tests for folder management."""

    def test_get_folders(self):
        """Should retrieve folders with query counts."""
        from domains.data_explorer.query_workbench_service import QueryWorkbenchService

        with patch('domains.data_explorer.query_workbench_service.create_engine') as mock_create_engine:
            mock_engine = MagicMock()
            mock_create_engine.return_value = mock_engine
            mock_conn = MagicMock()
            mock_engine.connect.return_value.__enter__.return_value = mock_conn

            mock_rows = [
                ('Analytics', 5),
                ('Reports', 3),
                ('Ad-hoc', 10)
            ]
            mock_conn.execute.return_value = mock_rows

            service = QueryWorkbenchService(engine=mock_engine)
            folders = service.get_folders()

            assert len(folders) == 3
            assert folders[0] == {'name': 'Analytics', 'query_count': 5}
            assert folders[1] == {'name': 'Reports', 'query_count': 3}


class TestPydanticModels:
    """Tests for Pydantic models validation."""

    def test_saved_query_create_model(self):
        """SavedQueryCreate should validate correctly."""
        from domains.data_explorer.query_workbench_models import SavedQueryCreate

        query = SavedQueryCreate(
            name="Test Query",
            sql="SELECT * FROM users",
            db_id="default",
            folder="Analytics",
            tags=["test", "users"]
        )

        assert query.name == "Test Query"
        assert query.db_id == "default"
        assert query.is_public is False

    def test_saved_query_create_validation_name_required(self):
        """SavedQueryCreate should require name."""
        from domains.data_explorer.query_workbench_models import SavedQueryCreate
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            SavedQueryCreate(sql="SELECT 1")

    def test_query_parameter_model(self):
        """QueryParameter should validate correctly."""
        from domains.data_explorer.query_workbench_models import QueryParameter

        param = QueryParameter(
            name="start_date",
            type="date",
            default="2024-01-01",
            description="Start date for the report"
        )

        assert param.name == "start_date"
        assert param.type == "date"

    def test_execute_query_request_defaults(self):
        """ExecuteQueryRequest should have sensible defaults."""
        from domains.data_explorer.query_workbench_models import ExecuteQueryRequest

        request = ExecuteQueryRequest()

        assert request.page == 1
        assert request.page_size == 100
        assert request.parameters is None

    def test_query_result_response_model(self):
        """QueryResultResponse should validate correctly."""
        from domains.data_explorer.query_workbench_models import QueryResultResponse

        result = QueryResultResponse(
            execution_id="exec_123",
            columns=["id", "name"],
            rows=[[1, "Alice"], [2, "Bob"]],
            total_rows=2,
            execution_time_ms=15.5,
            page=1,
            page_size=100
        )

        assert result.execution_id == "exec_123"
        assert len(result.columns) == 2
        assert len(result.rows) == 2


class TestSingleton:
    """Tests for singleton service pattern."""

    def test_get_query_workbench_service_singleton(self):
        """Should return the same service instance."""
        from domains.data_explorer import query_workbench_service as module

        # Reset singleton
        module._service_instance = None

        with patch.object(module, 'create_engine') as mock_create_engine:
            mock_engine = MagicMock()
            mock_create_engine.return_value = mock_engine

            service1 = module.get_query_workbench_service()
            service2 = module.get_query_workbench_service()

            assert service1 is service2
