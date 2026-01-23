# Testing Documentation

Test guides and procedures for zerostack features.

## Test Guides

| Document | Description |
|----------|-------------|
| [TEST_DATA_DICTIONARY.md](./TEST_DATA_DICTIONARY.md) | Data Dictionary testing procedures |
| [TEST_ML_DEVELOPMENT.md](./TEST_ML_DEVELOPMENT.md) | ML Development testing procedures |
| [TEST_M5_INTEGRATION_NOW.md](./TEST_M5_INTEGRATION_NOW.md) | M5 dataset integration tests |

## Running Tests

### Backend Tests

```bash
cd backend
pytest
```

### Specific Test Files

```bash
# Run specific test
pytest tests/test_health.py

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=.
```

### Integration Tests

```bash
# From project root
pytest tests/
```

## Related Documentation

- [Testing Guide](../testing.md)
- [Development Guide](../development.md)
- [RUN_TESTS.md](../RUN_TESTS.md)
