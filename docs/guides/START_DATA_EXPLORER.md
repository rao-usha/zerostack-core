# 🚀 Start Data Explorer - Quick Guide

## Step 1: Configure Your Database Connection

The Data Explorer needs database credentials. Choose ONE of these methods:

### Method A: Create backend/.env file (Recommended)

Create a file at `backend/.env` with:

```bash
# Your database connection details
EXPLORER_DB_HOST=localhost
EXPLORER_DB_PORT=5433
EXPLORER_DB_USER=nexdata
EXPLORER_DB_PASSWORD=nexdata_dev_password
EXPLORER_DB_NAME=nexdata
```

**⚠️ Important:** Adjust these values to match your actual PostgreSQL database!

### Method B: Set in PowerShell (Windows)

Open a PowerShell terminal and run:

```powershell
$env:EXPLORER_DB_HOST="localhost"
$env:EXPLORER_DB_PORT="5433"
$env:EXPLORER_DB_USER="nexdata"
$env:EXPLORER_DB_PASSWORD="nexdata_dev_password"
$env:EXPLORER_DB_NAME="nexdata"
```

---

## Step 2: Start the Backend

**Terminal 1 - Backend:**

```bash
cd backend
python -m uvicorn main:app --reload --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

---

## Step 3: Start the Frontend

**Terminal 2 - Frontend:**

```bash
cd frontend
npm run dev
```

You should see:
```
VITE v5.x.x  ready in xxx ms

➜  Local:   http://localhost:5173/
```

---

## Step 4: Access Data Explorer

1. Open your browser to: **http://localhost:5173**

2. Look for **"Data Explorer"** in the left navigation menu (should be 4th item, with a search icon 🔍)

3. Click on **"Data Explorer"**

4. You should see:
   - **Left sidebar** with schemas and tables
   - **Main area** with tabs: Preview, Columns, Query, Summary

---

## 🎯 What You Should See

### If Connection Successful:
- Left sidebar shows your database schemas
- Click on "public" to expand and see tables
- Click any table to view its data

### If Connection Failed:
- You'll see a red error box with connection details
- Check your environment variables
- Verify PostgreSQL is running:
  ```bash
  psql -h localhost -p 5433 -U nexdata -d nexdata
  ```

---

## 🧪 Quick Test

### Test the API directly:

**PowerShell:**
```powershell
Invoke-WebRequest -Uri "http://localhost:8000/api/v1/data-explorer/health" | Select-Object -Expand Content
```

**Or use your browser:**
Open: http://localhost:8000/api/v1/data-explorer/health

**Expected response if connected:**
```json
{
  "connected": true,
  "database": "nexdata",
  "version": "PostgreSQL 15.x...",
  "host": "localhost",
  "port": 5433
}
```

---

## 🐛 Troubleshooting

### "Database Connection Failed"

1. **Check PostgreSQL is running:**
   ```bash
   # Try connecting manually
   psql -h localhost -p 5433 -U nexdata -d nexdata
   ```

2. **Verify environment variables:**
   ```powershell
   # In the same terminal where you run uvicorn
   echo $env:EXPLORER_DB_HOST
   echo $env:EXPLORER_DB_PORT
   ```

3. **Check if using .env file:**
   - File must be at `backend/.env`
   - No spaces around `=` signs
   - No quotes needed for values

### "I don't see Data Explorer in navigation"

1. **Restart frontend dev server:**
   - Stop the frontend (Ctrl+C)
   - Run `npm run dev` again

2. **Clear browser cache:**
   - Hard refresh: Ctrl+Shift+R (Windows) or Cmd+Shift+R (Mac)

### "Page is blank"

1. **Check browser console:**
   - Press F12
   - Look for errors in Console tab

2. **Check if frontend is running:**
   - Should be on http://localhost:5173
   - Terminal should show "ready in xxx ms"

---

## ✅ Success Checklist

- [ ] Backend running on port 8000
- [ ] Frontend running on port 5173
- [ ] Environment variables set
- [ ] PostgreSQL accessible
- [ ] Can see Data Explorer in left navigation
- [ ] Can click on Data Explorer and see the page
- [ ] Can see schemas in left sidebar

---

## 📸 What to Expect

When you navigate to Data Explorer, you'll see:

```
┌─────────────────────────────────────────────────────────────┐
│ 🔍 Data Explorer                                            │
│ Browse and query your Postgres database                    │
├──────────────┬──────────────────────────────────────────────┤
│              │                                              │
│ SCHEMAS      │  Select a Table                              │
│              │                                              │
│ ▼ public (5) │  Choose a table from the sidebar            │
│   📄 users   │  to explore its data                         │
│   📄 orders  │                                              │
│   📄 items   │                                              │
│              │                                              │
└──────────────┴──────────────────────────────────────────────┘
```

---

Need more help? Check:
- `DATA_EXPLORER_QUICKSTART.md` - Detailed guide
- `backend/DATA_EXPLORER.md` - Full documentation
- `DATA_EXPLORER_ENV_SETUP.md` - Environment setup details

