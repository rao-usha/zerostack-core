# Nex Database Setup Guide

This guide explains how to initialize the Nex database from scratch.

## 🚀 Quick Start (Recommended)

### For Windows Users

From the project root, run:

```bash
setup_nex_db.bat
```

### For Mac/Linux Users

From the project root, run:

```bash
chmod +x setup_nex_db.sh
./setup_nex_db.sh
```

This will:
1. Start Docker containers if needed
2. Create the `nex` database
3. Run all Alembic migrations (001 → 008)
4. Seed default prompt recipes

---

## 📋 What Gets Created

### Database Tables

1. **`chat_conversations`** - Chat session storage
2. **`chat_messages`** - Individual chat messages
3. **`ai_analysis_results`** - Stored analysis results
4. **`analysis_jobs`** - Asynchronous job queue
5. **`prompt_recipes`** - Editable prompt templates
6. **`data_dictionary_entries`** - Column-level documentation
7. **`alembic_version`** - Migration tracking

### Default Data

- **7 Prompt Recipes** (one for each analysis type):
  - Data Profiling
  - Data Quality Checks
  - Outlier & Anomaly Detection
  - Relationship Analysis
  - Trend & Time-Series Analysis
  - Pattern Discovery
  - Column Documentation

---

## 🛠️ Manual Setup Options

### Option 1: Run Inside Docker Container

```bash
# Exec into the backend container
docker exec -it nex-backend-dev bash

# Run the setup script
cd /app
bash scripts/setup_database.sh
```

### Option 2: Run Locally (if you have PostgreSQL + Python)

#### Using Bash:
```bash
cd backend
bash scripts/setup_database.sh
```

#### Using PowerShell:
```powershell
cd backend
.\scripts\setup_database.ps1
```

---

## 🔧 Advanced: Step-by-Step Manual Setup

If you need to run each step individually:

### 1. Create Database

```bash
docker exec nex-postgres-dev psql -U postgres -c "CREATE DATABASE nex;"
```

### 2. Run Migrations

```bash
docker exec nex-backend-dev alembic upgrade head
```

### 3. Seed Prompt Recipes

```bash
docker exec nex-backend-dev python scripts/seed_prompt_recipes.py
```

### 4. Verify Setup

```bash
docker exec nex-backend-dev alembic current
```

---

## 🔄 Reset Database (Fresh Start)

To completely reset and rebuild the database:

### For Windows:
```batch
docker exec nex-postgres-dev psql -U postgres -c "DROP DATABASE IF EXISTS nex;"
setup_nex_db.bat
```

### For Mac/Linux:
```bash
docker exec nex-postgres-dev psql -U postgres -c "DROP DATABASE IF EXISTS nex;"
./setup_nex_db.sh
```

---

## 📊 Migration History

The current migrations in order:

```
001_bootstrap          - Initial chat tables
002_add_chat_tables    - Extended chat functionality
003_ai_analysis        - AI analysis results
004_metadata           - Enhanced metadata fields
005_jobs               - Async job system
006_recipes            - Prompt recipe system
007_recipe_fields      - Recipe integration with jobs
008_dictionary         - Data dictionary entries
```

---

## 🔍 Troubleshooting

### Issue: "Database already exists"

**Solution:** The script will skip creation if it exists. To reset:

```bash
docker exec nex-postgres-dev psql -U postgres -c "DROP DATABASE nex;"
```

Then re-run the setup script.

### Issue: "Migrations already applied"

**Solution:** This is normal. The script is idempotent and safe to re-run.

### Issue: "Can't connect to PostgreSQL"

**Solutions:**
1. Check if containers are running: `docker ps`
2. Restart services: `docker-compose restart`
3. Check logs: `docker logs nex-postgres-dev`

### Issue: "Alembic version mismatch"

**Solution:** Reset alembic state:

```bash
docker exec nex-postgres-dev psql -U postgres -d nex -c "DROP TABLE IF EXISTS alembic_version;"
```

Then re-run migrations.

### Issue: "Permission denied" on .sh file

**Solution:** Make the script executable:

```bash
chmod +x setup_nex_db.sh
chmod +x backend/scripts/setup_database.sh
```

---

## 🧪 Verify Your Setup

After running the setup, verify everything is working:

1. **Check migrations:**
   ```bash
   docker exec nex-backend-dev alembic current
   ```
   Should show: `008_dictionary (head)`

2. **Check prompt recipes:**
   ```bash
   docker exec nex-postgres-dev psql -U postgres -d nex -c "SELECT COUNT(*) FROM prompt_recipes;"
   ```
   Should show: `7`

3. **Check tables:**
   ```bash
   docker exec nex-postgres-dev psql -U postgres -d nex -c "\dt"
   ```
   Should list all 7 tables.

---

## 📝 Environment Variables

The setup scripts use these environment variables (with defaults):

| Variable | Default | Description |
|----------|---------|-------------|
| `EXPLORER_DB_HOST` | `localhost` | PostgreSQL host |
| `EXPLORER_DB_PORT` | `5432` | PostgreSQL port |
| `EXPLORER_DB_USER` | `postgres` | Database user |
| `EXPLORER_DB_PASSWORD` | `postgres` | Database password |
| `EXPLORER_DB_NAME` | `nex` | Database name |

Override in your `.env` file if needed.

---

## 🎯 Next Steps

After setup completes:

1. **Start the application:**
   ```bash
   docker-compose up
   ```

2. **Access Nex:**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

3. **Try it out:**
   - Go to `/analysis` to run your first analysis
   - Go to `/dictionary` to see column documentation
   - Go to `/chat` to chat with your data

---

## 💡 Tips

- The setup is **idempotent** - safe to run multiple times
- All scripts include **detailed logging** for troubleshooting
- Migrations are **tracked** in `alembic_version` table
- Default recipes can be **edited** in the Prompt Library UI
- The database schema is **documented** in the models

---

## 🆘 Need Help?

- Check the logs: `docker logs nex-backend-dev`
- Verify environment: `docker exec nex-backend-dev env | grep EXPLORER`
- Test connection: `docker exec nex-postgres-dev psql -U postgres -c '\l'`
- Review migrations: `docker exec nex-backend-dev alembic history`

---

**Happy analyzing! 🚀**







