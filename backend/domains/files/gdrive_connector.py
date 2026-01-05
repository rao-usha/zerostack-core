"""
Google Drive connector for scanning and downloading files
"""
import io
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from uuid import UUID

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from sqlmodel import Session

from domains.files.models import ExternalAccount, AuthProvider
from domains.files.encryption import get_token_encryptor


# Google Drive MIME types
GDRIVE_FOLDER_MIME = 'application/vnd.google-apps.folder'
GDRIVE_CSV_MIME = 'text/csv'
GDRIVE_XLS_MIME = 'application/vnd.ms-excel'
GDRIVE_XLSX_MIME = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'

SUPPORTED_MIME_TYPES = [
    GDRIVE_CSV_MIME,
    GDRIVE_XLS_MIME,
    GDRIVE_XLSX_MIME,
]

# Google native files (skip for MVP)
GOOGLE_NATIVE_MIME_PREFIX = 'application/vnd.google-apps.'


class GoogleDriveConnector:
    """
    Handles Google Drive OAuth and file operations
    """
    
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        scopes: List[str],
        cache_root: str,
    ):
        """
        Initialize Google Drive connector
        
        Args:
            client_id: Google OAuth client ID
            client_secret: Google OAuth client secret
            redirect_uri: OAuth redirect URI
            scopes: List of Google Drive scopes
            cache_root: Root directory for caching downloaded files
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.scopes = scopes
        self.cache_root = Path(cache_root)
        self.cache_root.mkdir(parents=True, exist_ok=True)
        self.encryptor = get_token_encryptor()
    
    def get_auth_url(self, state: str) -> str:
        """
        Generate Google OAuth authorization URL
        
        Args:
            state: State parameter for CSRF protection
            
        Returns:
            Authorization URL
        """
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [self.redirect_uri],
                }
            },
            scopes=self.scopes,
            redirect_uri=self.redirect_uri,
        )
        
        auth_url, _ = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            state=state,
            prompt='consent',  # Force consent to always get refresh token
        )
        
        return auth_url
    
    def exchange_code(
        self,
        code: str,
        session: Session,
    ) -> ExternalAccount:
        """
        Exchange authorization code for tokens and store in database
        
        Args:
            code: Authorization code from OAuth callback
            session: Database session
            
        Returns:
            ExternalAccount record
        """
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [self.redirect_uri],
                }
            },
            scopes=self.scopes,
            redirect_uri=self.redirect_uri,
        )
        
        flow.fetch_token(code=code)
        creds = flow.credentials
        
        # Get user email
        service = build('drive', 'v3', credentials=creds)
        about = service.about().get(fields='user').execute()
        user_email = about['user']['emailAddress']
        
        # Check if account already exists
        from sqlalchemy import select
        stmt = (
            select(ExternalAccount)
            .where(ExternalAccount.provider == AuthProvider.GOOGLE)
            .where(ExternalAccount.account_email == user_email)
        )
        account = session.exec(stmt).first()
        
        # Encrypt tokens
        access_token_enc = self.encryptor.encrypt(creds.token) if creds.token else None
        refresh_token_enc = self.encryptor.encrypt(creds.refresh_token) if creds.refresh_token else None
        
        if account:
            # Update existing account
            account.scopes = json.dumps(self.scopes)
            account.access_token_encrypted = access_token_enc
            account.refresh_token_encrypted = refresh_token_enc
            account.token_expiry = creds.expiry
            account.updated_at = datetime.utcnow()
        else:
            # Create new account
            account = ExternalAccount(
                provider=AuthProvider.GOOGLE,
                account_email=user_email,
                scopes=json.dumps(self.scopes),
                access_token_encrypted=access_token_enc,
                refresh_token_encrypted=refresh_token_enc,
                token_expiry=creds.expiry,
            )
        
        session.add(account)
        session.commit()
        session.refresh(account)
        
        return account
    
    def get_credentials(self, account: ExternalAccount, session: Session) -> Credentials:
        """
        Get Google credentials from external account, refreshing if needed
        
        Args:
            account: ExternalAccount record
            session: Database session
            
        Returns:
            Google Credentials object
        """
        # Decrypt tokens
        access_token = self.encryptor.decrypt(account.access_token_encrypted) if account.access_token_encrypted else None
        refresh_token = self.encryptor.decrypt(account.refresh_token_encrypted) if account.refresh_token_encrypted else None
        
        creds = Credentials(
            token=access_token,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=self.client_id,
            client_secret=self.client_secret,
            scopes=json.loads(account.scopes),
        )
        
        # Set expiry if available
        if account.token_expiry:
            creds.expiry = account.token_expiry
        
        # Refresh if expired
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            
            # Update stored tokens
            account.access_token_encrypted = self.encryptor.encrypt(creds.token)
            account.token_expiry = creds.expiry
            account.updated_at = datetime.utcnow()
            session.add(account)
            session.commit()
        
        return creds
    
    def list_files_recursive(
        self,
        credentials: Credentials,
        folder_id: str,
        include_shared_drives: bool = True,
    ) -> List[Dict]:
        """
        List files recursively in a Google Drive folder
        
        Args:
            credentials: Google OAuth credentials
            folder_id: Folder ID to scan
            include_shared_drives: Whether to include shared drives
            
        Returns:
            List of file metadata dicts
        """
        service = build('drive', 'v3', credentials=credentials)
        
        all_files = []
        folders_to_process = [(folder_id, "")]  # (folder_id, path_prefix)
        
        while folders_to_process:
            current_folder_id, path_prefix = folders_to_process.pop(0)
            
            # Query for files in current folder
            query = f"'{current_folder_id}' in parents and trashed=false"
            
            page_token = None
            while True:
                results = service.files().list(
                    q=query,
                    pageSize=100,
                    fields="nextPageToken, files(id, name, mimeType, size, modifiedTime, md5Checksum, parents)",
                    pageToken=page_token,
                    includeItemsFromAllDrives=include_shared_drives,
                    supportsAllDrives=include_shared_drives,
                    corpora='allDrives' if include_shared_drives else 'user',
                ).execute()
                
                files = results.get('files', [])
                
                for file in files:
                    mime_type = file.get('mimeType', '')
                    file_name = file['name']
                    
                    # Construct relative path
                    relative_path = f"{path_prefix}/{file_name}" if path_prefix else file_name
                    
                    if mime_type == GDRIVE_FOLDER_MIME:
                        # Add folder to processing queue
                        folders_to_process.append((file['id'], relative_path))
                    elif self._is_supported_file(file_name, mime_type):
                        # Add file to results
                        file['relative_path'] = relative_path
                        all_files.append(file)
                
                page_token = results.get('nextPageToken')
                if not page_token:
                    break
        
        return all_files
    
    def _is_supported_file(self, file_name: str, mime_type: str) -> bool:
        """
        Check if file is a supported type
        
        Args:
            file_name: File name
            mime_type: MIME type
            
        Returns:
            True if supported
        """
        # Skip Google native files
        if mime_type.startswith(GOOGLE_NATIVE_MIME_PREFIX):
            return False
        
        # Check MIME type
        if mime_type in SUPPORTED_MIME_TYPES:
            return True
        
        # Check file extension
        ext = Path(file_name).suffix.lower()
        return ext in ['.csv', '.xlsx', '.xls', '.tsv']
    
    def download_file(
        self,
        credentials: Credentials,
        file_id: str,
        location_id: UUID,
        version_hash: str,
        file_name: str,
    ) -> Path:
        """
        Download a file from Google Drive to cache
        
        Args:
            credentials: Google OAuth credentials
            file_id: Google Drive file ID
            location_id: File location UUID
            version_hash: Content hash for versioning
            file_name: Original file name
            
        Returns:
            Path to downloaded file
        """
        service = build('drive', 'v3', credentials=credentials)
        
        # Create cache directory structure
        cache_dir = self.cache_root / str(location_id) / file_id / version_hash
        cache_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = cache_dir / file_name
        
        # Skip if already cached
        if file_path.exists():
            return file_path
        
        # Download file
        request = service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        
        done = False
        while not done:
            status, done = downloader.next_chunk()
        
        # Write to cache
        with open(file_path, 'wb') as f:
            f.write(fh.getvalue())
        
        return file_path


def get_gdrive_connector() -> GoogleDriveConnector:
    """
    Get a GoogleDriveConnector instance from environment config
    
    Returns:
        GoogleDriveConnector instance
    """
    client_id = os.getenv('GOOGLE_OAUTH_CLIENT_ID')
    client_secret = os.getenv('GOOGLE_OAUTH_CLIENT_SECRET')
    redirect_uri = os.getenv('GOOGLE_OAUTH_REDIRECT_URI')
    scopes_str = os.getenv('GOOGLE_OAUTH_SCOPES', 'https://www.googleapis.com/auth/drive.readonly')
    cache_root = os.getenv('FILES_CACHE_ROOT', '/tmp/nex_files_cache')
    
    if not client_id or not client_secret or not redirect_uri:
        raise ValueError(
            "GOOGLE_OAUTH_CLIENT_ID, GOOGLE_OAUTH_CLIENT_SECRET, and "
            "GOOGLE_OAUTH_REDIRECT_URI must be set for Google Drive integration"
        )
    
    scopes = [s.strip() for s in scopes_str.split(',')]
    
    return GoogleDriveConnector(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        scopes=scopes,
        cache_root=cache_root,
    )
