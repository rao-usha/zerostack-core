# Files Feature - Complete Guide

## Overview

The **Files** feature allows you to:
- **Register local folders** on your machine as "File Locations"
- **Scan folders recursively** for CSV and Excel files  
- **Automatically track file versions** by content hash
- **Extract tables from files** (CSV = 1 table, Excel = 1 table per sheet)
- **Preview table data** with schema inference
- **Publish tables** to the Datasets domain (MVP: marks as published)

---

## 🚀 Quick Start

### 1. Set Up Environment Variables

Add to your `.env` file:

```bash
# Files Feature - Root directory for file access (security constraint)
# All file paths must be within this root directory
FILES_ROOT=C:\Users\YourName

# Or for Linux/Mac:
# FILES_ROOT=/home/yourname
```

**Important:** 
- This restricts which folders the backend can access for security
- All file locations must be within this root directory
- For Windows, use forward slashes or escaped backslashes

### 2. Run Database Migration

```bash
cd backend
docker exec -it nex-backend-dev alembic upgrade head
```

Or if running locally:
```bash
cd backend
alembic upgrade head
```

This creates the following tables:
- `file_locations` - Configured folder locations
- `file_assets` - Discovered files
- `file_versions` - File versions (tracked by content hash)
- `file_tables` - Extracted tables from files

### 3. Install Python Dependencies

The Files feature requires these packages (add to `requirements.txt` if missing):

```txt
pandas>=2.0.0
openpyxl>=3.1.0  # For Excel (.xlsx) support
xlrd>=2.0.0      # For older Excel (.xls) support
```

Install:
```bash
pip install pandas openpyxl xlrd
```

### 4. Start the Application

```bash
# Backend (if not already running)
cd backend
docker-compose -f docker-compose.dev.yml up backend

# Frontend (if not already running)
cd frontend
npm run dev
```

### 5. Access the Files Feature

Navigate to: **http://localhost:3000/files/locations**

---

## 📖 User Guide

### Creating a File Location

1. Go to **Files** in the left navigation
2. Click **"Add Location"**
3. Fill in:
   - **Name**: A friendly name (e.g., "Desktop Data Files")
   - **Local Path**: Full path to folder (e.g., `C:\Users\YourName\Desktop\data`)
4. Click **"Create Location"**

**Security Note:** The path MUST be within your configured `FILES_ROOT`.

### Scanning a Location

1. Find your location in the list
2. Click **"Scan Now"**
3. The backend will:
   - Walk the directory recursively
   - Find all `.csv`, `.xlsx`, `.xls`, `.tsv` files
   - Compute content hashes to detect changes
   - Extract tables and infer schemas
   - Store metadata in Postgres

### Viewing Files

1. Click **"Inventory"** (or go to `/files/inventory`)
2. Use filters:
   - **Search** by file name or path
   - **Filter by location**
   - **Show changes only** to see new versions
3. Click any file to view details

### Viewing File Details

On the file detail page you can:

**Versions Tab:**
- See all detected versions
- View modified date, size, content hash
- Compare versions over time

**Tables Tab:**
- View extracted tables (sheets for Excel)
- See row/column counts
- Preview table data (first 100 rows)
- Publish to Datasets

### Publishing a Table

1. Go to file detail page
2. Select a table
3. Click **"Publish to Datasets"**
4. (MVP: marks as published; future: creates Dataset record)

---

## 🔧 API Endpoints

### File Locations

```http
# Create location
POST /api/files/locations
{
  "name": "My Data Folder",
  "local_path": "C:\\Users\\Me\\data",
  "type": "local"
}

# List locations
GET /api/files/locations

# Get location
GET /api/files/locations/{location_id}

# Update location
PATCH /api/files/locations/{location_id}
{
  "name": "Updated Name",
  "is_active": true
}

# Delete location (soft delete)
DELETE /api/files/locations/{location_id}

# Scan location
POST /api/files/locations/{location_id}/scan
```

### File Assets

```http
# List all files
GET /api/files/assets

# List files in a location
GET /api/files/assets?location_id={location_id}

# Get file detail
GET /api/files/assets/{asset_id}
```

### Table Operations

```http
# Preview table data
POST /api/files/tables/preview
{
  "table_id": "...",
  "limit": 100,
  "offset": 0
}

# Publish table
POST /api/files/tables/{table_id}/publish
{
  "dataset_name": "optional_name",
  "description": "optional description"
}
```

---

## 🗂️ Database Schema

### file_locations
- `id` (UUID, PK)
- `name` (string) - User-friendly name
- `type` (string) - "local" (future: "google_drive", etc.)
- `local_path` (string) - Absolute file system path
- `is_active` (boolean)
- `last_scanned_at` (timestamp)
- `created_at`, `updated_at`

### file_assets
- `id` (UUID, PK)
- `location_id` (UUID, FK)
- `relative_path` (string) - Path relative to location root
- `file_name` (string)
- `ext` (string) - File extension
- `last_seen_at` (timestamp)
- `created_at`

### file_versions
- `id` (UUID, PK)
- `file_asset_id` (UUID, FK)
- `detected_at` (timestamp) - When we discovered this version
- `modified_at` (timestamp) - File's actual modification time
- `size_bytes` (bigint)
- `content_hash` (string) - SHA-256 hash
- `row_count_estimate` (int, nullable)

### file_tables
- `id` (UUID, PK)
- `file_version_id` (UUID, FK)
- `table_name` (string) - Sheet name (Excel) or file name (CSV)
- `row_count`, `column_count` (int)
- `schema_json` (text) - JSON array of column schemas
- `sample_data_json` (text, nullable) - First 5 rows
- `is_published` (boolean)
- `published_dataset_id` (UUID, nullable)
- `created_at`

---

## 🔒 Security Considerations

### Path Restriction

All file paths MUST be within the configured `FILES_ROOT`. This prevents:
- Arbitrary file system access
- Reading sensitive system files
- Directory traversal attacks

Example:
```python
FILES_ROOT=/home/datauser
✅ Allowed: /home/datauser/projects/data/sales.csv
❌ Blocked: /etc/passwd
❌ Blocked: /home/datauser/../otheruser/private.csv
```

### Read-Only Access

The Files feature only **reads** files. It:
- ✅ Scans directories
- ✅ Reads file metadata (size, modified time)
- ✅ Reads file content for parsing
- ❌ Never modifies or deletes files
- ❌ Never creates new files in scanned directories

### Supported File Types

Currently limited to:
- `.csv` - Comma-separated values
- `.tsv` - Tab-separated values
- `.xlsx` - Excel 2007+ format
- `.xls` - Older Excel format

**Future:** Parquet, JSON, SQLite, Avro, etc.

---

## 🎯 MVP vs Future Features

### ✅ Implemented (MVP)

- Local folder connector
- Recursive scanning
- CSV/Excel parsing (sheets as tables)
- Schema inference
- Content-based versioning
- Table preview (first 100 rows)
- Synchronous scanning
- Basic "publish" flag

### 🚀 Future Enhancements

- **Cloud connectors**: Google Drive, SharePoint, S3, Dropbox
- **Background scanning**: Async jobs with progress tracking
- **Scheduled scans**: Cron-like recurring scans
- **File watching**: Real-time change detection
- **Advanced Excel**: Named ranges, multiple tables per sheet
- **More formats**: Parquet, JSON, SQLite, Feather, HDF5, Avro
- **Dataset integration**: Actually create Dataset records when publishing
- **Data lineage**: Track where published datasets came from
- **Diff view**: Compare versions side-by-side
- **Metadata extraction**: Pull comments, formulas, formatting from Excel
- **Compression**: Handle .zip, .gz files
- **Large file support**: Streaming reads for files >1GB

---

## 🛠️ Troubleshooting

### "Path outside allowed root" error

**Problem:** File location path is not within `FILES_ROOT`

**Solution:**
1. Check your `.env` file: `FILES_ROOT=...`
2. Ensure your path starts with the FILES_ROOT value
3. On Windows, use consistent path separators

### Files not showing up after scan

**Possible causes:**
1. File extension not supported (only CSV/Excel currently)
2. File is hidden or in a hidden directory
3. Permission issues (backend can't read the file)

**Debug:**
- Check backend logs: `docker logs nex-backend-dev`
- Verify file permissions
- Try scanning a simpler folder first

### Excel file parsing errors

**Problem:** "Error reading Excel file"

**Solutions:**
1. Ensure `openpyxl` is installed: `pip install openpyxl`
2. For old `.xls` files, install `xlrd`: `pip install xlrd`
3. Check if file is corrupted (try opening in Excel)
4. Check if file is password-protected (not supported)

### Migration fails

**Problem:** Alembic migration error

**Solution:**
```bash
# Check current migration state
cd backend
alembic current

# If stuck, try:
alembic stamp head  # Mark as up-to-date
alembic upgrade head  # Run migrations
```

---

## 📚 Code Structure

```
backend/domains/files/
├── __init__.py
├── models.py          # SQLModel tables + Pydantic schemas
├── service.py         # Business logic (scanning, parsing, hashing)
├── router.py          # FastAPI endpoints

backend/migrations/versions/
└── 017_add_files_domain.py  # Database migration

frontend/src/
├── api/client.ts      # API functions + TypeScript types
└── pages/
    ├── FileLocations.tsx      # /files/locations
    ├── FileInventory.tsx      # /files/inventory
    └── FileAssetDetail.tsx    # /files/assets/:id
```

---

## 🤝 Contributing

To extend the Files feature:

1. **Add new file type support:**
   - Update `FileExtension` enum in `models.py`
   - Add parser in `service.py` → `_extract_tables()`
   - Example: Add JSON support

2. **Add cloud connector:**
   - Add new `LocationType` enum value
   - Create connector service (e.g., `google_drive_connector.py`)
   - Update `scanLocation()` to route by type

3. **Improve schema inference:**
   - Enhance `_infer_schema()` in `service.py`
   - Add data type detection (dates, currencies, enums)

---

## 📝 Example Workflow

1. **Create location:**
   ```
   Name: Sales Data
   Path: C:\Users\Me\Desktop\sales-reports
   ```

2. **Scan:**
   - Finds: `2024-Q1.xlsx`, `2024-Q2.xlsx`, `customers.csv`
   - Creates 3 `FileAsset` records
   - Creates 3 `FileVersion` records
   - Extracts tables (Excel sheets)

3. **User edits `2024-Q1.xlsx`:**
   - Next scan detects changed content hash
   - Creates new `FileVersion` record
   - Old version preserved for history

4. **Publish table:**
   - User selects "Q1 Sales" sheet
   - Clicks "Publish to Datasets"
   - Table marked as `is_published=true`

---

## 🎉 You're All Set!

The Files feature is now fully integrated into your NEX.AI platform. Start by:

1. Adding a file location pointing to your desktop or data folder
2. Scanning it to discover files
3. Exploring the inventory and previewing tables
4. Publishing useful tables to Datasets

For questions or issues, check the troubleshooting section or review the backend logs.

Happy data exploring! 🚀
