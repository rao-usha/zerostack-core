# Files Feature - Complete Testing Guide

This guide covers all testing for the zerostack Files feature, including automated tests and manual testing with real files.

## Quick Start

### 1. Test Files Setup
We've created test files in `C:\Users\awron\Desktop\nex-test-files\`:
- ✅ `products.csv` - 10 products with inventory data
- ✅ `customers.csv` - 15 customers with purchase history  
- ✅ `quarterly_report.xlsx` - 3-sheet Excel report

### 2. Run Automated Tests
```powershell
cd backend

# Run all unit tests (fast, no DB required)
.\run_tests.ps1 unit

# Run service tests
.\run_tests.ps1 service

# Run API tests
.\run_tests.ps1 api

# Run all tests
.\run_tests.ps1 all
```

### 3. Run Manual Tests with Test Files
```powershell
cd backend

# Verify test files structure
python tests/test_manual_scenarios.py

# Test actual scanning (requires running backend)
.\run_tests.ps1 manual-api
```

### 4. Manual Testing in UI
1. Start the application:
   ```powershell
   docker-compose -f docker-compose.dev.yml up -d
   ```

2. Navigate to http://localhost:3000/files/locations

3. Create a new location:
   - Name: "Desktop Test Files"
   - Type: Local
   - Path: `C:\Users\awron\Desktop\nex-test-files`
   - Click "Create"

4. Click "Scan" to detect files

5. Go to "File Inventory" to see all detected files

6. Click on any file to view details, versions, and tables

7. Click "Preview" to see table data

8. Click "Publish" to publish tables to the Data Explorer

## Test Coverage

### Automated Tests

| Test File | Purpose | Coverage |
|-----------|---------|----------|
| `test_files_models.py` | SQLModel & Pydantic models | 100% |
| `test_files_encryption.py` | Token encryption security | 100% |
| `test_files_service.py` | Business logic | 90%+ |
| `test_files_router.py` | API endpoints | 85%+ |
| `test_files_integration.py` | End-to-end workflows | 70%+ |
| `test_gdrive_connector.py` | Google Drive integration | 85%+ |
| `test_manual_scenarios.py` | Real file testing | Manual |

### Test Categories

#### ✅ Unit Tests (Fast, No Dependencies)
- File location models
- File asset models
- Version tracking models
- Table schema models
- Token encryption/decryption
- Validation logic

#### ✅ Service Tests (Mocked Dependencies)
- Create/list/get locations
- Scan local folders
- Scan Google Drive folders
- File hash computation
- Schema inference
- Version detection

#### ✅ API Tests (TestClient)
- All REST endpoints
- Request validation
- Error handling
- Response formats

#### ✅ Integration Tests (Requires DB)
- Full local workflow: create → scan → view → preview → publish
- Full GDrive workflow: connect → scan → view
- Version change detection
- Excel multi-sheet handling

#### ✅ Manual Tests (Real Files)
- Test file validation
- CSV structure verification
- Excel multi-sheet verification
- API scanning with real files
- Version detection with real changes

## Test Commands Reference

### PowerShell (Windows)
```powershell
# Navigate to backend
cd backend

# Unit tests (models + encryption)
.\run_tests.ps1 unit

# Service layer tests
.\run_tests.ps1 service

# API endpoint tests
.\run_tests.ps1 api

# Integration tests (requires DB)
.\run_tests.ps1 integration

# Google Drive tests (requires OAuth setup)
.\run_tests.ps1 gdrive

# Manual file structure tests
.\run_tests.ps1 manual

# Manual API tests (requires running server)
.\run_tests.ps1 manual-api

# All tests
.\run_tests.ps1 all

# Tests with coverage report
.\run_tests.ps1 coverage
```

### Direct pytest Commands
```bash
# Run specific test file
pytest tests/test_files_service.py -v

# Run specific test function
pytest tests/test_files_service.py::test_create_local_location -v

# Run with output (see prints)
pytest tests/test_manual_scenarios.py -v -s

# Run tests matching pattern
pytest -k "local" -v

# Run tests by marker
pytest -m integration -v

# Run with coverage
pytest tests/test_files_*.py --cov=domains.files --cov-report=html

# Skip marked tests
pytest tests/test_files_*.py -v -m "not manual"
```

## Manual Testing Scenarios

### Scenario 1: Local Folder Scanning

**Goal**: Scan a local folder and view files

**Steps**:
1. ✅ Navigate to Files → Locations
2. ✅ Click "New Location"
3. ✅ Enter:
   - Name: "Desktop Test Files"
   - Type: Local
   - Path: `C:\Users\awron\Desktop\nex-test-files`
4. ✅ Click "Create"
5. ✅ Click "Scan" on the new location
6. ✅ Verify scan result shows 3 files detected

**Expected Results**:
- 3 files detected: products.csv, customers.csv, quarterly_report.xlsx
- Scan status: "success"
- New files count: 3
- Updated files count: 0

### Scenario 2: View File Inventory

**Goal**: Browse all detected files

**Steps**:
1. ✅ Navigate to Files → Inventory
2. ✅ View list of all files
3. ✅ Check "Last Seen" timestamps
4. ✅ Verify file extensions and sizes

**Expected Results**:
- 3 files listed
- Each file shows: name, extension, location, last seen time
- All timestamps are recent (just scanned)

### Scenario 3: View CSV File Details

**Goal**: Inspect a CSV file's structure and data

**Steps**:
1. ✅ Click on "products.csv" in inventory
2. ✅ View asset details page
3. ✅ Check "Versions" section (should show 1)
4. ✅ Check "Tables" section (should show 1)
5. ✅ Click "Preview" on the table
6. ✅ Verify data preview shows 10 rows, 9 columns

**Expected Results**:
- File: products.csv
- Versions: 1
- Tables: 1 (named "products")
- Columns: product_id, name, category, price, stock_quantity, in_stock, supplier, rating, last_updated
- Rows: 10
- Data visible in preview table

### Scenario 4: View Excel Multi-Sheet File

**Goal**: Verify Excel files create multiple tables (one per sheet)

**Steps**:
1. ✅ Click on "quarterly_report.xlsx" in inventory
2. ✅ View asset details
3. ✅ Check "Tables" section (should show 3)
4. ✅ Verify table names match sheet names:
   - Sales Summary
   - Top Products
   - Customer Segments
5. ✅ Preview each table to see data

**Expected Results**:
- File: quarterly_report.xlsx
- Tables: 3
- Sheet 1: Sales Summary (3 rows, 5 columns)
- Sheet 2: Top Products (5 rows, 4 columns)
- Sheet 3: Customer Segments (4 rows, 4 columns)

### Scenario 5: Version Detection

**Goal**: Verify system detects when files change

**Steps**:
1. ✅ Open `C:\Users\awron\Desktop\nex-test-files\products.csv`
2. ✅ Change a price value (e.g., change 24.99 to 29.99)
3. ✅ Save the file
4. ✅ Return to Files → Locations
5. ✅ Click "Scan" again on the location
6. ✅ Verify scan result shows 1 updated file
7. ✅ Go to products.csv asset detail
8. ✅ Check "Versions" section (should now show 2)
9. ✅ Click on each version to compare

**Expected Results**:
- Scan detects 1 updated file
- Asset now has 2 versions
- Each version has different content hash
- Each version has different "detected_at" timestamp
- Can view/preview both versions separately

### Scenario 6: Publish to Data Explorer

**Goal**: Publish a file table to make it queryable in Data Explorer

**Steps**:
1. ✅ Go to products.csv asset detail
2. ✅ Click "Publish" on the products table
3. ✅ Enter target information:
   - Schema: public
   - Table name: products_from_files
4. ✅ Click "Publish"
5. ✅ Navigate to Data Explorer
6. ✅ Select the target database
7. ✅ Find the "products_from_files" table
8. ✅ Preview the data

**Expected Results**:
- Table published successfully
- Table appears in Data Explorer
- Data matches the CSV contents
- Can query the table with SQL

### Scenario 7: Rescan After No Changes

**Goal**: Verify efficient rescanning when files haven't changed

**Steps**:
1. ✅ Go to Files → Locations
2. ✅ Click "Scan" on existing location (without modifying files)
3. ✅ Verify scan result

**Expected Results**:
- Scan completes successfully
- New files: 0
- Updated files: 0
- All files still visible in inventory
- Last seen timestamps updated

## API Testing

### Using curl

```bash
# Base URL
BASE_URL="http://localhost:8000/api/v1/files"

# Create location
curl -X POST "$BASE_URL/locations" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Files",
    "type": "local",
    "local_path": "C:\\Users\\awron\\Desktop\\nex-test-files"
  }'

# List locations
curl "$BASE_URL/locations"

# Scan location (replace {id})
curl -X POST "$BASE_URL/locations/{id}/scan"

# List assets
curl "$BASE_URL/assets"

# Get asset detail (replace {id})
curl "$BASE_URL/assets/{id}"

# Preview table (replace {id})
curl "$BASE_URL/tables/{id}/preview"

# Publish table (replace {id})
curl -X POST "$BASE_URL/tables/{id}/publish" \
  -H "Content-Type: application/json" \
  -d '{
    "target_schema": "public",
    "target_table_name": "published_table"
  }'

# Get Google Drive auth URL
curl "$BASE_URL/gdrive/auth/url"

# List Google accounts
curl "$BASE_URL/gdrive/accounts"
```

### Using Python requests
```python
import requests

BASE_URL = "http://localhost:8000/api/v1/files"

# Create location
response = requests.post(
    f"{BASE_URL}/locations",
    json={
        "name": "Test Files",
        "type": "local",
        "local_path": r"C:\Users\awron\Desktop\nex-test-files"
    }
)
location = response.json()
print(f"Created location: {location['id']}")

# Scan
response = requests.post(f"{BASE_URL}/locations/{location['id']}/scan")
print(f"Scan result: {response.json()}")

# List assets
response = requests.get(f"{BASE_URL}/assets")
assets = response.json()
print(f"Found {len(assets)} assets")

# Get first asset detail
if assets:
    asset_id = assets[0]["id"]
    response = requests.get(f"{BASE_URL}/assets/{asset_id}")
    detail = response.json()
    print(f"Asset: {detail['asset']['file_name']}")
    print(f"  Versions: {len(detail['versions'])}")
    print(f"  Tables: {len(detail['tables'])}")
```

## Test Data Details

### products.csv
- **Rows**: 10 products
- **Columns**: 9
  - `product_id` (string): P001-P010
  - `name` (string): Product names
  - `category` (string): Electronics, Accessories, Furniture, Storage
  - `price` (float): 12.99 to 349.99
  - `stock_quantity` (int): 0 to 500
  - `in_stock` (bool): TRUE/FALSE
  - `supplier` (string): Supplier names (some null)
  - `rating` (float): 4.1 to 4.9 (some null)
  - `last_updated` (date): 2024-01-10 to 2024-01-20
- **Size**: ~800 bytes

### customers.csv
- **Rows**: 15 customers
- **Columns**: 7
  - `customer_id` (string): C001-C015
  - `name` (string): Customer names
  - `email` (string): Email addresses
  - `country` (string): USA, Canada, UK, Germany, Australia
  - `signup_date` (date): 2022-2023
  - `total_purchases` (int): 2 to 45
  - `lifetime_value` (float): 150.00 to 8500.00
- **Size**: ~1000 bytes

### quarterly_report.xlsx
- **Sheets**: 3
- **Sheet 1: Sales Summary**
  - Rows: 3 (Jan, Feb, Mar)
  - Columns: Month, Revenue, Orders, Avg_Order_Value, Growth_Percent
- **Sheet 2: Top Products**
  - Rows: 5 products
  - Columns: Rank, Product, Units_Sold, Revenue
- **Sheet 3: Customer Segments**
  - Rows: 4 segments
  - Columns: Segment, Customer_Count, Avg_Purchase, Retention_Rate
- **Size**: ~5-6 KB

## Troubleshooting

### Tests Fail with Database Errors
```powershell
# Ensure Postgres is running
docker-compose -f docker-compose.dev.yml up -d db

# Run migrations
cd backend
alembic upgrade head

# Restart backend
docker-compose -f docker-compose.dev.yml restart backend
```

### Tests Fail with Import Errors
```powershell
# Install test dependencies
cd backend
pip install -r requirements-test.txt
```

### Manual Tests Can't Find Files
```powershell
# Verify test files exist
dir C:\Users\awron\Desktop\nex-test-files

# Expected output:
# products.csv
# customers.csv
# quarterly_report.xlsx
```

### API Tests Timeout
```powershell
# Check backend is running
docker ps | findstr nex-backend

# Check logs
docker logs nex-backend-dev

# Restart if needed
docker-compose -f docker-compose.dev.yml restart backend
```

### Excel Files Not Parsing
```powershell
# Ensure openpyxl is installed
docker exec nex-backend-dev pip show openpyxl

# If not installed
docker exec nex-backend-dev pip install openpyxl xlrd
```

## Test Coverage Report

Generate HTML coverage report:
```powershell
cd backend
pytest tests/test_files_*.py --cov=domains.files --cov-report=html
```

Open `backend/htmlcov/index.html` in browser to view detailed coverage.

## Continuous Integration

For CI/CD pipelines, use:
```bash
# Run fast tests only (no integration/manual)
pytest tests/test_files_*.py -v -m "not integration and not manual"

# Run with coverage for reporting
pytest tests/test_files_*.py --cov=domains.files --cov-report=xml --cov-report=term

# Upload coverage to service (e.g., Codecov)
codecov -f coverage.xml
```

## Next Steps

After testing:
1. ✅ Verify all scenarios pass
2. ✅ Check test coverage (aim for 85%+)
3. ✅ Document any issues found
4. ✅ Test Google Drive integration (requires OAuth setup)
5. ✅ Test with larger files (100+ rows, multiple sheets)
6. ✅ Test edge cases (empty files, corrupted files, etc.)

## Questions?

- Check `backend/tests/README_TESTING.md` for detailed test documentation
- Review test files in `backend/tests/test_files_*.py` for examples
- Check pytest docs: https://docs.pytest.org
- Check FastAPI testing docs: https://fastapi.tiangolo.com/tutorial/testing/
