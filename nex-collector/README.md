# NEX Context Aggregator

A Python service for **context aggregation** and **dataset building** that helps you create consistent, high-quality training data from off-the-shelf LLMs.

## What This Tool Does

The NEX Context Aggregator is designed to:

1. **Aggregate Contexts** - Continuously generate and refresh context documents from OTS (off-the-shelf) LLMs like GPT-4
2. **Extract Features** - Automatically identify domain, persona, task, and style facets
3. **Build Datasets** - Turn contexts into synthetic examples and fine-tune packs for smaller models
4. **Mix & Match** - Compose new contexts by combining facets from existing variants
5. **Query by Domain** - Filter and query contexts by domain, persona, or task

## Quick Start

**Windows**: Run `.\nex-collector\start.bat` or see [GETTING_STARTED.md](GETTING_STARTED.md)

**Linux/Mac**: Run `bash nex-collector/start.sh` or see [GETTING_STARTED.md](GETTING_STARTED.md)

### Prerequisites

1. **Main NEX database running**: The service connects to the main NEX `nex_db` container
2. **Docker Desktop**: Required for running services
3. **OPENAI_API_KEY**: Set in root `.env` file (see [SETUP.md](SETUP.md))

### Quick Start

```bash
# 1. Start main NEX database
docker-compose up -d db

# 2. Start nex-collector
.\nex-collector\start.bat  # Windows
# or
bash nex-collector/start.sh  # Linux/Mac

# 3. Verify it's running
curl http://localhost:8080/healthz
```

See [GETTING_STARTED.md](GETTING_STARTED.md) for detailed instructions.

## Features

- **Context Aggregation**: Continuously sample OTS LLMs to generate/refresh contexts
- **Feature Extraction**: Extract domain/persona/task/style facets for mix-and-match
- **Dataset Building**: Turn contexts → examples → fine-tune packs
- **Document Store**: Contexts as bodies of text with variants + embeddings
- **Scalable Domains**: Support any domain (insurance, finance, healthcare, etc.) without schema changes

## Project Structure

```
nex-collector/
├── app/
│   ├── routes/          # API routes
│   ├── ingest/          # Aggregation pipeline
│   ├── distill/         # Distillation pipeline
│   └── providers/       # LLM providers
├── scripts/              # Seed scripts
│   ├── seed_insurance_underwriter.py  # Insurance context seed
│   ├── seed_insurance_dataset.py      # Insurance dataset seed
│   └── seed_demo.py                   # General demo seed
└── migrations/          # Alembic migrations
```

## Documentation

- **[GETTING_STARTED.md](GETTING_STARTED.md)** - Quick start guide (how to run)
- **[SETUP.md](SETUP.md)** - Environment setup and configuration
- **[DATA_STRUCTURE.md](DATA_STRUCTURE.md)** - Complete data structure guide with examples
- **[DATA_STORAGE.md](DATA_STORAGE.md)** - Where data is stored
- **[USAGE_GUIDE.md](USAGE_GUIDE.md)** - API usage examples and workflows

## API Documentation

Once running, visit: **http://localhost:8080/docs**

## License

MIT

## Usage Examples

### 1. Create Context and Variant

```bash
curl -X POST http://localhost:8080/v1/contexts \
  -H "Authorization: Bearer dev-secret" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "ctx-1",
    "title": "Finance Context",
    "version": "1.0.0",
    "body_text": "Financial analysis guidelines...",
    "metadata_json": {}
  }'

curl -X POST http://localhost:8080/v1/contexts/ctx-1/variants \
  -H "Authorization: Bearer dev-secret" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "var-1",
    "context_id": "ctx-1",
    "domain": "finance",
    "persona": "CFO",
    "task": "analyze",
    "style": "formal",
    "body_text": "Financial analysis guidelines...",
    "constraints_json": {}
  }'
```

### 2. Compose Variant (Mix & Match)

```bash
curl -X POST http://localhost:8080/v1/contexts/variants/compose \
  -H "Authorization: Bearer dev-secret" \
  -H "Content-Type: application/json" \
  -d '{
    "source_variant_ids": ["var-1", "var-2"],
    "domain": "finance",
    "persona": "CFO",
    "task": "explain",
    "composition_strategy": "merge"
  }'
```

### 3. Query Variants by Domain/Persona/Task

```bash
# Query all insurance variants
curl "http://localhost:8080/v1/contexts/variants?domain=insurance" \
  -H "Authorization: Bearer dev-secret"

# Query specific persona
curl "http://localhost:8080/v1/contexts/variants?domain=insurance&persona=underwriter" \
  -H "Authorization: Bearer dev-secret"
```

### 4. Generate Examples

```bash
curl -X POST http://localhost:8080/v1/datasets/distill/examples \
  -H "Authorization: Bearer dev-secret" \
  -H "Content-Type: application/json" \
  -d '{
    "variant_ids": ["var-1"],
    "example_type": "instruction",
    "quota_per_variant": 10
  }'
```

### 5. Build Fine-Tune Pack

```bash
curl -X POST http://localhost:8080/v1/datasets/distill/build \
  -H "Authorization: Bearer dev-secret" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "finance-pack",
    "version": "1.0.0",
    "kind": "finetune_pack",
    "variant_ids": ["var-1"],
    "filters": {"has_teacher_output": true}
  }'
```

## Custom Rubric Configuration

> **Note**: Underwriting functionality has been removed. This section is kept for reference only.

The service previously supported custom rubric configurations for underwriting. This feature has been removed in favor of a simpler architecture focused on context aggregation and dataset building.

## API Endpoints

See Swagger UI at `/docs` for full API documentation.

### Contexts
- `POST /v1/contexts` - Create ContextDoc
- `GET /v1/contexts/{id}` - Get ContextDoc
- `POST /v1/contexts/{id}/variants` - Create ContextVariant
- `GET /v1/contexts/variants` - List variants (filter by domain/persona/task)
- `GET /v1/contexts/variants/{id}` - Get ContextVariant
- `POST /v1/contexts/variants/compose` - Compose variant (mix & match)

### Aggregation
- `POST /v1/aggregate/sample` - Enqueue generation job

### Datasets
- `POST /v1/datasets/distill/examples` - Generate examples
- `POST /v1/datasets/distill/build` - Build dataset/fine-tune pack
- `GET /v1/datasets` - List datasets
- `GET /v1/datasets/{id}` - Get dataset manifest

### Teachers
- `POST /v1/teachers/runs` - Collect teacher outputs
- `GET /v1/teachers/runs/{id}` - Get teacher run

## Configuration

- `AGGREGATOR_INTERVAL_SECS`: Interval for continuous aggregation (default: 3600)
- `REQUIRE_APPROVAL`: Only approved variants for datasets (default: false, underwriting removed)
- `EMBEDDINGS_ENABLED`: Enable embeddings (default: false)
- `DATA_DIR`: Directory for datasets (default: ./data)
- `OPENAI_API_KEY`: OpenAI API key (required)
- `NEX_WRITE_TOKEN`: Bearer token for API auth (default: dev-secret)
- `MODE_INTEGRATION`: Integration mode - `separate` (default) or `integrated`

## Project Structure

```
nex-collector/
├── app/
│   ├── routes/          # API routes
│   ├── ingest/          # Aggregation pipeline
│   ├── distill/         # Distillation pipeline
│   └── providers/       # LLM providers
├── scripts/              # Seed scripts
│   ├── seed_insurance_underwriter.py  # Insurance context seed
│   ├── seed_insurance_dataset.py      # Insurance dataset seed
│   └── seed_demo.py                   # General demo seed
└── migrations/          # Alembic migrations
```

## Development

### Database Migrations

```bash
# Create migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## License

MIT
