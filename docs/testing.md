# Testing Guide

## Overview

NEX.AI includes comprehensive testing suites for backend, frontend, and distillation pipeline components. Testing ensures code quality, prevents regressions, and validates functionality.

## Test Categories

### Unit Tests
- **Backend**: Individual function and class testing
- **Frontend**: Component and utility function testing
- **Distillation**: Algorithm and pipeline component testing

### Integration Tests
- **API Endpoints**: Full request/response cycles
- **Database Operations**: Data persistence and retrieval
- **External APIs**: OpenAI integration testing

### End-to-End Tests
- **User Workflows**: Complete feature validation
- **Data Pipelines**: Upload → Process → Analyze cycles
- **Distillation Flows**: Context → Examples → Datasets

## Backend Testing

### Unit Tests

```bash
# Run all backend tests
cd backend
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_summarization.py -v

# Run with coverage
python -m pytest --cov=. --cov-report=html tests/
```

### Test Files Structure

```
backend/tests/
├── test_health.py                 # Health endpoint tests
├── test_summarization.py          # Document summarization tests
├── test_document_upload_summarization.py  # Upload + summarize integration
└── test_*.py                      # Additional test files
```

### Writing Tests

```python
# Example test structure
import pytest
from app.services.document_summarization import DocumentSummarizer

class TestDocumentSummarizer:
    def test_initialization_with_api_key(self):
        """Test proper initialization with API key."""
        summarizer = DocumentSummarizer(api_key="test-key")
        assert summarizer.client is not None

    def test_summarization_with_valid_text(self):
        """Test summarization with valid input."""
        # Test implementation
        pass

    def test_error_handling_no_api_key(self):
        """Test error handling when no API key provided."""
        # Test implementation
        pass
```

## Frontend Testing

### Component Tests

```bash
cd frontend

# Run all tests
npm test

# Run tests in watch mode
npm run test:watch

# Run with coverage
npm run test:coverage
```

### Test Files Structure

```
frontend/src/
├── components/
│   └── __tests__/          # Component tests
├── api/
│   └── __tests__/          # API client tests
└── utils/
    └── __tests__/          # Utility function tests
```

### Writing Component Tests

```typescript
// Example React component test
import { render, screen, fireEvent } from '@testing-library/react'
import { Button } from '../Button'

describe('Button', () => {
  it('renders with correct text', () => {
    render(<Button>Click me</Button>)
    expect(screen.getByText('Click me')).toBeInTheDocument()
  })

  it('calls onClick when clicked', () => {
    const handleClick = jest.fn()
    render(<Button onClick={handleClick}>Click me</Button>)

    fireEvent.click(screen.getByText('Click me'))
    expect(handleClick).toHaveBeenCalledTimes(1)
  })
})
```

## Distillation Testing

### Pipeline Tests

```bash
cd nex-collector

# Run all tests
python -m pytest tests/ -v

# Run specific distillation tests
python -m pytest tests/test_deduplication_drift.py -v

# Run with verbose output
python -m pytest tests/ -v -s
```

### Test Categories

- **Deduplication**: Test data deduplication algorithms
- **Drift Detection**: Test data drift detection
- **Retrieval**: Test MMR and retrieval algorithms
- **Quality Signals**: Test quality assessment
- **Rationales**: Test critique generation
- **Soft Labels**: Test label generation
- **Teacher Ensembles**: Test ensemble methods

## Integration Testing

### API Integration Tests

```bash
# Test backend API endpoints
cd backend
python test_summarization_full.py

# Test distillation API
cd nex-collector
python -c "
import requests
response = requests.get('http://localhost:8080/healthz')
print(f'Health check: {response.status_code}')
"
```

### End-to-End Testing

```bash
# Full workflow test (manual)
# 1. Upload dataset via API
# 2. Generate insights
# 3. Build predictive model
# 4. Generate synthetic data
# 5. Verify results in UI
```

## Quality Assurance

### Code Quality Tools

```bash
# Backend quality checks
cd backend
pip install black ruff mypy pytest-cov

# Format code
black .

# Lint code
ruff check .

# Type check
mypy .

# Run tests with coverage
pytest --cov=. --cov-report=html
```

### Frontend Quality Checks

```bash
cd frontend

# Lint and format
npm run lint
npm run format

# Type check
npm run type-check

# Build check
npm run build
```

## CI/CD Pipeline

### GitHub Actions Workflow

The project includes automated testing via GitHub Actions:

```yaml
# .github/workflows/ci.yml
name: CI
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run tests
        run: make test
```

### Local CI Simulation

```bash
# Run full CI pipeline locally
make verify

# Individual CI steps
make format    # Code formatting
make lint      # Linting
make type      # Type checking
make test      # Unit tests
make build     # Build verification
make smokes    # Smoke tests
```

## Test Data

### Sample Datasets

```bash
# Use provided test data
ls example_data/
# sample_sales_data.csv

# Generate synthetic test data
cd backend
python -c "
import pandas as pd
import numpy as np

# Generate test dataset
data = {
    'feature1': np.random.randn(100),
    'feature2': np.random.randn(100),
    'target': np.random.randint(0, 2, 100)
}
df = pd.DataFrame(data)
df.to_csv('test_data.csv', index=False)
"
```

### Mock Services

```python
# Mock OpenAI API for testing
import pytest
from unittest.mock import patch

@patch('openai.ChatCompletion.create')
def test_ai_feature(mock_openai):
    mock_openai.return_value = {
        'choices': [{'message': {'content': 'Mock response'}}]
    }
    # Test AI feature
    result = ai_function()
    assert result == 'Mock response'
```

## Performance Testing

### Load Testing

```bash
# Simple load test with curl
for i in {1..10}; do
  curl -s http://localhost:8000/healthz &
done
wait

# Advanced load testing
pip install locust
locust -f locustfile.py
```

### Memory and Performance Profiling

```python
# Profile memory usage
from memory_profiler import profile

@profile
def test_memory_intensive_function():
    # Test implementation
    pass

# Profile execution time
import time

def test_performance():
    start = time.time()
    # Execute function
    end = time.time()
    assert end - start < 1.0  # Should complete in < 1 second
```

## Debugging Tests

### Common Test Issues

1. **Test Discovery Issues**
   ```bash
   # Ensure test files are named correctly
   find . -name "test_*.py" -o -name "*_test.py"

   # Run pytest with discovery debug
   pytest --collect-only -q
   ```

2. **Import Errors**
   ```bash
   # Check Python path
   python -c "import sys; print(sys.path)"

   # Add current directory to path
   PYTHONPATH=. pytest
   ```

3. **Database Test Issues**
   ```bash
   # Use test database
   export DATABASE_URL="postgresql://test:test@localhost:5433/test_db"

   # Reset test database
   pytest --create-db
   ```

4. **Async Test Issues**
   ```python
   # Use pytest-asyncio
   import pytest_asyncio

   @pytest.mark.asyncio
   async def test_async_function():
       result = await async_function()
       assert result is not None
   ```

## Test Organization Best Practices

### Test File Naming
- `test_*.py` for test files
- `*_test.py` for test modules
- Descriptive names: `test_user_authentication.py`

### Test Structure
```python
class TestFeatureName:
    def setup_method(self):
        """Setup before each test."""
        pass

    def teardown_method(self):
        """Cleanup after each test."""
        pass

    def test_feature_behavior(self):
        """Test specific behavior."""
        pass

    def test_edge_case(self):
        """Test edge cases."""
        pass
```

### Test Data Management
- Use fixtures for reusable test data
- Avoid hard-coded test data
- Clean up after tests complete

### Mocking Strategy
- Mock external dependencies (APIs, databases)
- Use appropriate mocking libraries
- Avoid over-mocking (test real behavior when possible)

## Continuous Integration

### Quality Gates

- **Code Coverage**: Minimum 80% coverage required
- **Linting**: No linting errors allowed
- **Type Checking**: All type hints must be valid
- **Build Success**: All services must build successfully

### Automated Quality Checks

```makefile
# Makefile targets
.PHONY: verify format lint type test build smokes clean

verify: format lint type test build smokes

format:
    black .
    isort .

lint:
    ruff check .
    bandit -r .

type:
    mypy .

test:
    pytest --cov=. --cov-fail-under=80

build:
    docker-compose build

smokes:
    ./scripts/smoke_backend.sh

clean:
    find . -type f -name "*.pyc" -delete
    find . -type d -name "__pycache__" -delete
    rm -rf .coverage htmlcov
```

## Contributing to Tests

### Adding New Tests

1. **Identify test scope**: Unit, integration, or E2E
2. **Create test file**: Follow naming conventions
3. **Write descriptive test cases**: Clear names and docstrings
4. **Include edge cases**: Test error conditions
5. **Update documentation**: Add to this testing guide

### Test Maintenance

- **Keep tests updated**: Update when code changes
- **Remove obsolete tests**: Delete tests for removed features
- **Refactor test code**: Apply same standards as production code
- **Review test coverage**: Ensure new code is tested

## Troubleshooting Tests

### Debug Test Failures

```bash
# Run single failing test with debug output
pytest tests/test_specific.py::TestClass::test_method -v -s

# Debug with pdb
pytest --pdb tests/test_specific.py

# Show local variables on failure
pytest --tb=short --showlocals tests/
```

### Common Test Patterns

```python
# Parameterized tests
@pytest.mark.parametrize("input,expected", [
    (1, 2),
    (2, 3),
    (3, 4),
])
def test_increment(input, expected):
    assert increment(input) == expected

# Fixtures for setup/teardown
@pytest.fixture
def sample_data():
    return {"key": "value"}

def test_with_fixture(sample_data):
    assert sample_data["key"] == "value"

# Mock external dependencies
@patch('module.function')
def test_with_mock(mock_function):
    mock_function.return_value = "mocked"
    result = call_function()
    assert result == "mocked"
```

## Resources

- **pytest Documentation**: https://docs.pytest.org/
- **Testing Library**: https://testing-library.com/docs/react-testing-library/intro/
- **Jest Documentation**: https://jestjs.io/docs/getting-started
- **Locust Documentation**: https://docs.locust.io/
