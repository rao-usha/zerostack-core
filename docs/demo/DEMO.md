# ZeroStack Demo Guide

> Quick reference for demonstrating ZeroStack's AI-native data platform capabilities.

**Frontend:** `http://localhost:5173`
**Backend API:** `http://localhost:8000`
**API Docs:** `http://localhost:8000/docs`

---

## 1. The "Wow" Demo: Chat With Your Data (30 seconds)

**What it does:** Ask questions about your database in plain English - get SQL, insights, and visualizations.

### Via UI
1. Open `http://localhost:5173/chat`
2. Type: *"What tables do I have and how are they related?"*
3. Follow up: *"Show me the top 10 customers by revenue"*

### Via API
```bash
curl -X POST http://localhost:8000/api/v1/chat/message \
  -H "Content-Type: application/json" \
  -d '{"message": "What are my largest tables by row count?"}'
```

**Key talking points:**
- Natural language to SQL translation
- Understands your schema context
- Streaming responses via SSE
- Multi-turn conversation memory

---

## 2. AI-Powered Data Dictionary (The Killer Feature)

**What it does:** Automatically document your entire database with business definitions, tags, and relationships.

### Generate Documentation
1. Navigate to **Data Analysis** (`/analysis`)
2. Select your database connection
3. Choose tables to document
4. Select **"Column Documentation"** as analysis type
5. Pick LLM provider (OpenAI, Anthropic, Google, xAI)
6. Click **Create Job**

### View Results
1. Go to **Data Dictionary** (`/dictionary`)
2. Browse AI-generated documentation:
   - Business names and descriptions
   - Technical definitions
   - Data type analysis
   - PII detection and tagging
   - Example values

**What you get:**
```json
{
  "column_name": "cust_id",
  "business_name": "Customer ID",
  "business_description": "Unique identifier for each customer account",
  "technical_description": "Primary key, auto-incrementing integer",
  "tags": ["identifier", "primary_key"],
  "examples": ["1001", "1002", "1003"],
  "trust_tier": "certified"
}
```

**Key features:**
- Version history for all changes
- Human edits protected from AI overwrites
- Approval workflow (Draft → Approved → Published)
- Relationship intelligence (FK detection)

---

## 3. Database Explorer (Zero-Setup Data Browsing)

**What it does:** Browse any PostgreSQL database with schema introspection, data profiling, and safe query execution.

### Via UI
1. Open `http://localhost:5173/explorer`
2. Select database connection
3. Browse schemas → tables → columns
4. Click **Profile** to see statistics
5. Click **Sample** to preview data
6. Write and execute read-only queries

### Via API
```bash
# List schemas
curl http://localhost:8000/api/v1/data-explorer/schemas

# List tables in a schema
curl http://localhost:8000/api/v1/data-explorer/schemas/public/tables

# Get column info
curl http://localhost:8000/api/v1/data-explorer/schemas/public/tables/customers/columns

# Profile a table
curl http://localhost:8000/api/v1/data-explorer/schemas/public/tables/customers/profile

# Sample data
curl "http://localhost:8000/api/v1/data-explorer/schemas/public/tables/customers/sample?limit=10"

# Execute query (SELECT only)
curl -X POST http://localhost:8000/api/v1/data-explorer/query \
  -H "Content-Type: application/json" \
  -d '{"sql": "SELECT * FROM customers LIMIT 5"}'
```

**Safety features:**
- Read-only query validation
- Query timeout limits
- Row count limits
- No DDL/DML allowed

---

## 4. ML Development Workbench

**What it does:** End-to-end machine learning workflow - from data to trained model with explainability.

### Quick ML Demo
1. Navigate to **ML Workbench** (`/ml-workbench`)
2. Select a dataset (or upload CSV)
3. Choose target column
4. Select model type (Regression/Classification)
5. Click **Train Model**

### What You Get
- Model performance metrics (R², accuracy, F1)
- Feature importance (SHAP values)
- Confusion matrix / residual plots
- Model versioning and comparison

### Via API
```bash
# Train a model
curl -X POST http://localhost:8000/api/v1/ml/train \
  -H "Content-Type: application/json" \
  -d '{
    "dataset_id": "customers",
    "target_column": "churn",
    "model_type": "classification",
    "features": ["tenure", "monthly_charges", "total_charges"]
  }'

# Get predictions
curl -X POST http://localhost:8000/api/v1/ml/predict \
  -H "Content-Type: application/json" \
  -d '{
    "model_id": "model_123",
    "data": {"tenure": 12, "monthly_charges": 50.0}
  }'
```

---

## 5. Distillation Workbench

**What it does:** Create and curate high-quality training data for fine-tuning LLMs.

### Via UI
1. Open **Distillation Workbench** (`/distillation`)
2. Create a new distillation run
3. Define prompt templates
4. Generate examples using teacher model
5. Review and curate outputs
6. Export as JSONL for fine-tuning

**Use cases:**
- Generate domain-specific Q&A pairs
- Create SQL examples from natural language
- Build evaluation datasets

---

## 6. Data Lineage Tracking

**What it does:** Visualize how data flows through your systems with automatic SQL parsing.

### Via UI
1. Open **Lineage Demo** (`/lineage-demo`)
2. Paste a SQL query or select a table
3. See upstream and downstream dependencies
4. Click nodes to explore relationships

### Via API
```bash
# Get lineage for a table
curl http://localhost:8000/api/v1/lineage/table/public.customers

# Parse SQL for lineage
curl -X POST http://localhost:8000/api/v1/lineage/parse \
  -H "Content-Type: application/json" \
  -d '{"sql": "SELECT * FROM orders o JOIN customers c ON o.customer_id = c.id"}'
```

---

## 7. Synthetic Data Generation

**What it does:** Generate privacy-safe synthetic data that maintains statistical properties.

### Via API
```bash
# Generate synthetic data
curl -X POST http://localhost:8000/api/v1/synthetic/generate \
  -H "Content-Type: application/json" \
  -d '{
    "source_table": "customers",
    "num_rows": 1000,
    "preserve_correlations": true
  }'
```

**Key features:**
- Maintains column distributions
- Preserves relationships between columns
- No PII leakage
- Configurable row counts

---

## 8. Data Quality Scoring

**What it does:** Automatically assess data quality with actionable scores.

### Via API
```bash
curl http://localhost:8000/api/v1/quality/assess/public.customers
```

**What you get:**
```json
{
  "overall_score": 87,
  "dimensions": {
    "completeness": 95,
    "uniqueness": 100,
    "validity": 82,
    "consistency": 78
  },
  "issues": [
    {"column": "email", "issue": "12% null values"},
    {"column": "phone", "issue": "Invalid format in 8% of rows"}
  ],
  "recommendations": [...]
}
```

---

## 9. MCP Integration (Claude Desktop)

**What it does:** Use ZeroStack as a tool server for Claude Desktop - explore databases conversationally.

### Setup
Add to your Claude Desktop config:
```json
{
  "mcpServers": {
    "zerostack-explorer": {
      "command": "python",
      "args": ["C:/path/to/nex/backend/mcp_server.py"]
    },
    "zerostack-dictionary": {
      "command": "python",
      "args": ["C:/path/to/nex/backend/mcp_dictionary_server.py"]
    }
  }
}
```

### Available Tools
**Data Explorer:**
- `list_connections` - Show available databases
- `list_schemas` - Browse database schemas
- `list_tables` - See tables in a schema
- `get_table_info` - Column metadata
- `sample_rows` - Preview data
- `profile_table` - Statistical analysis
- `run_query` - Execute SELECT queries

**Data Dictionary:**
- `discover_assets` - Find documented tables
- `get_asset_documentation` - Get business definitions
- `explain_table` - Comprehensive table explanation
- `explain_join` - How to join two tables
- `check_data_quality` - Trust tier and quality scores

---

## Quick Demo Script (5 minutes)

### 1. Open the Dashboard (30 sec)
Open `http://localhost:5173` - *"Here's our AI-native data platform"*

### 2. Explore a Database (1 min)
1. Click **Data Explorer**
2. Select a connection
3. Browse to a table
4. Click **Profile** - *"Automatic statistical profiling"*
5. Click **Sample** - *"Preview data safely"*

### 3. Chat With Data (1 min)
1. Click **Chat**
2. Ask: *"What are my top 5 tables by row count?"*
3. Ask: *"Show me the relationship between orders and customers"*
4. *"Natural language to insights in seconds"*

### 4. Generate Documentation (1.5 min)
1. Click **Data Analysis**
2. Select tables → Column Documentation
3. Run with Claude/GPT
4. Go to **Data Dictionary**
5. *"AI-generated, human-editable documentation"*

### 5. Show ML Capabilities (1 min)
1. Click **ML Workbench**
2. Show a trained model
3. Display feature importance
4. *"End-to-end ML with explainability"*

---

## Key Differentiators

1. **Multi-LLM Support** - OpenAI, Anthropic, Google, xAI - switch providers anytime
2. **Chat-First Interface** - Natural language access to all data
3. **AI + Human Loop** - AI generates, humans curate and approve
4. **Enterprise Features** - Versioning, approval workflows, audit trails
5. **MCP Integration** - Works with Claude Desktop as a tool server
6. **Privacy-First** - Synthetic data, PII detection, read-only queries

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | React 18 + TypeScript + Vite + Tailwind |
| Backend | FastAPI (Python) - async, high-performance |
| Database | PostgreSQL + pgvector |
| ML | Scikit-learn, SHAP |
| LLM | OpenAI, Anthropic, Google, xAI SDKs |
| Visualization | Recharts, Plotly.js, XYFlow |

---

## Startup Commands

```powershell
# Backend
cd backend
pip install -r requirements-core.txt
uvicorn main:app --reload --port 8000

# Frontend
cd frontend
npm install
npm run dev

# Or with Docker
$env:DOCKER_BUILDKIT=1
docker-compose up --build
```

---

## If Something Breaks

```powershell
# Check backend health
curl http://localhost:8000/health

# Check logs
docker-compose logs backend --tail 50

# Restart
docker-compose down && docker-compose up --build -d
```
