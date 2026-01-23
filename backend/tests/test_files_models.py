"""Tests for Files domain models."""
import pytest
from datetime import datetime, timezone
from sqlmodel import Session, create_engine, SQLModel
from sqlalchemy.pool import StaticPool

from domains.files.models import (
    FileLocation,
    FileAsset,
    FileVersion,
    FileTable,
    ExternalAccount,
    LocationType,
    AuthProvider,
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


def test_create_local_file_location(session: Session):
    """Test creating a local file location."""
    location = FileLocation(
        name="Test Local Folder",
        type=LocationType.LOCAL,
        local_path="/path/to/folder",
        is_active=True,
    )
    session.add(location)
    session.commit()
    session.refresh(location)

    assert location.id is not None
    assert location.name == "Test Local Folder"
    assert location.type == LocationType.LOCAL
    assert location.local_path == "/path/to/folder"
    assert location.gdrive_folder_id is None
    assert location.is_active is True
    assert location.created_at is not None
    assert location.updated_at is not None


def test_create_gdrive_file_location(session: Session):
    """Test creating a Google Drive file location."""
    # First create an external account
    account = ExternalAccount(
        provider=AuthProvider.GOOGLE,
        account_email="test@example.com",
        scopes="https://www.googleapis.com/auth/drive.readonly",
        access_token_encrypted="encrypted_access_token",
        refresh_token_encrypted="encrypted_refresh_token",
    )
    session.add(account)
    session.commit()
    session.refresh(account)

    location = FileLocation(
        name="Test GDrive Folder",
        type=LocationType.GDRIVE,
        gdrive_folder_id="1A2B3C4D5E",
        gdrive_include_shared_drives=True,
        gdrive_account_email="test@example.com",
        external_account_id=account.id,
        is_active=True,
    )
    session.add(location)
    session.commit()
    session.refresh(location)

    assert location.id is not None
    assert location.type == LocationType.GDRIVE
    assert location.gdrive_folder_id == "1A2B3C4D5E"
    assert location.gdrive_include_shared_drives is True
    assert location.local_path is None
    assert location.external_account_id == account.id


def test_file_asset_creation(session: Session):
    """Test creating a file asset."""
    location = FileLocation(
        name="Test Location",
        type=LocationType.LOCAL,
        local_path="/test",
        is_active=True,
    )
    session.add(location)
    session.commit()

    asset = FileAsset(
        location_id=location.id,
        relative_path="subdir/test.csv",
        file_name="test.csv",
        ext=".csv",
        mime_type="text/csv",
        last_seen_at=datetime.now(timezone.utc),
    )
    session.add(asset)
    session.commit()
    session.refresh(asset)

    assert asset.id is not None
    assert asset.location_id == location.id
    assert asset.file_name == "test.csv"
    assert asset.ext == ".csv"


def test_file_version_creation(session: Session):
    """Test creating a file version."""
    location = FileLocation(
        name="Test", type=LocationType.LOCAL, local_path="/test", is_active=True
    )
    session.add(location)
    session.commit()

    asset = FileAsset(
        location_id=location.id,
        relative_path="test.csv",
        file_name="test.csv",
        ext=".csv",
        last_seen_at=datetime.now(timezone.utc),
    )
    session.add(asset)
    session.commit()

    version = FileVersion(
        file_asset_id=asset.id,
        detected_at=datetime.now(timezone.utc),
        modified_at=datetime.now(timezone.utc),
        size_bytes=1024,
        content_hash="abc123def456",
        row_count_estimate=100,
    )
    session.add(version)
    session.commit()
    session.refresh(version)

    assert version.id is not None
    assert version.file_asset_id == asset.id
    assert version.size_bytes == 1024
    assert version.content_hash == "abc123def456"
    assert version.row_count_estimate == 100


def test_file_table_creation(session: Session):
    """Test creating a file table."""
    location = FileLocation(
        name="Test", type=LocationType.LOCAL, local_path="/test", is_active=True
    )
    session.add(location)
    session.commit()

    asset = FileAsset(
        location_id=location.id,
        relative_path="test.xlsx",
        file_name="test.xlsx",
        ext=".xlsx",
        last_seen_at=datetime.now(timezone.utc),
    )
    session.add(asset)
    session.commit()

    version = FileVersion(
        file_asset_id=asset.id,
        detected_at=datetime.now(timezone.utc),
        modified_at=datetime.now(timezone.utc),
        size_bytes=2048,
        content_hash="xyz789",
    )
    session.add(version)
    session.commit()

    table = FileTable(
        file_version_id=version.id,
        table_name="Sheet1",
        sheet_name="Sheet1",
        row_count=50,
        col_count=10,
        schema_json={"columns": [{"name": "col1", "type": "string"}]},
    )
    session.add(table)
    session.commit()
    session.refresh(table)

    assert table.id is not None
    assert table.file_version_id == version.id
    assert table.table_name == "Sheet1"
    assert table.row_count == 50
    assert table.col_count == 10


def test_external_account_creation(session: Session):
    """Test creating an external account."""
    account = ExternalAccount(
        provider=AuthProvider.GOOGLE,
        account_email="user@gmail.com",
        scopes="https://www.googleapis.com/auth/drive.readonly",
        access_token_encrypted="enc_access",
        refresh_token_encrypted="enc_refresh",
        token_expiry=datetime.now(timezone.utc),
    )
    session.add(account)
    session.commit()
    session.refresh(account)

    assert account.id is not None
    assert account.provider == AuthProvider.GOOGLE
    assert account.account_email == "user@gmail.com"
    assert account.access_token_encrypted == "enc_access"
    assert account.refresh_token_encrypted == "enc_refresh"


def test_file_asset_cascade_relationships(session: Session):
    """Test that deleting a location cascades to assets."""
    location = FileLocation(
        name="Test", type=LocationType.LOCAL, local_path="/test", is_active=True
    )
    session.add(location)
    session.commit()

    asset = FileAsset(
        location_id=location.id,
        relative_path="test.csv",
        file_name="test.csv",
        ext=".csv",
        last_seen_at=datetime.now(timezone.utc),
    )
    session.add(asset)
    session.commit()

    asset_id = asset.id

    # Delete location
    session.delete(location)
    session.commit()

    # Asset should also be deleted (cascade)
    result = session.get(FileAsset, asset_id)
    assert result is None
