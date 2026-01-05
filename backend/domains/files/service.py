"""
Files Domain Service Layer

Business logic for scanning folders, parsing files, and managing file assets.
"""
import hashlib
import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from uuid import UUID

import pandas as pd
from sqlalchemy import select, func
from sqlmodel import Session

from domains.files.models import (
    FileLocation,
    FileAsset,
    FileVersion,
    FileTable,
    FileExtension,
    LocationType,
    AuthProvider,
    ExternalAccount,
    ColumnSchema,
    FileLocationResponse,
    FileAssetResponse,
    FileVersionResponse,
    FileTableResponse,
    ScanLocationResponse,
    FileAssetDetailResponse,
)
from domains.files.gdrive_connector import get_gdrive_connector


class FilesService:
    """Service for managing file locations and assets"""
    
    def __init__(self, session: Session, files_root: Optional[str] = None):
        """
        Initialize service
        
        Args:
            session: Database session
            files_root: Root directory for file access (security constraint)
        """
        self.session = session
        self.files_root = files_root or os.getenv("FILES_ROOT", str(Path.home()))
    
    # --- File Locations ---
    
    def create_location(
        self, 
        name: str,
        location_type: LocationType = LocationType.LOCAL,
        local_path: Optional[str] = None,
        gdrive_folder_id: Optional[str] = None,
        gdrive_include_shared_drives: bool = True,
        external_account_id: Optional[UUID] = None,
    ) -> FileLocationResponse:
        """
        Create a new file location (local or Google Drive)
        
        For local: Validates that path is within FILES_ROOT for security.
        For gdrive: Validates external account exists.
        """
        if location_type == LocationType.LOCAL:
            if not local_path:
                raise ValueError("local_path is required for local locations")
            
            # Security: validate path is within allowed root
            abs_path = Path(local_path).resolve()
            root_path = Path(self.files_root).resolve()
            
            if not str(abs_path).startswith(str(root_path)):
                raise ValueError(
                    f"Path {local_path} is outside allowed root {self.files_root}"
                )
            
            if not abs_path.exists():
                raise ValueError(f"Path {local_path} does not exist")
            
            if not abs_path.is_dir():
                raise ValueError(f"Path {local_path} is not a directory")
            
            location = FileLocation(
                name=name,
                type=LocationType.LOCAL,
                local_path=str(abs_path),
                auth_provider=AuthProvider.NONE,
            )
        
        elif location_type == LocationType.GDRIVE:
            if not gdrive_folder_id:
                raise ValueError("gdrive_folder_id is required for gdrive locations")
            
            if not external_account_id:
                raise ValueError("external_account_id is required for gdrive locations")
            
            # Validate external account exists
            account = self.session.get(ExternalAccount, external_account_id)
            if not account:
                raise ValueError(f"External account {external_account_id} not found")
            
            location = FileLocation(
                name=name,
                type=LocationType.GDRIVE,
                gdrive_folder_id=gdrive_folder_id,
                gdrive_include_shared_drives=gdrive_include_shared_drives,
                gdrive_account_email=account.account_email,
                auth_provider=AuthProvider.GOOGLE,
                external_account_id=external_account_id,
            )
        
        else:
            raise ValueError(f"Unsupported location type: {location_type}")
        
        self.session.add(location)
        self.session.commit()
        self.session.refresh(location)
        
        return self._location_to_response(location)
    
    def list_locations(self) -> List[FileLocationResponse]:
        """List all file locations with file counts"""
        locations = self.session.exec(select(FileLocation)).all()
        return [self._location_to_response(loc) for loc in locations]
    
    def get_location(self, location_id: UUID) -> Optional[FileLocationResponse]:
        """Get a specific location"""
        location = self.session.get(FileLocation, location_id)
        if not location:
            return None
        return self._location_to_response(location)
    
    def update_location(
        self, 
        location_id: UUID, 
        name: Optional[str] = None,
        local_path: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> Optional[FileLocationResponse]:
        """Update a file location"""
        location = self.session.get(FileLocation, location_id)
        if not location:
            return None
        
        if name is not None:
            location.name = name
        
        if local_path is not None:
            # Re-validate path
            abs_path = Path(local_path).resolve()
            root_path = Path(self.files_root).resolve()
            if not str(abs_path).startswith(str(root_path)):
                raise ValueError(f"Path outside allowed root")
            location.local_path = str(abs_path)
        
        if is_active is not None:
            location.is_active = is_active
        
        location.updated_at = datetime.utcnow()
        
        self.session.add(location)
        self.session.commit()
        self.session.refresh(location)
        
        return self._location_to_response(location)
    
    def delete_location(self, location_id: UUID) -> bool:
        """Delete a file location (soft delete by setting is_active=False)"""
        location = self.session.get(FileLocation, location_id)
        if not location:
            return False
        
        location.is_active = False
        location.updated_at = datetime.utcnow()
        self.session.add(location)
        self.session.commit()
        return True
    
    def _location_to_response(self, location: FileLocation) -> FileLocationResponse:
        """Convert SQLModel to Pydantic response"""
        # Count files
        stmt = (
            select(func.count(FileAsset.id))
            .where(FileAsset.location_id == location.id)
        )
        file_count = self.session.exec(stmt).one()
        
        return FileLocationResponse(
            id=location.id,
            name=location.name,
            type=location.type,
            local_path=location.local_path,
            gdrive_folder_id=location.gdrive_folder_id,
            gdrive_include_shared_drives=location.gdrive_include_shared_drives,
            gdrive_account_email=location.gdrive_account_email,
            auth_provider=location.auth_provider,
            external_account_id=location.external_account_id,
            is_active=location.is_active,
            last_scanned_at=location.last_scanned_at,
            created_at=location.created_at,
            updated_at=location.updated_at,
            file_count=file_count,
        )
    
    # --- File Scanning ---
    
    def scan_location(self, location_id: UUID) -> ScanLocationResponse:
        """
        Scan a location for files, create/update FileAssets and FileVersions
        
        Supports both local and Google Drive locations.
        For MVP, this is synchronous. Can be refactored to background task later.
        """
        start_time = time.time()
        location = self.session.get(FileLocation, location_id)
        if not location:
            raise ValueError(f"Location {location_id} not found")
        
        if location.type == LocationType.LOCAL:
            stats = self._scan_local(location)
        elif location.type == LocationType.GDRIVE:
            stats = self._scan_gdrive(location)
        else:
            raise ValueError(f"Unsupported location type: {location.type}")
        
        # Update location scan time
        location.last_scanned_at = datetime.utcnow()
        self.session.add(location)
        self.session.commit()
        
        duration = time.time() - start_time
        
        return ScanLocationResponse(
            location_id=location_id,
            scanned_at=location.last_scanned_at,
            duration_seconds=round(duration, 2),
            **stats
        )
    
    def _scan_local(self, location: FileLocation) -> Dict[str, int]:
        """Scan a local filesystem location"""
        if not location.local_path:
            raise ValueError(f"Location {location.id} has no local_path")
        
        root_path = Path(location.local_path)
        if not root_path.exists():
            raise ValueError(f"Path {root_path} does not exist")
        
        stats = {
            "files_found": 0,
            "files_new": 0,
            "files_updated": 0,
            "files_unchanged": 0,
        }
        
        # Supported extensions
        supported_exts = {ext.value for ext in FileExtension}
        
        # Walk directory recursively
        for file_path in root_path.rglob("*"):
            if not file_path.is_file():
                continue
            
            if file_path.suffix.lower() not in supported_exts:
                continue
            
            stats["files_found"] += 1
            
            # Process this file
            result = self._process_file(location, root_path, file_path)
            if result == "new":
                stats["files_new"] += 1
            elif result == "updated":
                stats["files_updated"] += 1
            else:
                stats["files_unchanged"] += 1
        
        return stats
    
    def _scan_gdrive(self, location: FileLocation) -> Dict[str, int]:
        """Scan a Google Drive location"""
        if not location.gdrive_folder_id or not location.external_account_id:
            raise ValueError(f"Location {location.id} missing gdrive configuration")
        
        # Get external account
        account = self.session.get(ExternalAccount, location.external_account_id)
        if not account:
            raise ValueError(f"External account {location.external_account_id} not found")
        
        # Get Google Drive connector
        connector = get_gdrive_connector()
        credentials = connector.get_credentials(account, self.session)
        
        # List files
        files = connector.list_files_recursive(
            credentials=credentials,
            folder_id=location.gdrive_folder_id,
            include_shared_drives=location.gdrive_include_shared_drives,
        )
        
        stats = {
            "files_found": len(files),
            "files_new": 0,
            "files_updated": 0,
            "files_unchanged": 0,
        }
        
        # Process each file
        for file_meta in files:
            result = self._process_gdrive_file(location, file_meta, connector, credentials)
            if result == "new":
                stats["files_new"] += 1
            elif result == "updated":
                stats["files_updated"] += 1
            else:
                stats["files_unchanged"] += 1
        
        return stats
    
    def _process_gdrive_file(
        self,
        location: FileLocation,
        file_meta: Dict,
        connector,
        credentials,
    ) -> str:
        """
        Process a single Google Drive file
        
        Returns: "new", "updated", or "unchanged"
        """
        file_id = file_meta['id']
        file_name = file_meta['name']
        relative_path = file_meta.get('relative_path', file_name)
        mime_type = file_meta.get('mimeType')
        size_bytes = int(file_meta.get('size', 0))
        modified_time_str = file_meta.get('modifiedTime')
        
        # Parse modified time
        modified_at = datetime.fromisoformat(modified_time_str.replace('Z', '+00:00'))
        
        # Get or create FileAsset
        stmt = (
            select(FileAsset)
            .where(FileAsset.location_id == location.id)
            .where(FileAsset.provider_file_id == file_id)
        )
        file_asset = self.session.exec(stmt).first()
        
        if not file_asset:
            file_asset = FileAsset(
                location_id=location.id,
                provider_file_id=file_id,
                relative_path=relative_path,
                file_name=file_name,
                ext=Path(file_name).suffix.lower(),
                mime_type=mime_type,
                last_seen_at=datetime.utcnow(),
            )
            self.session.add(file_asset)
            self.session.flush()
            result = "new"
        else:
            file_asset.last_seen_at = datetime.utcnow()
            file_asset.relative_path = relative_path  # Update in case file was moved
            self.session.add(file_asset)
            result = "unchanged"
        
        # Compute content hash (use md5Checksum if available, otherwise download)
        if 'md5Checksum' in file_meta:
            content_hash = file_meta['md5Checksum']
        else:
            # Download and compute SHA256
            temp_path = connector.download_file(
                credentials=credentials,
                file_id=file_id,
                location_id=location.id,
                version_hash="temp",
                file_name=file_name,
            )
            content_hash = self._compute_file_hash(temp_path)
        
        # Check if we already have this version
        stmt = (
            select(FileVersion)
            .where(FileVersion.file_asset_id == file_asset.id)
            .where(FileVersion.content_hash == content_hash)
        )
        existing_version = self.session.exec(stmt).first()
        
        if existing_version:
            return result
        
        # Download file to cache
        cached_path = connector.download_file(
            credentials=credentials,
            file_id=file_id,
            location_id=location.id,
            version_hash=content_hash[:16],
            file_name=file_name,
        )
        
        # Create new version
        file_version = FileVersion(
            file_asset_id=file_asset.id,
            modified_at=modified_at,
            size_bytes=size_bytes,
            content_hash=content_hash,
        )
        self.session.add(file_version)
        self.session.flush()
        
        # Extract tables from cached file
        try:
            self._extract_tables(cached_path, file_version)
            result = "updated" if result == "unchanged" else result
        except Exception as e:
            print(f"Error extracting tables from {file_name}: {e}")
        
        self.session.commit()
        return result
    
    def _process_file(
        self, 
        location: FileLocation, 
        root_path: Path, 
        file_path: Path
    ) -> str:
        """
        Process a single file: create/update FileAsset and FileVersion
        
        Returns: "new", "updated", or "unchanged"
        """
        relative_path = str(file_path.relative_to(root_path))
        
        # Get or create FileAsset
        stmt = (
            select(FileAsset)
            .where(FileAsset.location_id == location.id)
            .where(FileAsset.relative_path == relative_path)
        )
        file_asset = self.session.exec(stmt).first()
        
        if not file_asset:
            file_asset = FileAsset(
                location_id=location.id,
                relative_path=relative_path,
                file_name=file_path.name,
                ext=file_path.suffix.lower(),
                last_seen_at=datetime.utcnow(),
            )
            self.session.add(file_asset)
            self.session.flush()  # Get ID
            result = "new"
        else:
            file_asset.last_seen_at = datetime.utcnow()
            self.session.add(file_asset)
            result = "unchanged"
        
        # Compute file metadata
        stat = file_path.stat()
        modified_at = datetime.fromtimestamp(stat.st_mtime)
        size_bytes = stat.st_size
        content_hash = self._compute_file_hash(file_path)
        
        # Check if we already have this version
        stmt = (
            select(FileVersion)
            .where(FileVersion.file_asset_id == file_asset.id)
            .where(FileVersion.content_hash == content_hash)
        )
        existing_version = self.session.exec(stmt).first()
        
        if existing_version:
            # Version already exists
            return result
        
        # Create new version
        file_version = FileVersion(
            file_asset_id=file_asset.id,
            modified_at=modified_at,
            size_bytes=size_bytes,
            content_hash=content_hash,
        )
        self.session.add(file_version)
        self.session.flush()  # Get ID
        
        # Extract tables from file
        try:
            self._extract_tables(file_path, file_version)
            result = "updated" if result == "unchanged" else result
        except Exception as e:
            print(f"Error extracting tables from {file_path}: {e}")
            # Continue anyway - version is recorded
        
        self.session.commit()
        return result
    
    def _compute_file_hash(self, file_path: Path) -> str:
        """Compute SHA-256 hash of file content"""
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(8192):
                sha256.update(chunk)
        return sha256.hexdigest()
    
    def _extract_tables(self, file_path: Path, file_version: FileVersion):
        """
        Extract tables from a file and create FileTable records
        
        CSV => 1 table
        Excel => 1 table per sheet
        """
        ext = file_path.suffix.lower()
        
        if ext == ".csv" or ext == ".tsv":
            self._extract_csv_table(file_path, file_version, ext)
        elif ext in [".xlsx", ".xls"]:
            self._extract_excel_tables(file_path, file_version)
    
    def _extract_csv_table(self, file_path: Path, file_version: FileVersion, ext: str):
        """Extract single table from CSV/TSV"""
        sep = "\t" if ext == ".tsv" else ","
        
        # Read file
        try:
            df = pd.read_csv(file_path, sep=sep, nrows=1000)  # Sample first 1000 rows for inference
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            return
        
        # Infer schema
        schema = self._infer_schema(df)
        
        # Get row count (re-read without nrows limit for count)
        try:
            row_count = len(pd.read_csv(file_path, sep=sep, usecols=[0]))
        except:
            row_count = len(df)  # Fallback to sample size
        
        # Sample data (first 5 rows)
        sample_data = df.head(5).values.tolist()
        
        # Create FileTable
        file_table = FileTable(
            file_version_id=file_version.id,
            table_name=file_path.stem,  # File name without extension
            row_count=row_count,
            column_count=len(df.columns),
            schema_json=json.dumps([col.dict() for col in schema]),
            sample_data_json=json.dumps(sample_data),
        )
        
        self.session.add(file_table)
        
        # Update version row count
        file_version.row_count_estimate = row_count
        self.session.add(file_version)
    
    def _extract_excel_tables(self, file_path: Path, file_version: FileVersion):
        """Extract multiple tables from Excel sheets"""
        try:
            excel_file = pd.ExcelFile(file_path)
        except Exception as e:
            print(f"Error reading Excel file {file_path}: {e}")
            return
        
        total_rows = 0
        
        for sheet_name in excel_file.sheet_names:
            try:
                df = pd.read_excel(excel_file, sheet_name=sheet_name, nrows=1000)
                
                if df.empty:
                    continue
                
                # Infer schema
                schema = self._infer_schema(df)
                
                # Get actual row count
                df_full = pd.read_excel(excel_file, sheet_name=sheet_name, usecols=[0])
                row_count = len(df_full)
                total_rows += row_count
                
                # Sample data
                sample_data = df.head(5).values.tolist()
                
                # Create FileTable
                file_table = FileTable(
                    file_version_id=file_version.id,
                    table_name=sheet_name,
                    row_count=row_count,
                    column_count=len(df.columns),
                    schema_json=json.dumps([col.dict() for col in schema]),
                    sample_data_json=json.dumps(sample_data),
                )
                
                self.session.add(file_table)
                
            except Exception as e:
                print(f"Error processing sheet {sheet_name} in {file_path}: {e}")
                continue
        
        # Update version row count
        file_version.row_count_estimate = total_rows
        self.session.add(file_version)
    
    def _infer_schema(self, df: pd.DataFrame) -> List[ColumnSchema]:
        """Infer column schema from pandas DataFrame"""
        schema = []
        
        for col_name in df.columns:
            dtype = df[col_name].dtype
            
            # Map pandas dtype to simple type string
            if pd.api.types.is_integer_dtype(dtype):
                data_type = "integer"
            elif pd.api.types.is_float_dtype(dtype):
                data_type = "float"
            elif pd.api.types.is_bool_dtype(dtype):
                data_type = "boolean"
            elif pd.api.types.is_datetime64_any_dtype(dtype):
                data_type = "datetime"
            else:
                data_type = "string"
            
            # Check nullability
            nullable = df[col_name].isnull().any()
            
            # Get example values (non-null, unique)
            examples = (
                df[col_name]
                .dropna()
                .unique()[:3]
                .tolist()
            )
            example_values = [str(v) for v in examples]
            
            schema.append(ColumnSchema(
                name=str(col_name),
                data_type=data_type,
                nullable=nullable,
                example_values=example_values,
            ))
        
        return schema
    
    # --- File Assets ---
    
    def list_file_assets(
        self, 
        location_id: Optional[UUID] = None
    ) -> List[FileAssetResponse]:
        """List all file assets, optionally filtered by location"""
        stmt = select(FileAsset)
        if location_id:
            stmt = stmt.where(FileAsset.location_id == location_id)
        stmt = stmt.order_by(FileAsset.last_seen_at.desc())
        
        assets = self.session.exec(stmt).all()
        return [self._asset_to_response(asset) for asset in assets]
    
    def get_file_asset_detail(self, asset_id: UUID) -> Optional[FileAssetDetailResponse]:
        """Get detailed info about a file asset including versions and tables"""
        asset = self.session.get(FileAsset, asset_id)
        if not asset:
            return None
        
        # Get all versions
        stmt = (
            select(FileVersion)
            .where(FileVersion.file_asset_id == asset_id)
            .order_by(FileVersion.detected_at.desc())
        )
        versions = self.session.exec(stmt).all()
        version_responses = [self._version_to_response(v) for v in versions]
        
        # Get tables from latest version
        latest_tables = []
        if versions:
            latest_version = versions[0]
            stmt = select(FileTable).where(FileTable.file_version_id == latest_version.id)
            tables = self.session.exec(stmt).all()
            latest_tables = [self._table_to_response(t) for t in tables]
        
        return FileAssetDetailResponse(
            asset=self._asset_to_response(asset),
            versions=version_responses,
            latest_tables=latest_tables,
        )
    
    def _asset_to_response(self, asset: FileAsset) -> FileAssetResponse:
        """Convert FileAsset to response"""
        # Get location name
        location = self.session.get(FileLocation, asset.location_id)
        location_name = location.name if location else "Unknown"
        
        # Get latest version
        stmt = (
            select(FileVersion)
            .where(FileVersion.file_asset_id == asset.id)
            .order_by(FileVersion.detected_at.desc())
            .limit(1)
        )
        latest_version = self.session.exec(stmt).first()
        
        # Count versions
        stmt = (
            select(func.count(FileVersion.id))
            .where(FileVersion.file_asset_id == asset.id)
        )
        version_count = self.session.exec(stmt).one()
        
        # Has changes if latest version was detected recently
        has_changes = False
        if latest_version:
            time_since_detected = datetime.utcnow() - latest_version.detected_at
            has_changes = time_since_detected.total_seconds() < 300  # 5 minutes
        
        return FileAssetResponse(
            id=asset.id,
            location_id=asset.location_id,
            location_name=location_name,
            relative_path=asset.relative_path,
            file_name=asset.file_name,
            ext=asset.ext,
            mime_type=asset.mime_type,
            last_seen_at=asset.last_seen_at,
            created_at=asset.created_at,
            latest_version=self._version_to_response(latest_version) if latest_version else None,
            version_count=version_count,
            has_changes=has_changes,
        )
    
    def _version_to_response(self, version: FileVersion) -> FileVersionResponse:
        """Convert FileVersion to response"""
        # Count tables
        stmt = (
            select(func.count(FileTable.id))
            .where(FileTable.file_version_id == version.id)
        )
        table_count = self.session.exec(stmt).one()
        
        return FileVersionResponse(
            id=version.id,
            file_asset_id=version.file_asset_id,
            detected_at=version.detected_at,
            modified_at=version.modified_at,
            size_bytes=version.size_bytes,
            content_hash=version.content_hash,
            row_count_estimate=version.row_count_estimate,
            table_count=table_count,
        )
    
    def _table_to_response(self, table: FileTable) -> FileTableResponse:
        """Convert FileTable to response"""
        # Parse schema JSON
        schema = [ColumnSchema(**col) for col in json.loads(table.schema_json)]
        
        # Parse sample data if present
        sample_data = None
        if table.sample_data_json:
            sample_data = json.loads(table.sample_data_json)
        
        return FileTableResponse(
            id=table.id,
            file_version_id=table.file_version_id,
            table_name=table.table_name,
            row_count=table.row_count,
            column_count=table.column_count,
            schema=schema,
            sample_data=sample_data,
            is_published=table.is_published,
            published_dataset_id=table.published_dataset_id,
            created_at=table.created_at,
        )
    
    # --- Table Preview ---
    
    def preview_table(
        self, 
        table_id: UUID, 
        limit: int = 100, 
        offset: int = 0
    ) -> Optional[Dict]:
        """
        Load and preview data from a file table
        
        Returns dict with columns, rows, total_rows
        """
        table = self.session.get(FileTable, table_id)
        if not table:
            return None
        
        # Get file version and asset
        version = self.session.get(FileVersion, table.file_version_id)
        if not version:
            return None
        
        asset = self.session.get(FileAsset, version.file_asset_id)
        if not asset:
            return None
        
        location = self.session.get(FileLocation, asset.location_id)
        if not location or not location.local_path:
            return None
        
        # Construct file path
        file_path = Path(location.local_path) / asset.relative_path
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Load data based on file type
        ext = asset.ext.lower()
        
        try:
            if ext in [".csv", ".tsv"]:
                sep = "\t" if ext == ".tsv" else ","
                df = pd.read_csv(
                    file_path, 
                    sep=sep, 
                    skiprows=offset, 
                    nrows=limit
                )
            elif ext in [".xlsx", ".xls"]:
                df = pd.read_excel(
                    file_path, 
                    sheet_name=table.table_name,
                    skiprows=offset,
                    nrows=limit
                )
            else:
                raise ValueError(f"Unsupported file type: {ext}")
            
            # Convert to response format
            schema = [ColumnSchema(**col) for col in json.loads(table.schema_json)]
            rows = df.values.tolist()
            
            return {
                "table_id": table.id,
                "table_name": table.table_name,
                "columns": schema,
                "rows": rows,
                "total_rows": table.row_count,
                "limit": limit,
                "offset": offset,
            }
            
        except Exception as e:
            raise ValueError(f"Error reading file: {e}")
