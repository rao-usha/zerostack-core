# Files Feature - Quick Setup

## ✅ What's Been Built

The complete **Files** feature has been implemented with:

### Backend
- ✅ Domain models (`backend/domains/files/models.py`)
- ✅ Service layer with CSV/Excel parsing (`backend/domains/files/service.py`)
- ✅ FastAPI router with all endpoints (`backend/domains/files/router.py`)
- ✅ Database migration (`backend/migrations/versions/017_add_files_domain.py`)
- ✅ Router registered in `backend/main.py`

### Frontend
- ✅ API client functions (`frontend/src/api/client.ts`)
- ✅ File Locations page (`frontend/src/pages/FileLocations.tsx`)
- ✅ File Inventory page (`frontend/src/pages/FileInventory.tsx`)
- ✅ File Asset Detail page (`frontend/src/pages/FileAssetDetail.tsx`)
- ✅ Routes added to `frontend/src/App.tsx`
- ✅ "Files" navigation item in `frontend/src/components/Layout.tsx`

---

## 🚀 Next Steps to Use It

### 1. Add FILES_ROOT Environment Variable

Add this line to your `.env` file:

```bash
# Files Feature - Root directory for file access
FILES_ROOT=C:\Users\awron\Desktop
```

Or choose any folder you want to scan for files. **Important:** All file locations must be within this root directory for security.

### 2. Install Required Python Packages

```bash
cd backend
pip install pandas openpyxl xlrd
```

Or add to `requirements.txt`:
```txt
pandas>=2.0.0
openpyxl>=3.1.0
xlrd>=2.0.0
```

### 3. Run Database Migration

Start your backend container first, then run:

```bash
docker exec <your-backend-container> alembic upgrade head
```

Or if running locally:
```bash
cd backend
alembic upgrade head
```

This creates 4 new tables:
- `file_locations`
- `file_assets`
- `file_versions`
- `file_tables`

### 4. Restart Your Application

```bash
# Backend
docker-compose -f docker-compose.dev.yml restart backend

# Frontend (if needed)
docker restart nex-frontend-dev
```

### 5. Access the Feature

Navigate to: **http://localhost:3000/files/locations**

You should see the "Files" item in your left navigation!

---

## 📖 How to Use

### Step 1: Create a File Location
1. Click "Add Location"
2. Enter:
   - **Name**: "My Data Files"
   - **Local Path**: A folder within your FILES_ROOT (e.g., `C:\Users\awron\Desktop\data`)
3. Click "Create Location"

### Step 2: Scan for Files
1. Click "Scan Now" on your location
2. The backend will recursively find all CSV and Excel files
3. It extracts tables and infers schemas automatically

### Step 3: Browse Files
1. Click "Inventory" or navigate directly to `/files/inventory`
2. See all discovered files with their:
   - File size, row count, table count
   - Version history
   - Change indicators

### Step 4: View Details & Preview
1. Click any file to see its detail page
2. View all versions (tracked by content hash)
3. Preview table data (first 100 rows)
4. Publish tables to Datasets (MVP: marks as published)

---

## 🎯 Supported File Types

- ✅ `.csv` - Comma-separated values
- ✅ `.tsv` - Tab-separated values
- ✅ `.xlsx` - Excel 2007+ format
- ✅ `.xls` - Older Excel format

Each CSV/TSV becomes 1 table.
Each Excel file can have multiple tables (one per sheet).

---

## 🔒 Security Features

1. **Path Restriction**: All locations must be within FILES_ROOT
2. **Read-Only**: Never modifies or deletes files
3. **Content Hashing**: Detects changes without storing full file content
4. **Soft Deletes**: Locations are deactivated, not removed

---

## 📊 Example Use Case

**Scenario:** You have monthly sales reports in Excel files on your Desktop.

1. **Create Location:**
   - Name: "Sales Reports"
   - Path: `C:\Users\awron\Desktop\sales-reports`

2. **Scan:**
   - Finds: `2024-01.xlsx`, `2024-02.xlsx`, `2024-03.xlsx`
   - Each has sheets: "Sales", "Returns", "Summary"
   - Creates 3 files × 3 sheets = 9 tables

3. **Preview:**
   - Click `2024-03.xlsx`
   - Select "Sales" sheet
   - See first 100 rows with proper column types

4. **Publish:**
   - Click "Publish to Datasets"
   - (MVP: marks as published for future Dataset integration)

5. **Version Tracking:**
   - You update `2024-03.xlsx`
   - Next scan detects new version by content hash
   - Old version preserved in history

---

## 🛠️ Troubleshooting

### Migration Error

If migration fails:
```bash
cd backend
alembic current  # Check current state
alembic upgrade head  # Run migrations
```

### Files Not Found

Check:
1. Is the path within FILES_ROOT?
2. Does the backend container have access to that path?
3. For Docker on Windows, you may need to share the drive in Docker settings

### Import Errors

If you see `ModuleNotFoundError: No module named 'pandas'`:
```bash
docker exec <backend-container> pip install pandas openpyxl xlrd
```

---

## 📚 Full Documentation

See `FILES_FEATURE_README.md` for:
- Complete API documentation
- Database schema details
- Security considerations
- Future enhancement roadmap
- Troubleshooting guide

---

## 🎉 You're Ready!

The Files feature is fully integrated. Just:
1. Add `FILES_ROOT` to `.env`
2. Install Python packages
3. Run migration
4. Restart containers
5. Visit http://localhost:3000/files/locations

Happy file exploring! 🚀
