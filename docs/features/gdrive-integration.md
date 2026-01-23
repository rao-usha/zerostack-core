# Google Drive Integration

The Files feature supports both local folders and Google Drive folders, enabling unified file management across storage locations.

## Overview

Google Drive integration enables you to:
- Scan Google Drive folders for CSV and Excel files
- Support "My Drive" and Shared Drives
- Track file versions automatically via content hashing
- Preview and publish Drive files like local files
- Secure OAuth 2.0 authentication with encrypted token storage

## Quick Start

### 1. Install Dependencies

```bash
cd backend
pip install google-api-python-client google-auth google-auth-oauthlib cryptography
```

### 2. Google Cloud Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create/select a project
3. Enable **Google Drive API**
4. Create OAuth 2.0 credentials (Web application)
5. Add redirect URI: `http://localhost:8000/api/files/gdrive/auth/callback`
6. Save Client ID and Client Secret

### 3. Environment Configuration

Add to `.env`:

```bash
GOOGLE_OAUTH_CLIENT_ID=your-id.apps.googleusercontent.com
GOOGLE_OAUTH_CLIENT_SECRET=your-secret
GOOGLE_OAUTH_REDIRECT_URI=http://localhost:8000/api/files/gdrive/auth/callback
GOOGLE_OAUTH_SCOPES=https://www.googleapis.com/auth/drive.readonly
FILES_CACHE_ROOT=C:\Users\awron\AppData\Local\nex_files_cache
ENCRYPTION_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
```

### 4. Run Migration

```bash
cd backend
alembic upgrade head
```

### 5. Connect and Scan

1. Navigate to **Files** → **Locations** (`/files/locations`)
2. Click **Add Location** → **Google Drive**
3. Click **Connect Google Drive** (OAuth flow)
4. Enter Folder ID (from Drive URL)
5. Click **Create Location**
6. Click **Scan Now**

---

## Features

### OAuth Authentication
- Secure OAuth 2.0 flow with Google
- Tokens encrypted at rest (Fernet/AES)
- Automatic token refresh
- Multiple Google accounts supported

### File Scanning
- Recursive folder scanning
- My Drive and Shared Drives
- File type filtering: CSV, XLS, XLSX, TSV
- Skip Google-native files (Sheets/Docs)

### Version Tracking
- Content-based hashing (MD5 from Drive or SHA256)
- Automatic change detection on re-scan
- Version history for each file

### File Caching
Downloaded files cached locally:
```
{FILES_CACHE_ROOT}/
  {location_id}/
    {file_id}/
      {content_hash}/
        original_filename.xlsx
```

---

## Getting Folder ID

From Google Drive URL:
```
https://drive.google.com/drive/folders/1a2B3c4D5e6F7g8H9i0J
                                         ^^^^^^^^^^^^^^^^^^^^
                                         This is your Folder ID
```

---

## API Endpoints

### OAuth

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/files/gdrive/auth/url` | Get OAuth authorization URL |
| `GET` | `/api/files/gdrive/auth/callback` | OAuth callback handler |
| `GET` | `/api/files/gdrive/accounts` | List connected accounts |

### Locations

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/files/locations` | Create location (local or gdrive) |
| `POST` | `/api/files/locations/{id}/scan` | Trigger scan |

---

## Security

### Token Encryption
- Fernet encryption (AES-128)
- PBKDF2 key derivation (100k iterations)
- Tokens never exposed via API responses

### OAuth Scope
Using `drive.readonly`:
- Read-only access to Drive files
- Works for My Drive and Shared Drives
- User explicitly grants folder access

### Path Security
- Google Drive: Only accesses explicitly granted folders
- Local: Restricted to `FILES_ROOT` directory

---

## Troubleshooting

### "Invalid OAuth credentials"
- Check `.env` has correct Client ID/Secret
- Verify redirect URI matches exactly
- Restart backend after env changes

### "Folder not found"
- Verify folder ID is correct
- Check folder is shared with connected account
- For Shared Drives, enable `gdrive_include_shared_drives`

### "ENCRYPTION_KEY not set"
Generate one:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Files not appearing
- Check for CSV/Excel files (not Google Sheets)
- Verify account has folder access
- Check backend logs: `docker logs nex-backend-dev`

---

## Production Deployment

### Update Redirect URIs
Add production URLs to Google Cloud Console:
```
https://yourdomain.com/files/locations
https://api.yourdomain.com/api/files/gdrive/auth/callback
```

### Environment Variables
- Use unique `ENCRYPTION_KEY` (never reuse from dev)
- Set production `GOOGLE_OAUTH_REDIRECT_URI`
- Configure persistent `FILES_CACHE_ROOT`

### OAuth Consent Screen
- Publish the OAuth app if using "External"
- Add privacy policy and terms of service URLs

---

## Limitations (MVP)

| Limitation | Workaround |
|------------|------------|
| Google Sheets/Docs not supported | Export to CSV/Excel manually |
| No real-time watching | Use manual "Scan Now" |
| Synchronous scans | Most folders < 30 seconds |

---

## Related Documentation

- [Files Feature Overview](./files.md)
- [Environment Variables](../setup/ENVIRONMENT_VARIABLES.md)
- [API Reference](../api.md)
