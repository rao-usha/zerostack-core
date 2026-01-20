# ZeroStack Quick Commands

> Copy-paste commands for live demos. All assume service running at `localhost:8000`.

---

## Health & Status

```bash
# Health check
curl http://localhost:8000/health

# API docs
open http://localhost:8000/docs
```

---

## Data Explorer

```bash
# List database connections
curl http://localhost:8000/api/v1/data-explorer/connections

# List schemas
curl http://localhost:8000/api/v1/data-explorer/schemas

# List tables in public schema
curl http://localhost:8000/api/v1/data-explorer/schemas/public/tables

# Get columns for a table
curl http://localhost:8000/api/v1/data-explorer/schemas/public/tables/customers/columns

# Profile a table (statistics)
curl http://localhost:8000/api/v1/data-explorer/schemas/public/tables/customers/profile

# Sample rows
curl "http://localhost:8000/api/v1/data-explorer/schemas/public/tables/customers/sample?limit=5"

# Execute read-only query
curl -X POST http://localhost:8000/api/v1/data-explorer/query \
  -H "Content-Type: application/json" \
  -d '{"sql": "SELECT COUNT(*) FROM customers"}'
```

---

## Chat

```bash
# Send a message
curl -X POST http://localhost:8000/api/v1/chat/message \
  -H "Content-Type: application/json" \
  -d '{"message": "What tables do I have?"}'

# Start a conversation
curl -X POST http://localhost:8000/api/v1/chat/conversations \
  -H "Content-Type: application/json" \
  -d '{"title": "Demo Session"}'

# Continue conversation
curl -X POST http://localhost:8000/api/v1/chat/conversations/{id}/messages \
  -H "Content-Type: application/json" \
  -d '{"message": "Show me the schema"}'
```

---

## Data Dictionary

```bash
# List all documented assets
curl http://localhost:8000/api/v1/data-dictionary/enhanced/assets

# Get asset documentation
curl http://localhost:8000/api/v1/data-dictionary/enhanced/assets/{id}

# Get fields for an asset
curl http://localhost:8000/api/v1/data-dictionary/enhanced/assets/{id}/fields

# Get relationships
curl http://localhost:8000/api/v1/data-dictionary/enhanced/relationships

# Get full context for a table
curl http://localhost:8000/api/v1/data-dictionary/enhanced/context/default/public/customers
```

---

## Data Analysis Jobs

```bash
# Create documentation job
curl -X POST http://localhost:8000/api/v1/data-analysis/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "tables": ["public.customers", "public.orders"],
    "analysis_type": "column_documentation",
    "llm_provider": "anthropic",
    "llm_model": "claude-3-5-sonnet-20241022"
  }'

# Check job status
curl http://localhost:8000/api/v1/jobs/{job_id}

# List all jobs
curl http://localhost:8000/api/v1/jobs
```

---

## ML Development

```bash
# List models
curl http://localhost:8000/api/v1/ml/models

# Get model details
curl http://localhost:8000/api/v1/ml/models/{model_id}

# Get model metrics
curl http://localhost:8000/api/v1/ml/models/{model_id}/metrics
```

---

## Data Quality

```bash
# Assess table quality
curl http://localhost:8000/api/v1/quality/assess/public.customers

# Get quality history
curl http://localhost:8000/api/v1/quality/history/public.customers
```

---

## Synthetic Data

```bash
# Generate synthetic data
curl -X POST http://localhost:8000/api/v1/synthetic/generate \
  -H "Content-Type: application/json" \
  -d '{
    "source_table": "public.customers",
    "num_rows": 100
  }'
```

---

## Lineage

```bash
# Get table lineage
curl http://localhost:8000/api/v1/lineage/table/public.orders

# Parse SQL for lineage
curl -X POST http://localhost:8000/api/v1/lineage/parse \
  -H "Content-Type: application/json" \
  -d '{"sql": "SELECT * FROM orders JOIN customers ON orders.customer_id = customers.id"}'
```

---

## Insights

```bash
# Generate insights for a table
curl -X POST http://localhost:8000/api/v1/insights/generate \
  -H "Content-Type: application/json" \
  -d '{"table": "public.sales", "llm_provider": "openai"}'
```

---

## Frontend URLs

| Page | URL |
|------|-----|
| Dashboard | http://localhost:3000/ |
| Data Explorer | http://localhost:3000/explorer |
| Chat | http://localhost:3000/chat |
| Data Dictionary | http://localhost:3000/dictionary |
| ML Workbench | http://localhost:3000/ml-workbench |
| Distillation | http://localhost:3000/distillation |
| Lineage Demo | http://localhost:3000/lineage-demo |
| Data Quality | http://localhost:3000/quality |
| Insights | http://localhost:3000/insights |
