# Nex (zerostack) Feature Status

> **Last Updated:** January 2026

This document provides an overview of all features in the Nex AI Data Platform, their current implementation state, and what is complete vs incomplete.

---

## Quick Status Legend

| Status | Meaning |
|--------|---------|
| ✅ Complete | Feature is fully implemented and functional |
| 🟡 Partial | Core functionality works, some features missing |
| 🔧 In Progress | Under active development |
| 📝 Planned | Designed but not yet implemented |

---

## 1. Data Explorer

**Status: ✅ Complete**

Browse and explore PostgreSQL databases with a modern UI and MCP integration for AI assistants.

### Completed
- Database connection management (multiple databases)
- Schema and table browsing
- Column metadata viewing (types, nullability, defaults)
- Paginated data preview with row/column counts
- Table summary statistics (min/max/avg for numerics)
- Read-only SQL query execution with safety validation
- Query execution timing and error handling
- MCP HTTP bridge for LLM tool calling (xAI, Gemini, ChatGPT)
- Table profiling (null counts, distinct values, distributions)

### API Endpoints
- `GET /api/v1/data-explorer/databases` - List databases
- `GET /api/v1/data-explorer/schemas` - List schemas
- `GET /api/v1/data-explorer/tables` - List tables
- `GET /api/v1/data-explorer/tables/{schema}/{table}/columns` - Column metadata
- `GET /api/v1/data-explorer/tables/{schema}/{table}/rows` - Paginated data
- `POST /api/v1/data-explorer/query` - Execute SQL
- `POST /api/v1/data-explorer/tool/*` - MCP tool endpoints

---

## 2. Data Dictionary

**Status: ✅ Complete**

Business-focused data documentation system with approval workflows.

### Completed
- Table and column documentation
- Business descriptions and glossary terms
- Semantic types and sensitivity classification
- Approval workflow (draft → approved → deprecated)
- Enhanced relationship discovery
- Dictionary semantics (business terms, concepts)
- MCP integration for AI-assisted documentation

### API Endpoints
- `/api/v1/data-explorer/dictionary/*` - Core dictionary operations
- `/api/v1/data-explorer/dictionary-enhanced/*` - Enhanced features
- `/api/v1/data-explorer/dictionary-semantics/*` - Semantic operations

---

## 3. Chat Interface

**Status: ✅ Complete**

Multi-provider LLM chat with streaming responses and tool calling.

### Completed
- Multi-provider support (OpenAI, Anthropic, Google, xAI)
- Server-Sent Events streaming responses
- Conversation persistence in PostgreSQL
- Message history with full context
- Tool calling integration with Data Explorer
- Connection-scoped data conversations

### API Endpoints
- `POST /api/v1/chat/conversations` - Create conversation
- `GET /api/v1/chat/conversations` - List conversations
- `GET /api/v1/chat/conversations/{id}` - Get with messages
- `POST /api/v1/chat/conversations/{id}/messages` - Send message (streaming)

---

## 4. ML Development

**Status: 🟡 Partial**

ML recipe management, model registry, and run tracking system.

### Completed
- Recipe CRUD (create, read, update, delete)
- Recipe versioning with manifests
- Model families (Pricing, Forecasting, NBA, Location Scoring)
- Model registry with status tracking
- Run management (create, track, update)
- Run metrics and artifacts storage
- Monitoring snapshots (performance, drift, freshness)
- Synthetic example generation for recipes
- ML Chat assistant (LLM-powered recipe advisor)
- Derived assets with TTL and promotion
- Cost tracking and estimates
- Run reuse engine (similarity detection)
- Asset versioning with rollback
- Run comparison across metrics

### Partial/In Progress
- RunPod integration (scaffolded, needs testing)
- M5 forecasting pipeline (specific to M5 dataset)
- GPU pricing from live API

### API Endpoints
- `/api/v1/ml-development/recipes/*` - Recipe management
- `/api/v1/ml-development/models/*` - Model registry
- `/api/v1/ml-development/runs/*` - Run tracking
- `/api/v1/ml-development/assets/*` - Derived assets
- `/api/v1/ml-development/runpod/*` - GPU compute

---

## 5. Distillation Workbench

**Status: ✅ Complete**

Multi-model prompt execution, response curation, and dataset building for LLM fine-tuning.

### Completed
- Domain and topic organization
- Tag management for responses
- Task library with templates
- Interactive chat (streaming, concurrent multi-model)
- Response bank with quality ratings
- Banking and curation workflow
- Model comparisons and voting
- Blind A/B comparisons
- Structured data extraction with schemas
- Expert review queues with workflows
- Batch generation (prompt loop)
- Dataset building (JSONL, CSV, Alpaca exports)
- Full lineage and audit trail
- Model contribution statistics

### API Endpoints
- `/api/v1/distillation/domains/*` - Domain management
- `/api/v1/distillation/topics/*` - Topic management
- `/api/v1/distillation/tasks/*` - Task library
- `/api/v1/distillation/chat` - Interactive chat
- `/api/v1/distillation/responses/*` - Response bank
- `/api/v1/distillation/banked/*` - Banked responses
- `/api/v1/distillation/comparisons/*` - Model comparisons
- `/api/v1/distillation/datasets/*` - Dataset building
- `/api/v1/distillation/review-queues/*` - Expert review
- `/api/v1/distillation/batch-jobs/*` - Batch generation

---

## 6. Files & Google Drive

**Status: ✅ Complete**

File location management with local and Google Drive support.

### Completed
- File location CRUD (local directories, Google Drive folders)
- Directory scanning for CSV/Excel files
- File asset tracking with versioning (content hash detection)
- Table extraction from files (multi-sheet Excel support)
- Schema inference and column metadata
- Data preview with pagination
- Publish to datasets with lineage tracking
- Google Drive OAuth flow
- External account management
- Encryption for sensitive files

### API Endpoints
- `/api/files/locations/*` - Location management
- `/api/files/locations/{id}/scan` - Scan for files
- `/api/files/assets/*` - File asset management
- `/api/files/tables/preview` - Table preview
- `/api/files/tables/{id}/publish` - Publish to datasets
- `/api/files/gdrive/*` - Google Drive OAuth

---

## 7. Notebooks

**Status: ✅ Complete**

SQL and Python notebooks with cell execution and dataset export.

### Completed
- Notebook CRUD with folders and tags
- SQL cells with connection binding
- Python cells with shared session state
- Cell execution (SQL and Python)
- Session variable management
- Session reset functionality
- Query result caching
- Save results as datasets (Parquet/CSV)
- Dataset export to MinIO object storage
- Dataset preview and download URLs
- Cell positioning and reordering

### API Endpoints
- `/api/v1/notebooks/*` - Notebook CRUD
- `/api/v1/notebooks/{id}/cells/*` - Cell management
- `/api/v1/notebooks/{id}/cells/{id}/execute` - SQL execution
- `/api/v1/notebooks/{id}/cells/{id}/execute-python` - Python execution
- `/api/v1/notebooks/{id}/cells/{id}/save-dataset` - Export to dataset
- `/api/v1/notebooks/datasets/*` - Dataset management

---

## 8. Data Lineage

**Status: ✅ Complete**

Comprehensive data lineage tracking with SQL parsing and visualization.

### Completed
- Entity-based lineage (file, table, dataset, model)
- Edge types (derived, filtered, joined, aggregated, published)
- Upstream and downstream traversal
- SQL query parsing for automatic lineage
- Column-level lineage extraction
- ML query detection and feature tracking
- Cross-query pipeline discovery
- Impact analysis (what would be affected)
- Lineage summary statistics
- Auto-tracking from Data Explorer queries

### API Endpoints
- `/api/v1/lineage/{entity_type}/{entity_id}` - Get lineage graph
- `/api/v1/lineage/{entity_type}/{entity_id}/summary` - Quick summary
- `/api/v1/lineage/{entity_type}/{entity_id}/upstream` - Sources only
- `/api/v1/lineage/{entity_type}/{entity_id}/downstream` - Derived only
- `/api/v1/lineage/{entity_type}/{entity_id}/impact` - Impact analysis
- `/api/v1/lineage/track` - Track new relationship
- `/api/v1/lineage/parse-sql` - Preview SQL lineage
- `/api/v1/lineage/track-query` - Track from executed query
- `/api/v1/lineage/parse-sql/column-level` - Column-level lineage
- `/api/v1/lineage/analyze-ml-query` - Detect ML queries
- `/api/v1/lineage/pipelines` - Discover data pipelines

---

## 9. Data Connections

**Status: ✅ Complete**

Manage external database connections for notebooks and exploration.

### Completed
- Connection CRUD with credentials
- PostgreSQL connection support
- Connection testing/validation
- Scanner for M5 datasets
- Integration with notebooks and data explorer

### API Endpoints
- `/api/v1/data-connections/*` - Connection management

---

## 10. Highlighted Datasets

**Status: ✅ Complete**

Featured dataset management for quick access.

### Completed
- Dataset highlighting with descriptions
- Category organization
- Usage tracking
- Integration with model development

---

## 11. Insights & Quality

**Status: 🟡 Partial**

AI-powered insights and data quality assessment.

### Completed
- Basic insight generation (requires LLM API keys)
- Data quality scoring (0-100)
- Completeness, consistency checks
- Issue identification

### Needs Work
- Automated quality monitoring
- Quality trend tracking over time
- More sophisticated anomaly detection

---

## 12. Synthetic Data

**Status: 🟡 Partial**

Privacy-safe synthetic data generation.

### Completed
- Basic synthetic data generation
- Statistical property preservation

### Needs Work
- Advanced correlation preservation
- Conditional generation
- Quality validation

---

## Frontend Pages

| Page | Route | Status |
|------|-------|--------|
| Dashboard | `/` | ✅ Complete |
| Data Upload | `/upload` | ✅ Complete |
| Data Explorer | `/explorer` | ✅ Complete |
| Data Dictionary | `/dictionary` | ✅ Complete |
| Chat | `/chat` | ✅ Complete |
| Model Library | `/model-development` | ✅ Complete |
| ML Workbench | `/ml-workbench` | ✅ Complete |
| Recipe Detail | `/model-development/recipes/:id` | ✅ Complete |
| Model Detail | `/model-development/models/:id` | ✅ Complete |
| Run Detail | `/model-development/runs/:id` | ✅ Complete |
| Run Comparison | `/model-development/runs/compare` | ✅ Complete |
| Derived Assets | `/model-development/assets` | ✅ Complete |
| ML Chat | `/model-development/chat` | ✅ Complete |
| RunPod Jobs | `/model-development/runpod-jobs` | 🟡 Partial |
| Forecast Dashboard | `/forecast` | 🟡 Partial |
| Distillation | `/distillation` | ✅ Complete |
| File Locations | `/files/locations` | ✅ Complete |
| File Inventory | `/files/inventory` | ✅ Complete |
| File Asset Detail | `/files/assets/:id` | ✅ Complete |
| Data Sources | `/data-sources` | ✅ Complete |
| Notebooks | `/notebooks` | ✅ Complete |
| Notebook Editor | `/notebooks/:id` | ✅ Complete |
| Datasets | `/datasets` | ✅ Complete |
| Lineage Demo | `/lineage-demo` | ✅ Complete |
| Insights | `/insights` | 🟡 Partial |
| Quality | `/quality` | 🟡 Partial |
| Knowledge Gaps | `/gaps` | 🟡 Partial |
| Synthetic Data | `/synthetic` | 🟡 Partial |

---

## Infrastructure

| Component | Status |
|-----------|--------|
| PostgreSQL + pgvector | ✅ Running |
| MinIO Object Storage | ✅ Running |
| Redis (for jobs) | ✅ Running |
| Docker Compose | ✅ Complete |
| Database Migrations | ✅ Complete |
| Environment Config | ✅ Complete |

---

## What's Not Implemented

1. **User Authentication** - No auth system yet (single user assumed)
2. **Role-Based Access Control** - No permissions system
3. **Scheduled Jobs** - Scheduler domain is scaffolded but not active
4. **Drift Detection** - Drift domain exists but minimal implementation
5. **Evaluation Packs** - Schema exists but limited functionality
6. **Real GPU Training** - RunPod integration needs end-to-end testing

---

## Getting Started

```bash
# Start all services
docker compose -p nex up -d

# Access the platform
# Frontend: http://localhost:3000
# API Docs: http://localhost:8000/docs
# MinIO:    http://localhost:9001 (minioadmin/minioadmin)
```

## Environment Variables Required

```env
# Required for AI features
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Optional providers
XAI_API_KEY=...
GOOGLE_API_KEY=...

# For Google Drive
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...

# For RunPod GPU
RUNPOD_API_KEY=...
```

---

## Summary

- **14 major domains** implemented
- **~80% feature complete** for core data platform capabilities
- **Strong areas:** Data exploration, dictionary, chat, ML dev, distillation, notebooks, lineage
- **Needs work:** Authentication, scheduled jobs, drift detection, advanced ML ops
