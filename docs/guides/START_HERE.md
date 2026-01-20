# 🚀 ZeroStack - START HERE - Quick Setup

## Prerequisites

Before starting, ensure you have:
- **Python 3.8+** - `python3 --version`
- **Node.js 18+** - `node --version`
- **PostgreSQL** - Running locally or via Docker

## One-Command Installation

From the project root directory, run:

```bash
./scripts/install_all.sh
```

This will automatically install everything!

---

## Step-by-Step Instructions

### 1️⃣ Clone and Navigate to Project

```bash
cd /path/to/zerostack
```

### 2️⃣ Install Dependencies

```bash
./scripts/install_all.sh
```

The script will:
- ✅ Install Node.js dependencies
- ✅ Install all backend packages
- ✅ Install all frontend packages
- ✅ Create start scripts

### 3️⃣ Start the Application

**Terminal 1 - Backend:**
```bash
cd backend
source venv/bin/activate  # On Windows: venv\Scripts\activate
uvicorn main:app --reload --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

### 4️⃣ Open Your Browser

Go to: **http://localhost:3000**

---

## What's Being Installed

### Backend Packages
- FastAPI (web framework)
- Pandas (data analysis)
- Scikit-learn (machine learning)
- NumPy, SciPy (math libraries)
- SQLAlchemy, Alembic (database)
- And 50+ more packages

### Frontend Packages
- React 18 (UI framework)
- TypeScript (programming language)
- Tailwind CSS (styling)
- Vite (build tool)
- And 100+ more packages

---

## Quick Test

Once running:
1. Navigate to the Dashboard
2. Upload a CSV file via "Data Explorer"
3. Go to "Insights" to see AI analysis
4. Try "Chat" to ask questions about your data

---

## Need Help?

Check if everything is ready:
```bash
./scripts/check_setup.sh
```

See detailed guides:
- `docs/guides/QUICKSTART.md` - Quick start guide
- `docs/setup/DATABASE_SETUP.md` - Database configuration
- `docs/development.md` - Development guide

---

## TL;DR

```bash
# Step 1: Install everything
./scripts/install_all.sh

# Step 2: Start backend (Terminal 1)
cd backend && source venv/bin/activate && uvicorn main:app --reload

# Step 3: Start frontend (Terminal 2)
cd frontend && npm run dev

# Step 4: Open browser
open http://localhost:3000
```

That's it! 🎉
