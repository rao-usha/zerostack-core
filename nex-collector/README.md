# NEX Context Aggregator

## 🧪 AI-Native Data Distillation Pipeline

A sophisticated service for **context aggregation** and **dataset distillation** that transforms off-the-shelf LLMs into specialized, domain-expert models through teacher-student knowledge transfer.

## What This Tool Does

The NEX Context Aggregator implements a complete AI-native data distillation workflow:

### 1. **🧠 Context Aggregation**
- Continuously generate and refresh context documents from GPT-4 and other LLMs
- Automatic domain knowledge extraction and structuring
- Multi-faceted context creation (domain, persona, task, style)

### 2. **🔍 Feature Extraction**
- Automatic identification of domain, persona, task, and style facets
- Semantic chunking and vector embedding generation
- Facet-based context organization and retrieval

### 3. **🧪 Synthetic Example Generation**
- Privacy-safe training data creation from distilled contexts
- Teacher-student distillation using advanced LLMs
- Quality-controlled example generation with rationales

### 4. **📦 Fine-Tune Pack Building**
- Curated dataset assembly for model specialization
- Multi-variant composition and mixing
- Ready-to-use training datasets for smaller models

### 5. **🔄 Mix & Match Composition**
- Combine facets from existing variants to create new contexts
- Intelligent context merging and deduplication
- Domain adaptation through facet recombination

## 🚀 Quick Start with Docker

### One-Command Setup (Recommended)

```bash
# Start the complete NEX platform with distillation
docker-compose -f docker-compose.dev.yml up -d

# Seed demo distillation data
docker exec nex-collector-api-1 python scripts/seed_demo.py

# Access the Distillation Explorer
open http://localhost:3000  # Click "Distillation" tab
```

### Manual Setup

**Prerequisites:**
1. **Docker Desktop** (20.10+)
2. **OpenAI API Key** (for AI distillation features)
3. **Main NEX platform** running (see main README)

```bash
# 1. Start main NEX services
cd /path/to/nex
docker-compose -f docker-compose.dev.yml up -d db backend frontend

# 2. Start NEX-Collector
cd nex-collector
docker-compose --profile init up -d

# 3. Seed sample data
docker exec nex-collector-api-1 python scripts/seed_demo.py

# 4. Verify all services
curl http://localhost:8080/healthz  # NEX-Collector
curl http://localhost:8000/healthz  # Main Backend
curl -I http://localhost:3000       # Frontend
```

### 🖥️ **Access Points**
- **Distillation Explorer**: http://localhost:3000 (Distillation tab)
- **API Documentation**: http://localhost:8080/docs
- **Main Platform**: http://localhost:8000/docs

### 📊 **Sample Data Available**
After seeding, explore these pre-built distillation packs:
- **Retail Customer Service** (Macy's scenarios)
- **Insurance Underwriting** (Risk assessment)
- **Finance Analysis** (CFO persona)
- **General Retail** (Multi-domain contexts)

## ✨ Key Features

### 🧠 **Context Intelligence**
- **Continuous Aggregation**: Automatically generate and refresh context documents from GPT-4
- **Multi-Faceted Contexts**: Domain, persona, task, and style-aware context creation
- **Semantic Understanding**: Vector embeddings for context similarity and retrieval

### 🔬 **Distillation Pipeline**
- **Synthetic Example Generation**: Privacy-safe training data from distilled contexts
- **Teacher-Student Learning**: Knowledge transfer from large LLMs to specialized models
- **Quality Assurance**: Automated quality checks and rationale generation

### 🏗️ **Dataset Engineering**
- **Fine-Tune Pack Assembly**: Curated datasets ready for model training
- **Variant Composition**: Mix and match context facets for domain adaptation
- **Scalable Architecture**: Support any domain without schema changes

### 🔗 **Platform Integration**
- **Distillation Explorer UI**: Interactive exploration in the main NEX frontend
- **Unified API**: Seamless integration with main platform services
- **Shared Database**: Consistent data access across services

### 📊 **Pre-Built Data Packs**
Explore these ready-to-use distillation datasets:
- **🛍️ Retail Customer Service**: Macy's support scenarios with multiple personas
- **💼 Insurance Underwriting**: Risk assessment with different tolerance levels
- **🏦 Finance Analysis**: CFO persona for financial decision-making
- **🏪 General Retail**: Broad retail contexts for domain generalization

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
