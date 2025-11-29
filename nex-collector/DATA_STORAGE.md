# Data Storage

This document explains where data is stored and how to access it.

## Storage Locations

The NEX Context Aggregator stores data in two places:

### 1. Database (PostgreSQL)

**Location**: Shared `nex_db` container (same as main NEX)

**Database Name**: `nex_collector`

**Contains**:
- ContextDocs (context documents)
- ContextVariants (faceted variants)
- Chunks (text chunks with embeddings)
- FeatureVectors (extracted features)
- SyntheticExamples (generated examples)
- TeacherRuns (LLM outputs)
- Targets (distilled labels)
- DatasetManifests (dataset metadata)

**Access**:
```powershell
# Connect to database
docker exec -it nex_db psql -U nex -d nex_collector

# List tables
docker exec -it nex_db psql -U nex -d nex_collector -c "\dt"

# Backup database
docker exec nex_db pg_dump -U nex nex_collector > backup.sql
```

### 2. Dataset Files (JSONL/Parquet)

**Location**: `nex-collector/data/` (local filesystem)

**Structure**:
```
data/
├── packs/                    # Fine-tune packs
│   └── {name}@{version}/
│       ├── train.jsonl      # Training examples (90%)
│       ├── eval.jsonl       # Evaluation examples (10%)
│       └── manifest.json    # Metadata
└── {name}/                  # Other dataset types
    └── {version}/
        ├── examples.parquet
        ├── targets.parquet
        └── manifest.json
```

**Access from Host**:
```powershell
# List files
cd nex-collector
dir data\packs

# View a file
type data\packs\insurance-underwriter-risk-assessment@1.0.0\manifest.json
```

**Access from Container**:
```powershell
# List files
docker-compose exec api ls -la /code/data/

# View a file
docker-compose exec api cat /code/data/packs/my-pack@1.0.0/manifest.json
```

## Configuration

### Change Data Directory

Set `DATA_DIR` environment variable:

```bash
DATA_DIR=/path/to/custom/data
```

Default: `./data` (local) or `/code/data` (Docker)

## Finding Your Data

### Database

```powershell
# List databases
docker exec nex_db psql -U nex -d postgres -c "\l"

# Connect to nex_collector database
docker exec -it nex_db psql -U nex -d nex_collector
```

### Files

```powershell
# From project root
cd nex-collector
dir data

# Or from container
docker-compose exec api ls -la /code/data
```

## Backup & Restore

### Backup Database

```powershell
# Backup
docker exec nex_db pg_dump -U nex nex_collector > backup.sql

# Restore
docker exec -i nex_db psql -U nex nex_collector < backup.sql
```

### Backup Files

```powershell
# Copy entire data directory
xcopy /E /I nex-collector\data backup\data

# Or specific dataset
xcopy /E /I nex-collector\data\packs backup\packs
```

## Data Persistence

- **Database**: Persists in Docker volume (survives container restarts)
- **Files**: Stored on local filesystem (persists unless deleted)

**Note**: Using `docker-compose down -v` will remove volumes and delete database data.

