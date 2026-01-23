"""Manual test scenarios for Files feature with real test files.

These tests are designed to be run manually against the actual application
using the test files in C:\\Users\\awron\\Desktop\\nex-test-files\\.

Run with: pytest tests/test_manual_scenarios.py -v -s
(The -s flag shows print output)
"""
import pytest
from pathlib import Path
import sys

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))


# Mark all tests in this module as manual
pytestmark = [pytest.mark.manual, pytest.mark.skip(reason="Manual tests - run explicitly")]


TEST_FILES_PATH = r"C:\Users\awron\Desktop\nex-test-files"


def test_files_exist():
    """Verify test files exist before running other tests."""
    test_folder = Path(TEST_FILES_PATH)
    
    assert test_folder.exists(), f"Test folder not found: {TEST_FILES_PATH}"
    
    expected_files = [
        "products.csv",
        "customers.csv",
        "quarterly_report.xlsx",
    ]
    
    for filename in expected_files:
        file_path = test_folder / filename
        assert file_path.exists(), f"Test file not found: {filename}"
        print(f"✓ Found: {filename} ({file_path.stat().st_size} bytes)")


def test_products_csv_structure():
    """Verify products.csv has expected structure."""
    import pandas as pd
    
    csv_path = Path(TEST_FILES_PATH) / "products.csv"
    df = pd.read_csv(csv_path)
    
    # Check row count
    assert len(df) == 10, f"Expected 10 rows, got {len(df)}"
    print(f"✓ products.csv has 10 rows")
    
    # Check column count
    assert len(df.columns) == 9, f"Expected 9 columns, got {len(df.columns)}"
    print(f"✓ products.csv has 9 columns")
    
    # Check expected columns
    expected_columns = [
        "product_id", "name", "category", "price", "stock_quantity",
        "in_stock", "supplier", "rating", "last_updated"
    ]
    for col in expected_columns:
        assert col in df.columns, f"Missing column: {col}"
    print(f"✓ All expected columns present")
    
    # Check data types
    assert df["price"].dtype == "float64", "Price should be float"
    assert df["stock_quantity"].dtype == "int64", "Stock should be int"
    print(f"✓ Data types correct")
    
    # Check for missing values in specific columns
    nullable_columns = ["supplier", "rating"]
    for col in df.columns:
        if col not in nullable_columns:
            non_null = df[col].notna().sum()
            print(f"  {col}: {non_null}/{len(df)} non-null values")


def test_customers_csv_structure():
    """Verify customers.csv has expected structure."""
    import pandas as pd
    
    csv_path = Path(TEST_FILES_PATH) / "customers.csv"
    df = pd.read_csv(csv_path)
    
    assert len(df) == 15, f"Expected 15 rows, got {len(df)}"
    print(f"✓ customers.csv has 15 rows")
    
    assert len(df.columns) == 7, f"Expected 7 columns, got {len(df.columns)}"
    print(f"✓ customers.csv has 7 columns")
    
    expected_columns = [
        "customer_id", "name", "email", "country",
        "signup_date", "total_purchases", "lifetime_value"
    ]
    for col in expected_columns:
        assert col in df.columns, f"Missing column: {col}"
    print(f"✓ All expected columns present")
    
    # Check email format (basic)
    assert df["email"].str.contains("@").all(), "All emails should contain @"
    print(f"✓ Email format valid")


def test_quarterly_report_xlsx_structure():
    """Verify quarterly_report.xlsx has expected sheets and structure."""
    import pandas as pd
    
    xlsx_path = Path(TEST_FILES_PATH) / "quarterly_report.xlsx"
    
    # Read all sheets
    excel_file = pd.ExcelFile(xlsx_path)
    sheet_names = excel_file.sheet_names
    
    expected_sheets = ["Sales Summary", "Top Products", "Customer Segments"]
    assert len(sheet_names) == 3, f"Expected 3 sheets, got {len(sheet_names)}"
    print(f"✓ Excel file has 3 sheets")
    
    for sheet_name in expected_sheets:
        assert sheet_name in sheet_names, f"Missing sheet: {sheet_name}"
    print(f"✓ All expected sheets present: {sheet_names}")
    
    # Check Sales Summary sheet
    sales_df = pd.read_excel(xlsx_path, sheet_name="Sales Summary")
    assert len(sales_df) == 3, "Sales Summary should have 3 rows"
    assert len(sales_df.columns) == 5, "Sales Summary should have 5 columns"
    print(f"✓ Sales Summary: {len(sales_df)} rows, {len(sales_df.columns)} columns")
    
    # Check Top Products sheet
    products_df = pd.read_excel(xlsx_path, sheet_name="Top Products")
    assert len(products_df) == 5, "Top Products should have 5 rows"
    assert len(products_df.columns) == 4, "Top Products should have 4 columns"
    print(f"✓ Top Products: {len(products_df)} rows, {len(products_df.columns)} columns")
    
    # Check Customer Segments sheet
    segments_df = pd.read_excel(xlsx_path, sheet_name="Customer Segments")
    assert len(segments_df) == 4, "Customer Segments should have 4 rows"
    assert len(segments_df.columns) == 4, "Customer Segments should have 4 columns"
    print(f"✓ Customer Segments: {len(segments_df)} rows, {len(segments_df.columns)} columns")


@pytest.mark.requires_api
def test_api_scan_local_folder():
    """Test scanning the local test folder via API.
    
    Prerequisites:
    - Backend must be running (docker-compose -f docker-compose.dev.yml up -d)
    - Database must be initialized (alembic upgrade head)
    """
    import requests
    
    BASE_URL = "http://localhost:8000/api/v1/files"
    
    # Step 1: Create location
    location_payload = {
        "name": "Manual Test Files",
        "type": "local",
        "local_path": TEST_FILES_PATH,
    }
    
    response = requests.post(f"{BASE_URL}/locations", json=location_payload)
    assert response.status_code in [200, 201], f"Failed to create location: {response.text}"
    location = response.json()
    location_id = location["id"]
    print(f"✓ Created location: {location_id}")
    
    # Step 2: Scan location
    response = requests.post(f"{BASE_URL}/locations/{location_id}/scan")
    assert response.status_code == 200, f"Failed to scan: {response.text}"
    scan_result = response.json()
    print(f"✓ Scan result: {scan_result}")
    assert scan_result["status"] == "success"
    assert scan_result["new_files"] >= 3, "Should detect at least 3 files"
    
    # Step 3: List assets
    response = requests.get(f"{BASE_URL}/assets", params={"location_id": location_id})
    assert response.status_code == 200
    assets = response.json()
    print(f"✓ Found {len(assets)} assets")
    assert len(assets) >= 3
    
    # Step 4: Get products.csv detail
    products_asset = next((a for a in assets if a["file_name"] == "products.csv"), None)
    assert products_asset is not None, "products.csv not found in assets"
    
    response = requests.get(f"{BASE_URL}/assets/{products_asset['id']}")
    assert response.status_code == 200
    detail = response.json()
    print(f"✓ products.csv detail: {len(detail['versions'])} version(s), {len(detail['tables'])} table(s)")
    
    # Step 5: Preview products table
    assert len(detail["tables"]) >= 1, "Should have at least 1 table"
    table_id = detail["tables"][0]["id"]
    
    response = requests.get(f"{BASE_URL}/tables/{table_id}/preview")
    assert response.status_code == 200
    preview = response.json()
    print(f"✓ Preview: {len(preview['columns'])} columns, {len(preview['rows'])} rows")
    assert len(preview["columns"]) == 9
    assert len(preview["rows"]) == 10
    
    # Step 6: Check Excel multi-sheet
    excel_asset = next((a for a in assets if a["file_name"] == "quarterly_report.xlsx"), None)
    if excel_asset:
        response = requests.get(f"{BASE_URL}/assets/{excel_asset['id']}")
        excel_detail = response.json()
        print(f"✓ quarterly_report.xlsx: {len(excel_detail['tables'])} table(s)")
        
        # Should have 3 tables (one per sheet)
        assert len(excel_detail["tables"]) == 3, "Excel should have 3 tables (sheets)"
        
        table_names = [t["table_name"] for t in excel_detail["tables"]]
        print(f"  Table names: {table_names}")


@pytest.mark.requires_api
def test_api_version_detection():
    """Test that rescanning detects file changes.
    
    Prerequisites: Same as test_api_scan_local_folder
    """
    import requests
    import time
    
    BASE_URL = "http://localhost:8000/api/v1/files"
    
    # Create and scan location
    location_payload = {
        "name": "Version Test",
        "type": "local",
        "local_path": TEST_FILES_PATH,
    }
    
    response = requests.post(f"{BASE_URL}/locations", json=location_payload)
    location = response.json()
    location_id = location["id"]
    
    # First scan
    response = requests.post(f"{BASE_URL}/locations/{location_id}/scan")
    scan1 = response.json()
    print(f"✓ First scan: {scan1}")
    
    # Wait a bit to ensure timestamp difference
    time.sleep(2)
    
    # Modify products.csv
    csv_path = Path(TEST_FILES_PATH) / "products.csv"
    original_content = csv_path.read_text()
    try:
        # Add a new row
        modified_content = original_content + "P011,New Product,Electronics,99.99,50,TRUE,NewSupplier,5.0,2024-01-21\n"
        csv_path.write_text(modified_content)
        print("✓ Modified products.csv")
        
        # Wait to ensure file modified time is different
        time.sleep(1)
        
        # Second scan
        response = requests.post(f"{BASE_URL}/locations/{location_id}/scan")
        scan2 = response.json()
        print(f"✓ Second scan: {scan2}")
        
        # Should detect the change
        assert scan2["updated_files"] >= 1, "Should detect at least 1 updated file"
        print("✓ Version change detected!")
        
    finally:
        # Restore original file
        csv_path.write_text(original_content)
        print("✓ Restored original products.csv")


def test_print_test_file_summary():
    """Print a summary of all test files for documentation."""
    import pandas as pd
    
    print("\n" + "="*60)
    print("TEST FILES SUMMARY")
    print("="*60)
    
    # Products CSV
    print("\n📄 products.csv")
    print("-" * 40)
    products_df = pd.read_csv(Path(TEST_FILES_PATH) / "products.csv")
    print(f"  Rows: {len(products_df)}")
    print(f"  Columns: {len(products_df.columns)}")
    print(f"  Columns: {', '.join(products_df.columns)}")
    print(f"  Size: {Path(TEST_FILES_PATH).joinpath('products.csv').stat().st_size} bytes")
    
    # Customers CSV
    print("\n📄 customers.csv")
    print("-" * 40)
    customers_df = pd.read_csv(Path(TEST_FILES_PATH) / "customers.csv")
    print(f"  Rows: {len(customers_df)}")
    print(f"  Columns: {len(customers_df.columns)}")
    print(f"  Columns: {', '.join(customers_df.columns)}")
    print(f"  Size: {Path(TEST_FILES_PATH).joinpath('customers.csv').stat().st_size} bytes")
    
    # Quarterly Report Excel
    print("\n📄 quarterly_report.xlsx")
    print("-" * 40)
    excel_file = pd.ExcelFile(Path(TEST_FILES_PATH) / "quarterly_report.xlsx")
    print(f"  Sheets: {len(excel_file.sheet_names)}")
    for sheet_name in excel_file.sheet_names:
        df = pd.read_excel(excel_file, sheet_name=sheet_name)
        print(f"    • {sheet_name}: {len(df)} rows, {len(df.columns)} columns")
    print(f"  Size: {Path(TEST_FILES_PATH).joinpath('quarterly_report.xlsx').stat().st_size} bytes")
    
    print("\n" + "="*60)


if __name__ == "__main__":
    """Run specific tests when script is executed directly."""
    print("Running manual test scenarios...")
    print(f"Test files location: {TEST_FILES_PATH}\n")
    
    try:
        test_files_exist()
        print("\n✅ Files exist check passed\n")
        
        test_products_csv_structure()
        print("\n✅ products.csv structure check passed\n")
        
        test_customers_csv_structure()
        print("\n✅ customers.csv structure check passed\n")
        
        test_quarterly_report_xlsx_structure()
        print("\n✅ quarterly_report.xlsx structure check passed\n")
        
        test_print_test_file_summary()
        
        print("\n" + "="*60)
        print("✅ ALL MANUAL TESTS PASSED!")
        print("="*60)
        print("\nTo test API functionality, run:")
        print("  pytest tests/test_manual_scenarios.py::test_api_scan_local_folder -v -s")
        print("  pytest tests/test_manual_scenarios.py::test_api_version_detection -v -s")
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
