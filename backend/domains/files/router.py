"""
Files Domain Router

FastAPI endpoints for file location and asset management.
"""
import secrets
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlmodel import Session

from db_session import get_session
from domains.files.models import (
    FileLocationCreate,
    FileLocationUpdate,
    FileLocationResponse,
    ScanLocationRequest,
    ScanLocationResponse,
    FileAssetResponse,
    FileAssetDetailResponse,
    FileTablePreviewRequest,
    PublishTableRequest,
    ExternalAccount,
    ExternalAccountResponse,
    GoogleAuthUrlResponse,
    AuthProvider,
)
from domains.files.service import FilesService
from domains.files.gdrive_connector import get_gdrive_connector


router = APIRouter(prefix="/api/files", tags=["files"])


def get_files_service(session: Session = Depends(get_session)) -> FilesService:
    """Dependency to get FilesService instance"""
    return FilesService(session)


# --- File Locations ---

@router.post("/locations", response_model=FileLocationResponse, status_code=status.HTTP_201_CREATED)
async def create_location(
    location_data: FileLocationCreate,
    service: FilesService = Depends(get_files_service),
):
    """
    Create a new file location (local or Google Drive)
    
    For local: local_path must be within the configured FILES_ROOT for security.
    For gdrive: must provide gdrive_folder_id and external_account_id.
    """
    try:
        return service.create_location(
            name=location_data.name,
            location_type=location_data.type,
            local_path=location_data.local_path,
            gdrive_folder_id=location_data.gdrive_folder_id,
            gdrive_include_shared_drives=location_data.gdrive_include_shared_drives,
            external_account_id=location_data.external_account_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating location: {e}"
        )


@router.get("/locations", response_model=List[FileLocationResponse])
async def list_locations(
    service: FilesService = Depends(get_files_service),
):
    """List all file locations with file counts"""
    return service.list_locations()


@router.get("/locations/{location_id}", response_model=FileLocationResponse)
async def get_location(
    location_id: UUID,
    service: FilesService = Depends(get_files_service),
):
    """Get details of a specific file location"""
    location = service.get_location(location_id)
    if not location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Location {location_id} not found"
        )
    return location


@router.patch("/locations/{location_id}", response_model=FileLocationResponse)
async def update_location(
    location_id: UUID,
    update_data: FileLocationUpdate,
    service: FilesService = Depends(get_files_service),
):
    """Update a file location"""
    try:
        location = service.update_location(
            location_id=location_id,
            name=update_data.name,
            local_path=update_data.local_path,
            is_active=update_data.is_active,
        )
        if not location:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Location {location_id} not found"
            )
        return location
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/locations/{location_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_location(
    location_id: UUID,
    service: FilesService = Depends(get_files_service),
):
    """Delete (deactivate) a file location"""
    success = service.delete_location(location_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Location {location_id} not found"
        )
    return None


# --- File Scanning ---

@router.post("/locations/{location_id}/scan", response_model=ScanLocationResponse)
async def scan_location(
    location_id: UUID,
    service: FilesService = Depends(get_files_service),
):
    """
    Scan a location for files (CSV, Excel)
    
    This will:
    - Walk the directory recursively
    - Create/update FileAsset records
    - Detect new FileVersions by content hash
    - Extract tables and schemas
    
    For MVP, this is synchronous. Can be refactored to background task.
    """
    try:
        return service.scan_location(location_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error scanning location: {e}"
        )


# --- File Assets ---

@router.get("/assets", response_model=List[FileAssetResponse])
async def list_file_assets(
    location_id: Optional[UUID] = None,
    service: FilesService = Depends(get_files_service),
):
    """
    List all file assets, optionally filtered by location
    
    Returns files with their latest version info.
    """
    return service.list_file_assets(location_id=location_id)


@router.get("/assets/{asset_id}", response_model=FileAssetDetailResponse)
async def get_file_asset(
    asset_id: UUID,
    service: FilesService = Depends(get_files_service),
):
    """
    Get detailed info about a file asset
    
    Includes all versions and tables from the latest version.
    """
    asset = service.get_file_asset_detail(asset_id)
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File asset {asset_id} not found"
        )
    return asset


# --- Table Preview ---

@router.post("/tables/preview")
async def preview_table(
    request: FileTablePreviewRequest,
    service: FilesService = Depends(get_files_service),
):
    """
    Preview data from a file table
    
    Returns up to `limit` rows (max 1000) with pagination support.
    """
    try:
        result = service.preview_table(
            table_id=request.table_id,
            limit=request.limit,
            offset=request.offset,
        )
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Table {request.table_id} not found"
            )
        return result
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error previewing table: {e}"
        )


# --- Publish to Datasets ---

@router.post("/tables/{table_id}/publish")
async def publish_table(
    table_id: UUID,
    request: PublishTableRequest,
    service: FilesService = Depends(get_files_service),
):
    """
    Publish a file table to the Datasets domain
    
    For MVP, this marks the table as published.
    Future: create actual Dataset record and copy data.
    """
    # MVP: Just mark as published
    # TODO: Integrate with datasets domain when available
    from domains.files.models import FileTable
    from db_session import get_session
    
    # Get session manually (since we need to access FileTable directly)
    session = next(get_session())
    
    try:
        table = session.get(FileTable, table_id)
        if not table:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Table {table_id} not found"
            )
        
        table.is_published = True
        session.add(table)
        session.commit()
        session.refresh(table)
        
        return {
            "table_id": table.id,
            "table_name": table.table_name,
            "is_published": table.is_published,
            "message": "Table marked as published (MVP - no dataset created yet)",
        }
    finally:
        session.close()


# --- Google Drive OAuth ---

# In-memory state storage for OAuth (for MVP; use Redis/DB for production)
_oauth_states = {}

@router.get("/gdrive/auth/url", response_model=GoogleAuthUrlResponse)
async def get_gdrive_auth_url():
    """
    Get Google OAuth authorization URL
    
    Returns a URL to redirect the user's browser to start OAuth flow.
    """
    try:
        connector = get_gdrive_connector()
        
        # Generate state for CSRF protection
        state = secrets.token_urlsafe(32)
        _oauth_states[state] = {"created_at": "now"}  # Store with timestamp
        
        auth_url = connector.get_auth_url(state)
        
        return GoogleAuthUrlResponse(auth_url=auth_url, state=state)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating auth URL: {e}"
        )


@router.get("/gdrive/auth/callback")
async def gdrive_auth_callback(
    code: str = Query(...),
    state: str = Query(...),
    session: Session = Depends(get_session),
):
    """
    Handle Google OAuth callback
    
    Exchanges authorization code for tokens and stores in database.
    """
    # Validate state
    if state not in _oauth_states:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid state parameter"
        )
    
    # Remove used state
    _oauth_states.pop(state, None)
    
    try:
        connector = get_gdrive_connector()
        account = connector.exchange_code(code, session)
        
        # Redirect to frontend with success
        # For MVP, redirect to a success page or back to locations
        return RedirectResponse(
            url=f"/files/locations?connected={account.account_email}",
            status_code=status.HTTP_302_FOUND
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error exchanging code: {e}"
        )


@router.get("/gdrive/accounts", response_model=List[ExternalAccountResponse])
async def list_gdrive_accounts(
    session: Session = Depends(get_session),
):
    """
    List connected Google Drive accounts
    """
    stmt = select(ExternalAccount).where(ExternalAccount.provider == AuthProvider.GOOGLE)
    accounts = session.exec(stmt).all()
    
    return [
        ExternalAccountResponse(
            id=acc.id,
            provider=acc.provider,
            account_email=acc.account_email,
            scopes=acc.scopes.strip('[]"').split('","') if acc.scopes else [],
            token_expiry=acc.token_expiry,
            created_at=acc.created_at,
        )
        for acc in accounts
    ]


# --- Health Check ---

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "files"}
