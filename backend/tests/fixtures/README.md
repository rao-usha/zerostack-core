# Test Fixtures

This directory contains sample data files used for testing the Files feature.

## Files

### sample.csv
Basic CSV file with 10 rows and 5 columns (product data)

### sample_with_nulls.csv
CSV file with missing/null values for testing null handling

### nested/
Subdirectory with additional files for testing recursive scanning

## Usage in Tests

```python
import pytest
from pathlib import Path

@pytest.fixture
def fixtures_dir():
    return Path(__file__).parent / "fixtures"

def test_csv_parsing(fixtures_dir):
    csv_path = fixtures_dir / "sample.csv"
    # Test CSV parsing logic
```
