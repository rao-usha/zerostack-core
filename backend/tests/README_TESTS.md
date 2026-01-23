# Files Feature Test Suite

This directory contains comprehensive tests for the Files feature.

## Test Structure

```
tests/
├── conftest.py                    # Pytest configuration & shared fixtures
├── test_files_models.py           # SQLModel database models tests
├── test_files_encryption.py       # Token encryption/decryption tests
├── test_files_service.py          # Business logic & service layer tests
├── test_files_router.py           # API endpoint tests
├── test_gdrive_connector.py       # Google Drive connector tests
└── test_files_integration.py      # End-to-end integration tests
```

## Running Tests

### Run all tests
```bash
cd backend
pytest tests/
```

### Run specific test file
```bash
pytest tests/test_files_models.py
pytest tests/test_files_encryption.py
```

### Run with coverage
```bash
pytest --cov=domains.files --cov-report=html tests/
```

### Run with verbose output
```bash
pytest -v tests/
```

### Run only fast tests (skip integration)
```bash
pytest -m "not integration" tests/
```

## Test Categories

### Unit Tests
- **Models**: Test database models, relationships, validation
- **Encryption**: Test token encryption/decryption
- **Service**: Test business logic with mocked dependencies
- **Router**: Test API endpoints with test client
- **GDrive Connector**: Test Google Drive integration with mocks

### Integration Tests
- **End-to-end**: Test complete workflows (create location → scan → preview → publish)
- **Database**: Test with real Postgres (Docker required)

## Test Coverage Goals

- **Models**: 100% coverage (straightforward CRUD)
- **Encryption**: 100% coverage (critical security component)
- **Service**: 90%+ coverage (core business logic)
- **Router**: 80%+ coverage (API endpoints)
- **GDrive Connector**: 85%+ coverage (external API integration)

## Key Testing Patterns

### 1. Database Tests (SQLModel)
```python
@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
```

### 2. Mocking External Services
```python
@pytest.fixture
def mock_gdrive_connector():
    return Mock()

def test_with_mock(mock_gdrive_connector):
    mock_gdrive_connector.list_files.return_value = [...]
```

### 3. Testing API Endpoints
```python
def test_endpoint(client: TestClient):
    response = client.get("/api/v1/files/locations")
    assert response.status_code == 200
```

### 4. Parameterized Tests
```python
@pytest.mark.parametrize("input,expected", [
    ("test.csv", ".csv"),
    ("file.xlsx", ".xlsx"),
])
def test_extension(input, expected):
    assert get_extension(input) == expected
```

## Writing New Tests

### Test File Naming
- Use `test_*.py` prefix
- Match the module being tested: `test_<module_name>.py`

### Test Function Naming
- Use descriptive names: `test_<what>_<scenario>_<expected>`
- Examples:
  - `test_create_location_with_valid_data`
  - `test_scan_location_when_folder_not_found_raises_error`

### Test Structure (Arrange-Act-Assert)
```python
def test_something():
    # Arrange: setup test data
    location = FileLocation(name="Test", ...)
    
    # Act: perform the action
    result = service.scan_location(location.id)
    
    # Assert: verify the outcome
    assert result["status"] == "success"
    assert result["new_files"] == 5
```

## Common Fixtures

Defined in `conftest.py`:
- `session`: In-memory SQLite database session
- `client`: FastAPI test client
- `mock_gdrive_connector`: Mocked Google Drive service

## Environment Variables for Testing

Set in `conftest.py`:
- `ENVIRONMENT=test`
- `DATABASE_URL=sqlite:///:memory:`
- `SECRET_KEY=test-secret-key-for-testing-only`
- `ENCRYPTION_KEY=test-encryption-key-for-testing`

## Continuous Integration

Tests run automatically on:
- Pull requests to `main`/`develop`
- Commits to `main`/`develop`
- Nightly builds (full integration suite)

## Troubleshooting

### Import Errors
Ensure `backend/` is in Python path:
```python
sys.path.insert(0, str(Path(__file__).parent.parent))
```

### Database Errors
- Use in-memory SQLite for unit tests
- Use Docker Postgres for integration tests
- Ensure migrations are up to date

### Mock Failures
- Verify mock setup matches actual interface
- Use `Mock(spec=ActualClass)` for type checking
- Check `mock.assert_called_once()` patterns

## Test Data

Sample test files in `backend/tests/fixtures/`:
- `sample.csv`: Basic CSV with 3 columns, 10 rows
- `sample.xlsx`: Excel with 2 sheets
- `nested/`: Folder structure for recursive scanning tests

## Dependencies

Additional test dependencies (in `requirements.txt`):
```
pytest>=7.4.0
pytest-cov>=4.1.0
pytest-mock>=3.11.1
pytest-asyncio>=0.21.0
```

## Best Practices

1. **Isolate tests**: Each test should be independent
2. **Use fixtures**: Share setup code via fixtures
3. **Mock external services**: Don't hit real Google Drive in unit tests
4. **Test edge cases**: Empty inputs, null values, large files
5. **Test error paths**: Ensure errors are handled gracefully
6. **Keep tests fast**: Unit tests should run in < 1s each
7. **Clear assertions**: One logical assertion per test preferred
8. **Clean up**: Use `yield` in fixtures for teardown

## Coverage Report

After running with `--cov`, open `htmlcov/index.html` to view detailed coverage report.
