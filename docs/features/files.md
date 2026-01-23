# Files Feature

The Files feature enables scanning, versioning, and managing data files from multiple sources including local folders and cloud storage.

## Overview

The Files feature provides:
- **Multi-Source Support**: Local folders, Google Drive (more coming)
- **Automatic Scanning**: Discover CSV, Excel, TSV files
- **Version Tracking**: Content-hash based versioning
- **Table Extraction**: Parse files into queryable tables
- **Publishing**: Promote file tables to Datasets

## Supported File Types

| Type | Extensions |
|------|------------|
| CSV | `.csv` |
| TSV | `.tsv` |
| Excel | `.xls`, `.xlsx` |

---

## Quick Start

### Local Folders

1. Configure `FILES_ROOT` in `.env`:
   ```bash
   FILES_ROOT=C:\Users\awron\data
   ```

2. Navigate to **Files** → **Locations**
3. Click **Add Location** → **Local Folder**
4. Enter folder path (relative to FILES_ROOT)
5. Click **Create Location**
6. Click **Scan Now**

### Google Drive

See [Google Drive Integration](./gdrive-integration.md) for setup.

---

## Concepts

### Locations

A location represents a scannable source:

| Field | Description |
|-------|-------------|
| `name` | Display name |
| `type` | `local` or `gdrive` |
| `path` | Local path or Drive folder ID |
| `last_scanned` | Last scan timestamp |

### File Assets

Discovered files within locations:

| Field | Description |
|-------|-------------|
| `filename` | Original file name |
| `file_size` | Size in bytes |
| `content_hash` | SHA256 or MD5 hash |
| `provider_file_id` | Google Drive file ID (if applicable) |

### File Versions

Track changes over time:

| Field | Description |
|-------|-------------|
| `version_number` | Auto-incrementing |
| `content_hash` | Hash for this version |
| `discovered_at` | When version was found |

### File Tables

Extracted tables from files:

| Field | Description |
|-------|-------------|
| `sheet_name` | Excel sheet or "default" |
| `row_count` | Number of rows |
| `column_count` | Number of columns |
| `schema` | Inferred column types |

---

## Scanning Behavior

When you click **Scan Now**:

1. **Discovery**: List all files in location
2. **Filtering**: Keep only supported types
3. **Hashing**: Compute content hash
4. **Comparison**: Check for new/changed files
5. **Extraction**: Parse new files into tables
6. **Schema Inference**: Detect column types

### Change Detection

- Files with same hash → skip (no changes)
- Files with new hash → create new version
- New files → create asset + version

---

## API Endpoints

### Locations

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/files/locations` | List locations |
| `POST` | `/api/files/locations` | Create location |
| `DELETE` | `/api/files/locations/{id}` | Delete location |
| `POST` | `/api/files/locations/{id}/scan` | Trigger scan |

### Assets

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/files/locations/{id}/assets` | List file assets |
| `GET` | `/api/files/assets/{id}` | Get asset details |
| `GET` | `/api/files/assets/{id}/versions` | Get version history |

### Tables

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/files/assets/{id}/tables` | List extracted tables |
| `GET` | `/api/files/tables/{id}/preview` | Preview table data |
| `POST` | `/api/files/tables/{id}/publish` | Publish to Datasets |

---

## File Caching

For cloud sources, files are cached locally:

```
{FILES_CACHE_ROOT}/
  {location_id}/
    {file_id}/
      {content_hash}/
        original_filename.xlsx
```

Benefits:
- Faster repeat scans
- Offline access after initial download
- Reuses existing parsers

---

## Configuration

### Environment Variables

```bash
# Local files root directory
FILES_ROOT=C:\Users\awron\data

# Cache for downloaded cloud files  
FILES_CACHE_ROOT=C:\Users\awron\AppData\Local\nex_files_cache
```

---

## Publishing to Datasets

Once a file is scanned and parsed:

1. Go to **Files** → select a location
2. Click on a file asset
3. Select a table (sheet)
4. Click **Publish to Datasets**
5. Table becomes available in Data Explorer

---

## Supported Sources

| Source | Status | Notes |
|--------|--------|-------|
| Local Folder | ✅ Available | Paths within FILES_ROOT |
| Google Drive | ✅ Available | See [GDrive docs](./gdrive-integration.md) |
| SharePoint | 🔜 Planned | Similar OAuth flow |
| S3 | 🔜 Planned | IAM credentials |
| Dropbox | 🔜 Planned | OAuth integration |

---

## Related Documentation

- [Google Drive Integration](./gdrive-integration.md)
- [Data Explorer](../guides/START_DATA_EXPLORER.md)
- [Environment Variables](../setup/ENVIRONMENT_VARIABLES.md)
