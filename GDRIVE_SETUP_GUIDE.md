# Google Drive Integration - Setup Guide

## 🚀 Overview

The Files feature now supports **both local folders AND Google Drive folders**! This allows you to:
- Scan Google Drive folders for CSV and Excel files
- Support "My Drive" and Shared Drives
- Track file versions automatically
- Preview and publish Drive files just like local files

---

## 📋 Prerequisites

### 1. Python Dependencies

Install required Google packages:

```bash
cd backend
pip install google-api-python-client google-auth google-auth-oauthlib cryptography
```

Or add to `requirements.txt`:
```txt
google-api-python-client>=2.100.0
google-auth>=2.23.0
google-auth-oauthlib>=1.1.0
cryptography>=41.0.0
```

### 2. Google Cloud Project Setup

**Create a Google Cloud Project:**

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable the **Google Drive API**:
   - Go to "APIs & Services" > "Library"
   - Search for "Google Drive API"
   - Click "Enable"

**Create OAuth 2.0 Credentials:**

1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth client ID"
3. Application type: **Web application**
4. Name: "NEX.AI Files Integration"
5. Authorized redirect URIs:
   ```
   http://localhost:3000/files/locations
   http://localhost:8000/api/files/gdrive/auth/callback
   ```
   (Add production URLs when deploying)
6. Click "Create"
7. **Save the Client ID and Client Secret** - you'll need these!

**Configure OAuth Consent Screen:**

1. Go to "OAuth consent screen"
2. User Type: **Internal** (for organization) or **External** (for public)
3. Fill in app information:
   - App name: NEX.AI
   - User support email: your email
   - Developer contact: your email
4. Add scopes:
   - `https://www.googleapis.com/auth/drive.readonly` (recommended)
   - OR `https://www.googleapis.com/auth/drive.file` (more restrictive)
5. Save and continue

---

## ⚙️ Environment Configuration

Add these variables to your `.env` file:

```bash
# Google Drive OAuth
GOOGLE_OAUTH_CLIENT_ID=your-client-id-here.apps.googleusercontent.com
GOOGLE_OAUTH_CLIENT_SECRET=your-client-secret-here
GOOGLE_OAUTH_REDIRECT_URI=http://localhost:8000/api/files/gdrive/auth/callback
GOOGLE_OAUTH_SCOPES=https://www.googleapis.com/auth/drive.readonly

# Files cache (for downloaded Drive files)
FILES_CACHE_ROOT=C:\Users\awron\AppData\Local\nex_files_cache

# Encryption key for storing OAuth tokens
ENCRYPTION_KEY=your-secure-random-key-here-min-32-chars

# Optional: Reuse existing SECRET_KEY if available
# If ENCRYPTION_KEY is not set, will fallback to SECRET_KEY
```

### 🔐 **Generating ENCRYPTION_KEY**

```bash
# Python
python -c "import secrets; print(secrets.token_urlsafe(32))"

# PowerShell
-join ((65..90) + (97..122) + (48..57) | Get-Random -Count 32 | % {[char]$_})
```

---

## 🗄️ Database Migration

Run the migration to add Google Drive support:

```bash
cd backend
docker exec <backend-container> alembic upgrade head
```

Or locally:
```bash
cd backend
alembic upgrade head
```

This creates:
- `external_accounts` table (OAuth credentials)
- New columns in `file_locations` (gdrive_folder_id, external_account_id, etc.)

---

## 🎯 Using Google Drive Integration

### 1. Connect Your Google Account

1. Navigate to **Files > Locations** in NEX.AI
2. Click **"Add Location"**
3. Select **"Google Drive"** tab
4. Click **"Connect Google Drive"**
5. A Google OAuth window opens:
   - Sign in with your Google account
   - Grant permissions to NEX.AI
   - Window closes automatically
6. Your account appears in the dropdown

### 2. Create a Google Drive Location

1. After connecting, fill in:
   - **Name**: "My Sales Reports"
   - **Google Account**: Select from dropdown
   - **Folder ID**: Copy from Drive URL
   - **Include Shared Drives**: Check if you want shared drives included

**Getting Folder ID:**
- Open Google Drive in browser
- Navigate to the folder you want to scan
- Copy ID from URL:
  ```
  https://drive.google.com/drive/folders/1a2B3c4D5e6F7g8H9i0J
                                           ^^^^^^^^^^^^^^^^^^^^
                                           This is your Folder ID
  ```

2. Click **"Create Location"**
3. Click **"Scan Now"** to start scanning!

### 3. Scanning Behavior

The scan will:
- ✅ Recursively list all files in the folder
- ✅ Support both "My Drive" and Shared Drives
- ✅ Filter for CSV, XLS, XLSX files only
- ✅ Skip Google-native files (Docs/Sheets/Slides) for MVP
- ✅ Download files to cache (`FILES_CACHE_ROOT`)
- ✅ Compute content hashes (MD5 from Drive or SHA256)
- ✅ Create FileAsset and FileVersion records
- ✅ Extract tables and infer schemas
- ✅ Reuse existing file parsing pipeline

---

## 🔒 Security Features

### Token Encryption

- **Access tokens** and **refresh tokens** are encrypted at rest using Fernet (AES)
- Encryption key derived from `ENCRYPTION_KEY` with PBKDF2
- Tokens never exposed via API responses
- Automatic token refresh when expired

### Path Security

- **Google Drive:** Only accesses folders user explicitly grants access to
- **Local:** Still restricted to `FILES_ROOT` directory

### OAuth Scope Strategy

**MVP uses `drive.readonly`:**
- ✅ Read-only access to all Drive files
- ✅ Simplest setup
- ✅ Works for "My Drive" and Shared Drives

**Alternative: `drive.file`:**
- ⚠️ Only accesses files created by the app
- ⚠️ More restrictive but less useful for scanning existing folders

**Recommendation:** Use `drive.readonly` for file scanning use case.

---

## 🧪 Testing

### 1. Test Local OAuth Flow

```bash
# Get auth URL
curl http://localhost:8000/api/files/gdrive/auth/url

# Follow the URL, complete OAuth
# Should redirect to: http://localhost:3000/files/locations?connected=you@gmail.com
```

### 2. List Connected Accounts

```bash
curl http://localhost:8000/api/files/gdrive/accounts
```

### 3. Create GDrive Location

```bash
curl -X POST http://localhost:8000/api/files/locations \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Drive Folder",
    "type": "gdrive",
    "gdrive_folder_id": "YOUR_FOLDER_ID",
    "gdrive_include_shared_drives": true,
    "external_account_id": "ACCOUNT_ID_FROM_STEP_2"
  }'
```

### 4. Scan GDrive Location

```bash
curl -X POST http://localhost:8000/api/files/locations/{LOCATION_ID}/scan
```

---

## 🐛 Troubleshooting

### "Invalid OAuth credentials"

**Problem:** GOOGLE_OAUTH_CLIENT_ID or CLIENT_SECRET not set or incorrect

**Solution:**
1. Check `.env` file has correct values
2. Verify credentials in Google Cloud Console
3. Ensure redirect URI matches exactly (including http/https)
4. Restart backend container/process

### "Folder not found" or "Permission denied"

**Problem:** User doesn't have access to the folder

**Solution:**
1. Verify folder ID is correct
2. Check folder is shared with the connected Google account
3. For Shared Drives, ensure `gdrive_include_shared_drives=true`
4. Reconnect Google account with proper permissions

### "ENCRYPTION_KEY not set"

**Problem:** Token encryption requires ENCRYPTION_KEY

**Solution:**
```bash
# Add to .env
ENCRYPTION_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
```

### OAuth window doesn't open

**Problem:** Pop-up blocked by browser

**Solution:**
- Allow pop-ups for localhost:3000
- Or manually copy/paste the auth URL into a new tab

### "Token expired" errors

**Problem:** Refresh token invalid or revoked

**Solution:**
1. Reconnect the Google account
2. Check if user revoked access in Google Account settings
3. Verify `refresh_token_encrypted` is stored in database

### Files not appearing after scan

**Possible causes:**
1. Folder contains no CSV/Excel files
2. Files are Google-native (Docs/Sheets) - not supported in MVP
3. Permission issues
4. Network/firewall blocking Drive API requests

**Debug:**
- Check backend logs: `docker logs nex-backend-dev`
- Verify file extensions: `.csv`, `.xlsx`, `.xls`, `.tsv` only
- Test with a simple folder with 1-2 CSV files first

---

## 📊 Architecture

### Database Schema

**external_accounts**
- Stores encrypted OAuth tokens
- One account can be used for multiple locations
- Tokens automatically refreshed

**file_locations (updated)**
- New fields: `gdrive_folder_id`, `external_account_id`, `auth_provider`
- `type` enum: "local" | "gdrive"

**file_assets**
- `provider_file_id` stores Google Drive file ID
- Same versioning logic for both local and Drive files

### File Caching

Google Drive files are downloaded to:
```
{FILES_CACHE_ROOT}/
  {location_id}/
    {file_id}/
      {content_hash}/
        original_filename.xlsx
```

Benefits:
- Faster repeat scans (don't re-download unchanged files)
- Works offline once cached
- Reuses existing CSV/Excel parsers

---

## 🚀 Production Deployment

### 1. Update Redirect URIs

Add production URLs to Google Cloud Console:
```
https://yourdomain.com/files/locations
https://api.yourdomain.com/api/files/gdrive/auth/callback
```

### 2. Environment Variables

Ensure production `.env` has:
- Valid `GOOGLE_OAUTH_CLIENT_ID` and `CLIENT_SECRET`
- Secure `ENCRYPTION_KEY` (never reuse from dev!)
- Production `GOOGLE_OAUTH_REDIRECT_URI`
- Persistent `FILES_CACHE_ROOT` (e.g., mounted volume)

### 3. OAuth Consent Screen

- Publish the OAuth app (if using "External" type)
- Submit for verification if needed
- Add privacy policy and terms of service URLs

### 4. Monitoring

- Monitor token refresh failures
- Track cache disk usage
- Log scan durations and error rates

---

## 🎉 You're Ready!

The Google Drive integration is fully implemented and ready to use. Just:

1. ✅ Install Google API Python packages
2. ✅ Create Google Cloud project + OAuth credentials
3. ✅ Add environment variables to `.env`
4. ✅ Run database migration
5. ✅ Restart backend
6. ✅ Connect Google account in UI
7. ✅ Scan your first Drive folder!

For any issues, check the troubleshooting section or review backend logs.

Happy Drive exploring! ☁️🚀
