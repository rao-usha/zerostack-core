# Files Feature Testing Guide

This guide covers testing the Files feature, including local folder scanning, Google Drive integration, file versioning, and table extraction.

## Test Structure

```
backend/tests/
├── test_files_models.py          # SQLModel and Pydantic model tests
├── test_files_encryption.py      # Token encryption tests
├── test_files_service.py         # Business logic tests
├── test_files_router.py          # API endpoint tests
├── test_files_integration.py     # End-to-end workflow tests
├── test_gdrive_connector.py      # Google Drive connector tests
└── test_data/                    # Test files (CSV, Excel)
```

## Running Tests

### Run All Tests
```bash
cd backend
pytest tests/test_files_*.py -v
```

### Run Specific Test Categories

**Unit Tests (Fast)**
```bash
pytest tests/test_files_models.py tests/test_files_encryption.py -v
```

**Service Layer Tests**
```bash
pytest tests/test_files_service.py -v
```

**API Tests**
```bash
pytest tests/test_files_router.py -v
```

**Integration Tests (Requires DB)**
```bash
pytest tests/test_files_integration.py -v -m integration
```

**Google Drive Tests (Requires OAuth Setup)**
```bash
pytest tests/test_gdrive_connector.py -v -m gdrive
```

### Run Tests with Coverage
```bash
pytest tests/test_files_*.py --cov=domains.files --cov-report=html
# View coverage report at htmlcov/index.html
```

### Run Specific Test
```bash
pytest tests/test_files_service.py::test_create_local_location -v
```

## Test Categories

### 1. Model Tests (`test_files_models.py`)
Tests SQLModel and Pydantic models:
- ✅ FileLocation creation and validation
- ✅ FileAsset relationships
- ✅ FileVersion tracking
- ✅ FileTable schema
- ✅ ExternalAccount for OAuth
- ✅ Enum validation (LocationType, etc.)

### 2. Encryption Tests (`test_files_encryption.py`)
Tests secure token storage:
- ✅ Token encryption/decryption
- ✅ Key derivation (PBKDF2)
- ✅ Error handling for invalid tokens
- ✅ Round-trip encryption

### 3. Service Tests (`test_files_service.py`)
Tests business logic:
- ✅ Create/list/get file locations
- ✅ Scan local folders
- ✅ Scan Google Drive folders
- ✅ File hash computation (SHA-256)
- ✅ Schema inference from DataFrames
- ✅ Version tracking (detect changes)
- ✅ Asset and table management

### 4. Router Tests (`test_files_router.py`)
Tests API endpoints:
- ✅ `POST /api/v1/files/locations` (create location)
- ✅ `GET /api/v1/files/locations` (list locations)
- ✅ `GET /api/v1/files/locations/{id}` (get location)
- ✅ `POST /api/v1/files/locations/{id}/scan` (scan folder)
- ✅ `GET /api/v1/files/assets` (list assets)
- ✅ `GET /api/v1/files/assets/{id}` (asset detail)
- ✅ `GET /api/v1/files/tables/{id}/preview` (preview table)
- ✅ `POST /api/v1/files/tables/{id}/publish` (publish to datasets)
- ✅ `GET /api/v1/files/gdrive/auth/url` (Google OAuth)
- ✅ `GET /api/v1/files/gdrive/accounts` (list accounts)

### 5. Integration Tests (`test_files_integration.py`)
Tests complete workflows:
- ✅ Full local workflow: create → scan → view → preview
- ✅ Full GDrive workflow: connect → scan → view
- ✅ Rescan detects file changes
- ✅ Excel multi-sheet creates multiple tables

### 6. Google Drive Tests (`test_gdrive_connector.py`)
Tests Google Drive integration:
- ✅ OAuth flow (auth URL generation, token exchange)
- ✅ Recursive folder listing
- ✅ Shared drives support
- ✅ File filtering (CSV, Excel only)
- ✅ File downloading and caching
- ✅ Token refresh

## Manual Testing with Test Files

### Setup Test Files
We've created test files in `C:\Users\awron\Desktop\nex-test-files\`:
- `products.csv` - Product inventory (10 rows, 9 columns)
- `customers.csv` - Customer data (15 rows, 7 columns)
- `quarterly_report.xlsx` - Multi-sheet Excel (3 sheets)

### Manual Test Scenario 1: Local Folder Scan

1. **Start the application**
   ```bash
   docker-compose -f docker-compose.dev.yml up -d
   ```

2. **Navigate to Files**
   - Go to http://localhost:3000/files/locations

3. **Create Location**
   - Click "New Location"
   - Name: "Desktop Test Files"
   - Type: Local
   - Path: `C:\Users\awron\Desktop\nex-test-files`
   - Click "Create"

4. **Scan Folder**
   - Click "Scan" on the new location
   - Should detect 3 files:
     - products.csv
     - customers.csv
     - quarterly_report.xlsx

5. **View Assets**
   - Go to "File Inventory"
   - Verify all 3 files appear
   - Check "Last Seen" timestamps

6. **View Asset Detail**
   - Click on "products.csv"
   - Should see:
     - 1 version
     - 1 table ("products")
     - 10 rows, 9 columns

7. **Preview Table**
   - Click "Preview" on the products table
   - Should see product data with columns:
     - product_id, name, category, price, stock_quantity, in_stock, supplier, rating, last_updated

8. **Test Excel Multi-Sheet**
   - Click on "quarterly_report.xlsx"
   - Should see 3 tables:
     - "Sales Summary" (3 rows, 5 columns)
     - "Top Products" (5 rows, 4 columns)
     - "Customer Segments" (4 rows, 4 columns)

### Manual Test Scenario 2: Version Detection

1. **Modify a test file**
   - Edit `C:\Users\awron\Desktop\nex-test-files\products.csv`
   - Change a price value or add a row

2. **Rescan Location**
   - Return to Files → Locations
   - Click "Scan" again

3. **Verify Version Tracking**
   - Go to the products.csv asset detail
   - Should now see 2 versions
   - Click on each version to see the changes

### Manual Test Scenario 3: Publish to Datasets

1. **Navigate to Asset**
   - Go to products.csv asset detail

2. **Click "Publish"**
   - Select target schema (e.g., "public")
   - Enter table name (e.g., "products_from_files")
   - Click "Publish"

3. **Verify in Data Explorer**
   - Go to Data Explorer
   - Navigate to the target schema
   - Find "products_from_files" table
   - Preview the data

## API Testing with curl

### Create Local Location
```bash
curl -X POST http://localhost:8000/api/v1/files/locations \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Desktop Files",
    "type": "local",
    "local_path": "C:\\Users\\awron\\Desktop\\nex-test-files"
  }'
```

### List Locations
```bash
curl http://localhost:8000/api/v1/files/locations
```

### Scan Location (replace {location_id})
```bash
curl -X POST http://localhost:8000/api/v1/files/locations/{location_id}/scan
```

### List Assets
```bash
curl http://localhost:8000/api/v1/files/assets
```

### Get Asset Detail (replace {asset_id})
```bash
curl http://localhost:8000/api/v1/files/assets/{asset_id}
```

### Preview Table (replace {table_id})
```bash
curl http://localhost:8000/api/v1/files/tables/{table_id}/preview
```

### Get Google Drive Auth URL
```bash
curl http://localhost:8000/api/v1/files/gdrive/auth/url
```

## Expected Test Results

### products.csv
- **Rows**: 10
- **Columns**: 9
- **Schema**:
  - product_id (string)
  - name (string)
  - category (string)
  - price (float)
  - stock_quantity (int)
  - in_stock (bool)
  - supplier (string)
  - rating (float, nullable)
  - last_updated (string/date)

### customers.csv
- **Rows**: 15
- **Columns**: 7
- **Schema**:
  - customer_id (string)
  - name (string)
  - email (string)
  - country (string)
  - signup_date (string/date)
  - total_purchases (int)
  - lifetime_value (float)

### quarterly_report.xlsx
- **Sheet 1: "Sales Summary"**
  - Rows: 3
  - Columns: Month, Revenue, Orders, Avg_Order_Value, Growth_Percent

- **Sheet 2: "Top Products"**
  - Rows: 5
  - Columns: Rank, Product, Units_Sold, Revenue

- **Sheet 3: "Customer Segments"**
  - Rows: 4
  - Columns: Segment, Customer_Count, Avg_Purchase, Retention_Rate

## Troubleshooting Tests

### Test Failures Due to Missing Database
If tests fail with database errors:
```bash
# Ensure Postgres is running
docker-compose -f docker-compose.dev.yml up -d db

# Run migrations
cd backend
alembic upgrade head
```

### Test Failures Due to Missing Dependencies
```bash
cd backend
pip install -r requirements-test.txt
```

### Integration Tests Skipped
Integration tests marked with `@pytest.mark.skip` require:
- Running database
- Proper environment variables
- File system access

To enable them, remove the `@pytest.mark.skip` decorator and ensure prerequisites are met.

### Google Drive Tests Skipped
GDrive tests require:
- `GOOGLE_OAUTH_CLIENT_ID` env variable
- `GOOGLE_OAUTH_CLIENT_SECRET` env variable
- `GOOGLE_OAUTH_REDIRECT_URI` env variable

## Continuous Integration

### GitHub Actions Example
```yaml
name: Files Feature Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_DB: test_db
          POSTGRES_USER: test_user
          POSTGRES_PASSWORD: test_pass
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
          pip install -r requirements-test.txt
      
      - name: Run tests
        run: |
          cd backend
          pytest tests/test_files_*.py -v --cov=domains.files
```

## Test Coverage Goals

- **Models**: 100% (simple data classes)
- **Encryption**: 100% (critical security)
- **Service**: 90%+ (core business logic)
- **Router**: 85%+ (API endpoints)
- **Integration**: 70%+ (key workflows)

## Adding New Tests

When adding new functionality:

1. **Write tests first** (TDD approach)
2. **Follow naming convention**: `test_<feature>_<scenario>`
3. **Use appropriate fixtures** from `conftest.py`
4. **Mark integration tests** with `@pytest.mark.integration`
5. **Document expected behavior** in docstrings
6. **Test both success and error cases**

### Example Test Template
```python
def test_new_feature_success(service: FilesService):
    """Test that new feature works correctly with valid input."""
    # Arrange
    input_data = create_test_data()
    
    # Act
    result = service.new_feature(input_data)
    
    # Assert
    assert result is not None
    assert result.status == "success"

def test_new_feature_invalid_input(service: FilesService):
    """Test that new feature handles invalid input properly."""
    # Arrange
    invalid_data = create_invalid_data()
    
    # Act & Assert
    with pytest.raises(ValueError):
        service.new_feature(invalid_data)
```

## Questions?

For questions about testing the Files feature:
1. Check this README first
2. Review existing test files for examples
3. Check pytest documentation: https://docs.pytest.org
4. Review FastAPI testing docs: https://fastapi.tiangolo.com/tutorial/testing/
