"""Tests for Google Drive connector."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone
from pathlib import Path

from domains.files.gdrive_connector import GoogleDriveConnector
from domains.files.encryption import TokenEncryption


@pytest.fixture
def encryption():
    """Create encryption instance."""
    return TokenEncryption("test-key")


@pytest.fixture
def connector(encryption):
    """Create GoogleDriveConnector with mocks."""
    with patch("domains.files.gdrive_connector.build"):
        connector = GoogleDriveConnector(
            client_id="test_client_id",
            client_secret="test_client_secret",
            redirect_uri="http://localhost:8000/callback",
            scopes=["https://www.googleapis.com/auth/drive.readonly"],
            encryption=encryption,
        )
        return connector


def test_generate_auth_url(connector: GoogleDriveConnector):
    """Test generating OAuth authorization URL."""
    url, state = connector.generate_auth_url()
    
    assert isinstance(url, str)
    assert "accounts.google.com" in url or "oauth2" in url
    assert isinstance(state, str)
    assert len(state) > 0


def test_exchange_code_for_tokens(connector: GoogleDriveConnector):
    """Test exchanging authorization code for tokens."""
    mock_flow = MagicMock()
    mock_credentials = MagicMock()
    mock_credentials.token = "access_token_123"
    mock_credentials.refresh_token = "refresh_token_456"
    mock_credentials.expiry = datetime.now(timezone.utc)
    
    mock_flow.fetch_token.return_value = None
    mock_flow.credentials = mock_credentials
    
    with patch("domains.files.gdrive_connector.Flow.from_client_config", return_value=mock_flow):
        tokens = connector.exchange_code_for_tokens("auth_code_xyz", "state_abc")
    
    assert tokens["access_token"] == "access_token_123"
    assert tokens["refresh_token"] == "refresh_token_456"
    assert "token_expiry" in tokens


def test_refresh_access_token(connector: GoogleDriveConnector):
    """Test refreshing an expired access token."""
    encrypted_refresh = connector.encryption.encrypt("refresh_token_456")
    
    mock_credentials = MagicMock()
    mock_credentials.token = "new_access_token_789"
    mock_credentials.expiry = datetime.now(timezone.utc)
    
    with patch("domains.files.gdrive_connector.Credentials") as mock_creds_class:
        mock_creds_class.return_value = mock_credentials
        
        new_tokens = connector.refresh_access_token(encrypted_refresh)
    
    assert "access_token" in new_tokens
    assert "token_expiry" in new_tokens


def test_list_files_in_folder(connector: GoogleDriveConnector):
    """Test listing files in a Google Drive folder."""
    mock_service = MagicMock()
    
    # Mock API response
    mock_service.files().list().execute.return_value = {
        "files": [
            {
                "id": "file1",
                "name": "test.csv",
                "mimeType": "text/csv",
                "modifiedTime": "2024-01-01T00:00:00.000Z",
                "size": "1024",
            },
            {
                "id": "file2",
                "name": "data.xlsx",
                "mimeType": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "modifiedTime": "2024-01-02T00:00:00.000Z",
                "size": "2048",
            },
        ],
        "nextPageToken": None,
    }
    
    connector.service = mock_service
    
    files = connector.list_files_in_folder(
        folder_id="folder123",
        access_token="token",
        include_shared_drives=False,
    )
    
    assert len(files) >= 2
    assert any(f["name"] == "test.csv" for f in files)
    assert any(f["name"] == "data.xlsx" for f in files)


def test_download_file(connector: GoogleDriveConnector):
    """Test downloading a file from Google Drive."""
    mock_service = MagicMock()
    
    # Mock file download
    mock_request = MagicMock()
    mock_service.files().get_media.return_value = mock_request
    
    with patch("domains.files.gdrive_connector.MediaIoBaseDownload") as mock_download:
        mock_downloader = MagicMock()
        mock_downloader.next_chunk.side_effect = [(None, False), (None, True)]
        mock_download.return_value = mock_downloader
        
        connector.service = mock_service
        
        cache_root = Path("/tmp/test_cache")
        result = connector.download_file(
            file_id="file123",
            file_name="test.csv",
            access_token="token",
            cache_root=cache_root,
            location_id="loc123",
        )
        
        assert isinstance(result, Path)


def test_list_files_filters_supported_types(connector: GoogleDriveConnector):
    """Test that listing filters to only supported file types."""
    mock_service = MagicMock()
    
    mock_service.files().list().execute.return_value = {
        "files": [
            {"id": "1", "name": "doc.csv", "mimeType": "text/csv", "modifiedTime": "2024-01-01T00:00:00.000Z", "size": "100"},
            {"id": "2", "name": "sheet.xlsx", "mimeType": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "modifiedTime": "2024-01-01T00:00:00.000Z", "size": "200"},
            {"id": "3", "name": "old.xls", "mimeType": "application/vnd.ms-excel", "modifiedTime": "2024-01-01T00:00:00.000Z", "size": "150"},
            {"id": "4", "name": "image.png", "mimeType": "image/png", "modifiedTime": "2024-01-01T00:00:00.000Z", "size": "300"},
            {"id": "5", "name": "gdoc", "mimeType": "application/vnd.google-apps.document", "modifiedTime": "2024-01-01T00:00:00.000Z"},
        ],
        "nextPageToken": None,
    }
    
    connector.service = mock_service
    
    files = connector.list_files_in_folder("folder123", "token", False)
    
    # Should only return CSV and Excel files, not PNG or Google Doc
    supported_files = [f for f in files if f["mimeType"] in [
        "text/csv",
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    ]]
    
    assert len(supported_files) == 3
    assert not any(f["name"] == "image.png" for f in supported_files)
    assert not any(f.get("name") == "gdoc" for f in supported_files)


def test_recursive_folder_scanning(connector: GoogleDriveConnector):
    """Test recursive scanning of nested folders."""
    mock_service = MagicMock()
    
    # Mock first call: returns a folder and a file
    mock_service.files().list().execute.side_effect = [
        {
            "files": [
                {"id": "folder1", "name": "subfolder", "mimeType": "application/vnd.google-apps.folder", "modifiedTime": "2024-01-01T00:00:00.000Z"},
                {"id": "file1", "name": "root.csv", "mimeType": "text/csv", "modifiedTime": "2024-01-01T00:00:00.000Z", "size": "100"},
            ],
            "nextPageToken": None,
        },
        # Mock second call (recursing into subfolder): returns a file
        {
            "files": [
                {"id": "file2", "name": "nested.xlsx", "mimeType": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "modifiedTime": "2024-01-01T00:00:00.000Z", "size": "200"},
            ],
            "nextPageToken": None,
        },
    ]
    
    connector.service = mock_service
    
    files = connector.list_files_in_folder("root_folder", "token", False)
    
    # Should find both root.csv and nested.xlsx
    assert len(files) >= 2
    assert any(f["name"] == "root.csv" for f in files)
    assert any(f["name"] == "nested.xlsx" for f in files)


def test_pagination_handling(connector: GoogleDriveConnector):
    """Test that pagination is handled correctly."""
    mock_service = MagicMock()
    
    # Mock paginated responses
    mock_service.files().list().execute.side_effect = [
        {
            "files": [
                {"id": "file1", "name": "page1.csv", "mimeType": "text/csv", "modifiedTime": "2024-01-01T00:00:00.000Z", "size": "100"},
            ],
            "nextPageToken": "token_page2",
        },
        {
            "files": [
                {"id": "file2", "name": "page2.csv", "mimeType": "text/csv", "modifiedTime": "2024-01-01T00:00:00.000Z", "size": "200"},
            ],
            "nextPageToken": None,
        },
    ]
    
    connector.service = mock_service
    
    files = connector.list_files_in_folder("folder123", "token", False)
    
    # Should retrieve files from both pages
    assert len(files) >= 2
    assert any(f["name"] == "page1.csv" for f in files)
    assert any(f["name"] == "page2.csv" for f in files)
