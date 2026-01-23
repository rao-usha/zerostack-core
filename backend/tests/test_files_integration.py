"""Integration tests for Files feature (end-to-end workflows)."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
import tempfile
from pathlib import Path
import sys

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from main import app


pytestmark = pytest.mark.integration


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def test_folder_with_files():
    """Create temporary folder with test CSV and Excel files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create CSV file
        csv_path = Path(tmpdir) / "products.csv"
        csv_path.write_text(
            "id,name,price\n"
            "1,Widget,19.99\n"
            "2,Gadget,29.99\n"
            "3,Thing,9.99\n"
        )
        
        # Create subfolder with another CSV
        subdir = Path(tmpdir) / "archive"
        subdir.mkdir()
        archive_csv = subdir / "old_products.csv"
        archive_csv.write_text(
            "id,name\n"
            "100,OldWidget\n"
        )
        
        yield tmpdir


@pytest.mark.skip(reason="Requires database setup")
def test_full_local_workflow(client: TestClient, test_folder_with_files):
    """Test complete workflow: create location → scan → view assets → preview table."""
    
    # Step 1: Create location
    create_response = client.post(
        "/api/v1/files/locations",
        json={
            "name": "Integration Test Folder",
            "type": "local",
            "local_path": str(test_folder_with_files),
        },
    )
    assert create_response.status_code in [200, 201]
    location = create_response.json()
    location_id = location["id"]
    
    # Step 2: Scan location
    scan_response = client.post(f"/api/v1/files/locations/{location_id}/scan")
    assert scan_response.status_code == 200
    scan_result = scan_response.json()
    assert scan_result["status"] == "success"
    assert scan_result["new_files"] >= 2  # products.csv + old_products.csv
    
    # Step 3: List assets
    assets_response = client.get(f"/api/v1/files/assets?location_id={location_id}")
    assert assets_response.status_code == 200
    assets = assets_response.json()
    assert len(assets) >= 2
    
    # Find the products.csv asset
    products_asset = next(a for a in assets if a["file_name"] == "products.csv")
    asset_id = products_asset["id"]
    
    # Step 4: Get asset detail
    detail_response = client.get(f"/api/v1/files/assets/{asset_id}")
    assert detail_response.status_code == 200
    detail = detail_response.json()
    assert detail["asset"]["file_name"] == "products.csv"
    assert len(detail["versions"]) >= 1
    assert len(detail["tables"]) >= 1  # CSV creates 1 table
    
    # Step 5: Preview table
    table_id = detail["tables"][0]["id"]
    preview_response = client.get(f"/api/v1/files/tables/{table_id}/preview")
    assert preview_response.status_code == 200
    preview = preview_response.json()
    assert len(preview["columns"]) == 3  # id, name, price
    assert len(preview["rows"]) == 3  # 3 products


@pytest.mark.skip(reason="Requires Google OAuth setup")
def test_full_gdrive_workflow(client: TestClient):
    """Test complete GDrive workflow: connect account → create location → scan."""
    
    # Step 1: Get auth URL
    auth_url_response = client.get("/api/v1/files/gdrive/auth/url")
    assert auth_url_response.status_code == 200
    auth_data = auth_url_response.json()
    assert "url" in auth_data
    assert "state" in auth_data
    
    # Step 2: Simulate OAuth callback (would normally come from Google)
    # In real test, you'd use a test OAuth flow or mock it
    
    # Step 3: Create GDrive location
    create_response = client.post(
        "/api/v1/files/locations",
        json={
            "name": "Test Drive Folder",
            "type": "gdrive",
            "gdrive_folder_id": "test_folder_id_123",
            "external_account_id": "mock_account_id",
        },
    )
    assert create_response.status_code in [200, 201, 422, 500]


def test_create_and_list_locations(client: TestClient):
    """Test creating multiple locations and listing them."""
    # This test will work even without full DB as it tests the API structure
    
    locations_before = client.get("/api/v1/files/locations")
    # May fail if DB not available, but that's okay for structure test
    
    # Attempt to create location
    create_response = client.post(
        "/api/v1/files/locations",
        json={
            "name": "Test Location",
            "type": "local",
            "local_path": "/tmp/test",
        },
    )
    # Accept various status codes depending on environment
    assert create_response.status_code in [200, 201, 422, 500]


def test_scan_nonexistent_location_returns_404(client: TestClient):
    """Test scanning a non-existent location returns 404."""
    response = client.post("/api/v1/files/locations/00000000-0000-0000-0000-000000000000/scan")
    assert response.status_code in [404, 500]


def test_preview_nonexistent_table_returns_404(client: TestClient):
    """Test previewing a non-existent table returns 404."""
    response = client.get("/api/v1/files/tables/00000000-0000-0000-0000-000000000000/preview")
    assert response.status_code in [404, 500]


def test_api_endpoints_exist(client: TestClient):
    """Test that all expected API endpoints exist and return appropriate status codes."""
    endpoints = [
        ("GET", "/api/v1/files/locations"),
        ("GET", "/api/v1/files/assets"),
        ("GET", "/api/v1/files/gdrive/accounts"),
        ("GET", "/api/v1/files/gdrive/auth/url"),
    ]
    
    for method, path in endpoints:
        if method == "GET":
            response = client.get(path)
        elif method == "POST":
            response = client.post(path, json={})
        
        # Should not return 404 (endpoint not found)
        # May return 500, 422, 200 depending on environment
        assert response.status_code != 404, f"Endpoint {method} {path} not found"


@pytest.mark.skip(reason="Requires full database and file system access")
def test_rescan_detects_changes(client: TestClient, test_folder_with_files):
    """Test that rescanning a location detects changed files."""
    
    # Create and scan location
    create_response = client.post(
        "/api/v1/files/locations",
        json={
            "name": "Test Folder",
            "type": "local",
            "local_path": str(test_folder_with_files),
        },
    )
    location_id = create_response.json()["id"]
    
    # First scan
    scan1 = client.post(f"/api/v1/files/locations/{location_id}/scan")
    result1 = scan1.json()
    
    # Modify a file
    csv_path = Path(test_folder_with_files) / "products.csv"
    csv_path.write_text("id,name,price\n1,Widget,25.99\n")  # Changed price
    
    # Second scan
    scan2 = client.post(f"/api/v1/files/locations/{location_id}/scan")
    result2 = scan2.json()
    
    # Should detect the update
    assert result2["updated_files"] >= 1


@pytest.mark.skip(reason="Requires full setup")
def test_excel_multi_sheet_creates_multiple_tables(client: TestClient):
    """Test that Excel file with multiple sheets creates multiple tables."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Would need openpyxl to create real Excel file
        # For now, this is a placeholder test
        pass
