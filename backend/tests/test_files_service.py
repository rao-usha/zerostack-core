"""Tests for Files service layer."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from datetime import datetime, timezone
from sqlmodel import Session, create_engine, SQLModel
from sqlalchemy.pool import StaticPool
import tempfile
import os

from domains.files.service import FilesService
from domains.files.models import (
    FileLocation,
    FileAsset,
    FileVersion,
    FileTable,
    LocationType,
    FileLocationCreate,
)


@pytest.fixture(name="session")
def session_fixture():
    """Create a test database session."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture
def mock_gdrive_connector():
    """Create a mock Google Drive connector."""
    return Mock()


@pytest.fixture
def service(session: Session, mock_gdrive_connector):
    """Create a FilesService instance."""
    return FilesService(db=session, gdrive_connector=mock_gdrive_connector)


@pytest.fixture
def temp_test_folder():
    """Create a temporary folder with test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test CSV file
        csv_path = Path(tmpdir) / "test.csv"
        csv_path.write_text("col1,col2,col3\n1,2,3\n4,5,6\n")
        
        # Create test Excel file (simple CSV-like for testing)
        xlsx_path = Path(tmpdir) / "test.xlsx"
        # We'll mock pandas reading, so just create an empty file
        xlsx_path.write_text("")
        
        # Create nested folder
        subdir = Path(tmpdir) / "subfolder"
        subdir.mkdir()
        nested_csv = subdir / "nested.csv"
        nested_csv.write_text("a,b\n1,2\n")
        
        yield tmpdir


def test_create_local_location(service: FilesService):
    """Test creating a local file location."""
    location_data = FileLocationCreate(
        name="Test Local",
        type=LocationType.LOCAL,
        local_path="/test/path",
    )
    
    location = service.create_location(location_data)
    
    assert location.id is not None
    assert location.name == "Test Local"
    assert location.type == LocationType.LOCAL
    assert location.local_path == "/test/path"
    assert location.is_active is True


def test_create_gdrive_location(service: FilesService):
    """Test creating a Google Drive location."""
    location_data = FileLocationCreate(
        name="Test GDrive",
        type=LocationType.GDRIVE,
        gdrive_folder_id="1A2B3C",
        external_account_id="account-123",
    )
    
    location = service.create_location(location_data)
    
    assert location.id is not None
    assert location.type == LocationType.GDRIVE
    assert location.gdrive_folder_id == "1A2B3C"


def test_list_locations(service: FilesService):
    """Test listing file locations."""
    # Create multiple locations
    service.create_location(
        FileLocationCreate(name="Loc1", type=LocationType.LOCAL, local_path="/a")
    )
    service.create_location(
        FileLocationCreate(name="Loc2", type=LocationType.LOCAL, local_path="/b")
    )
    
    locations = service.list_locations()
    
    assert len(locations) == 2
    assert locations[0].name == "Loc1"
    assert locations[1].name == "Loc2"


def test_get_location(service: FilesService):
    """Test getting a single location by ID."""
    created = service.create_location(
        FileLocationCreate(name="Test", type=LocationType.LOCAL, local_path="/test")
    )
    
    retrieved = service.get_location(created.id)
    
    assert retrieved is not None
    assert retrieved.id == created.id
    assert retrieved.name == "Test"


def test_get_nonexistent_location_returns_none(service: FilesService):
    """Test getting a non-existent location returns None."""
    from uuid import uuid4
    
    result = service.get_location(str(uuid4()))
    
    assert result is None


@patch("domains.files.service.Path")
@patch("domains.files.service.pd")
def test_scan_local_location_with_csv(mock_pd, mock_path, service: FilesService, temp_test_folder):
    """Test scanning a local folder with CSV files."""
    # Create location
    location = service.create_location(
        FileLocationCreate(
            name="Test Scan",
            type=LocationType.LOCAL,
            local_path=str(temp_test_folder),
        )
    )
    
    # Mock Path.glob to return our test files
    mock_path_instance = MagicMock()
    mock_path.return_value = mock_path_instance
    
    test_csv = Path(temp_test_folder) / "test.csv"
    mock_path_instance.rglob.return_value = [test_csv]
    
    # Mock pandas read_csv
    mock_df = MagicMock()
    mock_df.columns = ["col1", "col2", "col3"]
    mock_df.__len__.return_value = 2
    mock_df.head.return_value = mock_df
    mock_df.dtypes = {"col1": "int64", "col2": "int64", "col3": "int64"}
    mock_pd.read_csv.return_value = mock_df
    
    # Mock file stats
    with patch.object(Path, "stat") as mock_stat:
        mock_stat.return_value.st_mtime = datetime.now(timezone.utc).timestamp()
        mock_stat.return_value.st_size = 100
        
        with patch.object(Path, "read_bytes", return_value=b"test data"):
            result = service.scan_location(str(location.id))
    
    assert result["status"] == "success"
    assert result["new_files"] >= 0
    assert result["updated_files"] >= 0


def test_list_assets(service: FilesService):
    """Test listing file assets."""
    # Create location
    location = service.create_location(
        FileLocationCreate(name="Test", type=LocationType.LOCAL, local_path="/test")
    )
    
    # Manually create an asset for testing
    asset = FileAsset(
        location_id=location.id,
        relative_path="test.csv",
        file_name="test.csv",
        ext=".csv",
        last_seen_at=datetime.now(timezone.utc),
    )
    service.db.add(asset)
    service.db.commit()
    
    assets = service.list_assets(location_id=str(location.id))
    
    assert len(assets) > 0
    assert assets[0].file_name == "test.csv"


def test_get_asset_detail(service: FilesService):
    """Test getting asset detail."""
    # Create location and asset
    location = service.create_location(
        FileLocationCreate(name="Test", type=LocationType.LOCAL, local_path="/test")
    )
    
    asset = FileAsset(
        location_id=location.id,
        relative_path="test.csv",
        file_name="test.csv",
        ext=".csv",
        last_seen_at=datetime.now(timezone.utc),
    )
    service.db.add(asset)
    service.db.commit()
    service.db.refresh(asset)
    
    detail = service.get_asset_detail(str(asset.id))
    
    assert detail is not None
    assert detail["asset"]["file_name"] == "test.csv"
    assert "versions" in detail
    assert "tables" in detail


@patch("domains.files.service.GoogleDriveConnector")
def test_scan_gdrive_location(mock_connector_class, service: FilesService):
    """Test scanning a Google Drive location."""
    # Setup mock connector
    mock_connector = MagicMock()
    mock_connector.list_files_in_folder.return_value = [
        {
            "id": "file123",
            "name": "test.csv",
            "mimeType": "text/csv",
            "modifiedTime": "2024-01-01T00:00:00.000Z",
            "size": "1024",
        }
    ]
    mock_connector.download_file.return_value = Path("/tmp/cached_file.csv")
    service.gdrive_connector = mock_connector
    
    # Create GDrive location
    location = service.create_location(
        FileLocationCreate(
            name="Test GDrive",
            type=LocationType.GDRIVE,
            gdrive_folder_id="folder123",
            external_account_id="account123",
        )
    )
    
    # Mock file parsing
    with patch("domains.files.service.pd.read_csv") as mock_read_csv:
        mock_df = MagicMock()
        mock_df.columns = ["col1", "col2"]
        mock_df.__len__.return_value = 10
        mock_df.head.return_value = mock_df
        mock_df.dtypes = {"col1": "int64", "col2": "string"}
        mock_read_csv.return_value = mock_df
        
        result = service.scan_location(str(location.id))
    
    assert result["status"] == "success"
    mock_connector.list_files_in_folder.assert_called_once()


def test_compute_file_hash(service: FilesService):
    """Test file hash computation."""
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(b"test content")
        f.flush()
        temp_path = f.name
    
    try:
        hash1 = service._compute_file_hash(Path(temp_path))
        hash2 = service._compute_file_hash(Path(temp_path))
        
        # Same file should produce same hash
        assert hash1 == hash2
        
        # Hash should be SHA256 hex (64 chars)
        assert len(hash1) == 64
    finally:
        os.unlink(temp_path)


def test_infer_schema_from_dataframe(service: FilesService):
    """Test schema inference from pandas DataFrame."""
    import pandas as pd
    
    df = pd.DataFrame({
        "int_col": [1, 2, 3],
        "str_col": ["a", "b", "c"],
        "float_col": [1.1, 2.2, 3.3],
    })
    
    schema = service._infer_schema_from_df(df)
    
    assert "columns" in schema
    assert len(schema["columns"]) == 3
    
    col_names = [col["name"] for col in schema["columns"]]
    assert "int_col" in col_names
    assert "str_col" in col_names
    assert "float_col" in col_names
