"""
Files Domain Models

SQLModel tables and Pydantic schemas for file location and asset management.
"""
from datetime import datetime
from enum import Enum
from typing import Optional, List
from uuid import UUID, uuid4

from pydantic import BaseModel, Field
from sqlmodel import Column, DateTime, Field as SQLField, Relationship, SQLModel, Text


# --- Enums ---

class LocationType(str, Enum):
    """Type of file location connector"""
    LOCAL = "local"
    GDRIVE = "gdrive"
    # Future: SHAREPOINT = "sharepoint", etc.


class FileExtension(str, Enum):
    """Supported file extensions"""
    CSV = ".csv"
    XLSX = ".xlsx"
    XLS = ".xls"
    TSV = ".tsv"


class AuthProvider(str, Enum):
    """OAuth provider types"""
    NONE = "none"
    GOOGLE = "google"


# --- SQLModel Tables (Database) ---

class ExternalAccount(SQLModel, table=True):
    """
    OAuth credentials for external providers (Google Drive, etc.)
    """
    __tablename__ = "external_accounts"
    
    id: UUID = SQLField(default_factory=uuid4, primary_key=True)
    provider: AuthProvider = SQLField(nullable=False)
    account_email: str = SQLField(nullable=False, index=True)
    scopes: str = SQLField(sa_column=Column(Text, nullable=False))  # JSON array as string
    access_token_encrypted: Optional[str] = SQLField(default=None, sa_column=Column(Text))
    refresh_token_encrypted: Optional[str] = SQLField(default=None, sa_column=Column(Text))
    token_expiry: Optional[datetime] = SQLField(
        default=None, sa_column=Column(DateTime(timezone=True))
    )
    created_at: datetime = SQLField(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False)
    )
    updated_at: datetime = SQLField(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False)
    )
    
    # Relationships
    file_locations: List["FileLocation"] = Relationship(back_populates="external_account")


class FileLocation(SQLModel, table=True):
    """
    A configured location where files are stored (local folder, cloud storage, etc.)
    """
    __tablename__ = "file_locations"
    
    id: UUID = SQLField(default_factory=uuid4, primary_key=True)
    name: str = SQLField(index=True, nullable=False)
    type: LocationType = SQLField(default=LocationType.LOCAL, nullable=False)
    
    # Local filesystem fields
    local_path: Optional[str] = SQLField(default=None, sa_column=Column(Text))
    
    # Google Drive fields
    gdrive_folder_id: Optional[str] = SQLField(default=None)
    gdrive_include_shared_drives: bool = SQLField(default=True, nullable=False)
    gdrive_account_email: Optional[str] = SQLField(default=None)
    
    # OAuth integration
    auth_provider: AuthProvider = SQLField(default=AuthProvider.NONE, nullable=False)
    external_account_id: Optional[UUID] = SQLField(
        default=None, foreign_key="external_accounts.id", index=True
    )
    
    is_active: bool = SQLField(default=True, nullable=False)
    last_scanned_at: Optional[datetime] = SQLField(
        default=None, sa_column=Column(DateTime(timezone=True))
    )
    created_at: datetime = SQLField(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False)
    )
    updated_at: datetime = SQLField(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False)
    )
    
    # Relationships
    file_assets: List["FileAsset"] = Relationship(back_populates="location")
    external_account: Optional[ExternalAccount] = Relationship(back_populates="file_locations")


class FileAsset(SQLModel, table=True):
    """
    A file discovered in a location (tracks the file itself, across versions)
    """
    __tablename__ = "file_assets"
    
    id: UUID = SQLField(default_factory=uuid4, primary_key=True)
    location_id: UUID = SQLField(foreign_key="file_locations.id", nullable=False, index=True)
    provider_file_id: Optional[str] = SQLField(default=None)  # For cloud providers
    relative_path: str = SQLField(nullable=False, index=True)  # Path relative to location root
    file_name: str = SQLField(nullable=False)
    ext: str = SQLField(nullable=False)  # .csv, .xlsx, etc.
    mime_type: Optional[str] = SQLField(default=None)
    last_seen_at: datetime = SQLField(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False)
    )
    created_at: datetime = SQLField(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False)
    )
    
    # Relationships
    location: FileLocation = Relationship(back_populates="file_assets")
    versions: List["FileVersion"] = Relationship(back_populates="file_asset")


class FileVersion(SQLModel, table=True):
    """
    A specific version of a file (detected by content hash + modified timestamp)
    """
    __tablename__ = "file_versions"
    
    id: UUID = SQLField(default_factory=uuid4, primary_key=True)
    file_asset_id: UUID = SQLField(foreign_key="file_assets.id", nullable=False, index=True)
    detected_at: datetime = SQLField(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False)
    )
    modified_at: datetime = SQLField(
        sa_column=Column(DateTime(timezone=True), nullable=False)
    )
    size_bytes: int = SQLField(nullable=False)
    content_hash: str = SQLField(nullable=False, index=True)  # SHA-256
    row_count_estimate: Optional[int] = SQLField(default=None)
    
    # Relationships
    file_asset: FileAsset = Relationship(back_populates="versions")
    tables: List["FileTable"] = Relationship(back_populates="file_version")


class FileTable(SQLModel, table=True):
    """
    A logical table extracted from a file version (CSV = 1 table, Excel = N sheets)
    """
    __tablename__ = "file_tables"
    
    id: UUID = SQLField(default_factory=uuid4, primary_key=True)
    file_version_id: UUID = SQLField(foreign_key="file_versions.id", nullable=False, index=True)
    table_name: str = SQLField(nullable=False)  # Sheet name for Excel, file name for CSV
    row_count: int = SQLField(default=0, nullable=False)
    column_count: int = SQLField(default=0, nullable=False)
    schema_json: str = SQLField(sa_column=Column(Text))  # JSON array of {name, type, nullable}
    sample_data_json: Optional[str] = SQLField(default=None, sa_column=Column(Text))  # First 5 rows
    is_published: bool = SQLField(default=False, nullable=False)
    published_dataset_id: Optional[UUID] = SQLField(default=None)  # FK to datasets table (if exists)
    created_at: datetime = SQLField(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False)
    )
    
    # Relationships
    file_version: FileVersion = Relationship(back_populates="tables")


# --- Pydantic Schemas (API Request/Response) ---

class FileLocationCreate(BaseModel):
    """Request schema for creating a file location"""
    name: str = Field(..., min_length=1, max_length=255)
    type: LocationType = LocationType.LOCAL
    # Local fields
    local_path: Optional[str] = None
    # Google Drive fields
    gdrive_folder_id: Optional[str] = None
    gdrive_include_shared_drives: bool = True
    external_account_id: Optional[UUID] = None


class FileLocationUpdate(BaseModel):
    """Request schema for updating a file location"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    local_path: Optional[str] = None
    is_active: Optional[bool] = None


class FileLocationResponse(BaseModel):
    """Response schema for file location"""
    id: UUID
    name: str
    type: LocationType
    local_path: Optional[str]
    gdrive_folder_id: Optional[str]
    gdrive_include_shared_drives: bool
    gdrive_account_email: Optional[str]
    auth_provider: AuthProvider
    external_account_id: Optional[UUID]
    is_active: bool
    last_scanned_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    file_count: int = 0  # Computed field
    
    class Config:
        from_attributes = True


class ScanLocationRequest(BaseModel):
    """Request to scan a location for files"""
    location_id: UUID


class ScanLocationResponse(BaseModel):
    """Response from scanning a location"""
    location_id: UUID
    scanned_at: datetime
    files_found: int
    files_new: int
    files_updated: int
    files_unchanged: int
    duration_seconds: float


class FileAssetResponse(BaseModel):
    """Response schema for file asset"""
    id: UUID
    location_id: UUID
    location_name: str
    relative_path: str
    file_name: str
    ext: str
    mime_type: Optional[str]
    last_seen_at: datetime
    created_at: datetime
    latest_version: Optional["FileVersionResponse"] = None
    version_count: int = 0
    has_changes: bool = False  # True if latest version is new
    
    class Config:
        from_attributes = True


class ColumnSchema(BaseModel):
    """Schema for a single column"""
    name: str
    data_type: str  # "string", "integer", "float", "boolean", "datetime", etc.
    nullable: bool = True
    example_values: Optional[List[str]] = None


class FileVersionResponse(BaseModel):
    """Response schema for file version"""
    id: UUID
    file_asset_id: UUID
    detected_at: datetime
    modified_at: datetime
    size_bytes: int
    content_hash: str
    row_count_estimate: Optional[int]
    table_count: int = 0
    
    class Config:
        from_attributes = True


class FileTableResponse(BaseModel):
    """Response schema for file table"""
    id: UUID
    file_version_id: UUID
    table_name: str
    row_count: int
    column_count: int
    schema: List[ColumnSchema]  # Parsed from schema_json
    sample_data: Optional[List[List]] = None  # Parsed from sample_data_json
    is_published: bool
    published_dataset_id: Optional[UUID]
    created_at: datetime
    
    class Config:
        from_attributes = True


class FileTablePreviewRequest(BaseModel):
    """Request to preview a file table"""
    table_id: UUID
    limit: int = Field(default=100, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)


class FileTablePreviewResponse(BaseModel):
    """Response with table preview data"""
    table_id: UUID
    table_name: str
    columns: List[ColumnSchema]
    rows: List[List]  # Array of arrays
    total_rows: int
    limit: int
    offset: int


class FileAssetDetailResponse(BaseModel):
    """Detailed response for a single file asset"""
    asset: FileAssetResponse
    versions: List[FileVersionResponse]
    latest_tables: List[FileTableResponse]  # Tables from latest version
    
    class Config:
        from_attributes = True


class PublishTableRequest(BaseModel):
    """Request to publish a file table to datasets"""
    table_id: UUID
    dataset_name: Optional[str] = None  # If None, use table_name
    description: Optional[str] = None


# --- Google Drive Schemas ---

class ExternalAccountResponse(BaseModel):
    """Response schema for external account"""
    id: UUID
    provider: AuthProvider
    account_email: str
    scopes: List[str]  # Parsed from JSON
    token_expiry: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True


class GoogleAuthUrlResponse(BaseModel):
    """Response with Google OAuth URL"""
    auth_url: str
    state: str


class GoogleAuthCallbackRequest(BaseModel):
    """Request from OAuth callback"""
    code: str
    state: str
