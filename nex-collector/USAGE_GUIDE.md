# NEX Context Aggregator - Complete Usage Guide

A comprehensive guide to using the NEX Context Aggregator and understanding its outputs.

## Table of Contents

1. [What This Tool Does](#what-this-tool-does)
2. [Core Concepts](#core-concepts)
3. [Quick Start](#quick-start)
4. [How to Use](#how-to-use)
5. [Understanding the Output](#understanding-the-output)
6. [Example Workflows](#example-workflows)
7. [Customization](#customization)
8. [Troubleshooting](#troubleshooting)

## What This Tool Does

The NEX Context Aggregator is designed to:

1. **Aggregate Contexts** - Continuously generate and refresh context documents from OTS (off-the-shelf) LLMs like GPT-4
2. **Underwrite Contexts** - Score and evaluate contexts for risk, utility, and fitness for use
3. **Extract Features** - Automatically identify domain, persona, task, and style facets
4. **Build Datasets** - Turn contexts into synthetic examples and fine-tune packs for smaller models
5. **Mix & Match** - Compose new contexts by combining facets from existing variants

## Core Concepts

### Context = Document
A **ContextDoc** is a body of text (instructions, policies, exemplars) that serves as knowledge for your models. Think of it as a "prompt pack" or "instruction manual."

### Variants = Faceted Views
A **ContextVariant** is a version of a context with specific facets:
- **Domain**: finance, healthcare, legal, technology
- **Persona**: CFO, doctor, lawyer, engineer
- **Task**: analyze, explain, classify, generate
- **Style**: formal, conversational, neutral

Variants enable **mix-and-match** - you can combine facets from different variants to create new contexts.

### Underwriting = Quality Assurance
**Underwriting** evaluates each context variant like an insurance policy:
- **Risk Score** (0-100): Safety, PII detection, prompt injection risk
- **Utility Score** (0-100): Clarity, structure, constraint compliance
- **Decision**: APPROVE, HOLD, or REJECT

Only **approved** variants flow into dataset building by default.

### Distillation = Dataset Creation
**Distillation** turns contexts into training data:
1. **Sample** examples from variants
2. **Collect** teacher outputs from OTS LLMs
3. **Filter** by quality gates
4. **Build** fine-tune packs (JSONL format)

## Quick Start

### Prerequisites

- Docker and Docker Compose
- OpenAI API key (for context generation and teacher outputs)
- PostgreSQL 16+ (via Docker)
- Redis 7+ (via Docker)

### Setup

```bash
cd nex-collector

# Copy environment file
cp .env.example .env

# Edit .env and set:
# OPENAI_API_KEY=sk-your-key-here
# NEX_WRITE_TOKEN=your-secret-token
```

### Start Services

```bash
# Start database and Redis
docker-compose up -d db redis

# Wait ~10 seconds for services to be ready
```

### Initialize Database

```bash
# Create initial migration
docker-compose run --rm api alembic revision --autogenerate -m "initial_schema"

# Apply migrations
docker-compose run --rm api alembic upgrade head
```

### Run Seed Script (Demo)

```bash
# Set your OpenAI API key
export OPENAI_API_KEY=sk-...

# Run the seed script
docker-compose run --rm -e OPENAI_API_KEY=$OPENAI_API_KEY api python scripts/seed_demo.py
```

This will create:
- 1 ContextDoc (finance domain)
- 1 ContextVariant with facets
- Underwriting scores
- 5 SyntheticExamples
- 3 TeacherRuns
- 1 Fine-tune pack

### Start API and Worker

```bash
# Start API server
docker-compose up -d api

# Start background worker (processes teacher runs)
docker-compose up -d worker

# View API docs
# Open http://localhost:8080/docs
```

## How to Use

### Workflow Overview

```
1. Create ContextDoc
   ↓
2. Create ContextVariant (with facets)
   ↓
3. Run Underwriting (get scores & decision)
   ↓
4. Generate SyntheticExamples
   ↓
5. Collect Teacher Outputs (label examples)
   ↓
6. Build Fine-Tune Pack
```

### Step-by-Step Usage

#### Step 1: Create a Context Document

```bash
curl -X POST http://localhost:8080/v1/contexts \
  -H "Authorization: Bearer dev-secret" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "ctx-finance-001",
    "title": "Financial Analysis Guidelines",
    "version": "1.0.0",
    "body_text": "When analyzing financial data, you must:\n1. Verify data sources\n2. Check for anomalies\n3. Calculate key metrics\n4. Provide clear recommendations.",
    "metadata_json": {"domain": "finance", "author": "CFO Team"}
  }'
```

**Output**: Creates a ContextDoc with your text content.

#### Step 2: Create a Variant (with Facets)

```bash
curl -X POST http://localhost:8080/v1/contexts/ctx-finance-001/variants \
  -H "Authorization: Bearer dev-secret" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "var-finance-cfo",
    "context_id": "ctx-finance-001",
    "domain": "finance",
    "persona": "CFO",
    "task": "analyze",
    "style": "formal",
    "body_text": "When analyzing financial data, you must:\n1. Verify data sources\n2. Check for anomalies\n3. Calculate key metrics\n4. Provide clear recommendations.",
    "constraints_json": {"max_length": 500, "require_citations": true}
  }'
```

**What Happens**:
- Creates ContextVariant with facets
- **Automatically extracts features** (domain, persona, task, style)
- **Automatically chunks** text for retrieval
- **Optionally embeds** chunks (if `EMBEDDINGS_ENABLED=true`)

**Output**: Variant with extracted features and chunks.

#### Step 3: Generate Context from OTS LLM (Optional)

Instead of manually creating contexts, you can generate them:

```bash
curl -X POST http://localhost:8080/v1/aggregate/sample \
  -H "Authorization: Bearer dev-secret" \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "openai",
    "model": "gpt-4o-mini",
    "prompt": "Generate a comprehensive context document for finance domain with analysis guidelines.",
    "domain": "finance",
    "persona": "CFO",
    "task": "analyze"
  }'
```

**Output**: Enqueues a job that generates a new ContextDoc and Variant.

#### Step 4: Run Underwriting

Evaluate the variant for quality and risk:

```bash
curl -X POST "http://localhost:8080/v1/underwrite/run?variant_id=var-finance-cfo&rubric_id=default" \
  -H "Authorization: Bearer dev-secret"
```

**Output**:
```json
{
  "id": "uw-abc123",
  "variant_id": "var-finance-cfo",
  "risk_score": 15,
  "utility_score": 75,
  "decision": "approve",
  "metrics_json": {
    "utility": {
      "length": 156,
      "length_ok": true,
      "has_sections": true,
      "instruction_clarity": 80
    },
    "safety": {
      "has_deny_patterns": false,
      "has_pii": false,
      "has_injection_risk": false
    },
    "hallucination_risk": {
      "has_citations": false,
      "contradiction_markers": 0
    }
  },
  "notes": "Context approved. Consider adding citations for factual claims."
}
```

**Decision Meanings**:
- **APPROVE**: Risk < 30 and Utility ≥ 50 → Ready for dataset building
- **HOLD**: Needs review or improvements
- **REJECT**: Risk ≥ 60 or Utility < 20 → Not suitable

#### Step 5: Compose Variants (Mix & Match)

Create new variants by combining facets:

```bash
curl -X POST http://localhost:8080/v1/contexts/variants/compose \
  -H "Authorization: Bearer dev-secret" \
  -H "Content-Type: application/json" \
  -d '{
    "source_variant_ids": ["var-finance-cfo", "var-healthcare-doctor"],
    "domain": "finance",
    "persona": "CFO",
    "task": "explain",
    "composition_strategy": "merge"
  }'
```

**Output**: New variant combining content from both sources with new task facet.

#### Step 6: Generate Synthetic Examples

Create examples from approved variants:

```bash
curl -X POST http://localhost:8080/v1/datasets/distill/examples \
  -H "Authorization: Bearer dev-secret" \
  -H "Content-Type: application/json" \
  -d '{
    "variant_ids": ["var-finance-cfo"],
    "example_type": "instruction",
    "quota_per_variant": 10
  }'
```

**Output**:
```json
{
  "example_ids": ["ex-001", "ex-002", ...],
  "count": 10
}
```

**Example Types**:
- `instruction`: Instruction-following examples
- `qa`: Question-answer pairs
- `task`: Task completion examples

#### Step 7: Collect Teacher Outputs

Label examples using OTS LLMs:

```bash
curl -X POST http://localhost:8080/v1/teachers/runs \
  -H "Authorization: Bearer dev-secret" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "tr-001",
    "example_id": "ex-001",
    "provider": "openai",
    "model": "gpt-4o-mini",
    "params_json": {
      "temperature": 0.7,
      "max_tokens": 200
    }
  }'
```

**What Happens**:
- Worker processes the job asynchronously
- Calls OpenAI API with the example input
- Stores output text, usage, and logprobs (if available)

**Output**: TeacherRun with `output_json` containing the LLM response.

#### Step 8: Build Fine-Tune Pack

Create a dataset ready for fine-tuning:

```bash
curl -X POST http://localhost:8080/v1/datasets/distill/build \
  -H "Authorization: Bearer dev-secret" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "finance-analysis-pack",
    "version": "1.0.0",
    "kind": "finetune_pack",
    "variant_ids": ["var-finance-cfo"],
    "filters": {
      "has_teacher_output": true,
      "min_length": 50
    }
  }'
```

**Output**: Creates files in `data/packs/finance-analysis-pack@1.0.0/`:
- `train.jsonl` - Training examples (90% split)
- `eval.jsonl` - Evaluation examples (10% split)
- `manifest.json` - Metadata and file hashes

**JSONL Format** (each line is a JSON object):
```json
{"instruction": "Analyze this financial data", "input": "...", "output": "Based on the analysis..."}
{"instruction": "Explain revenue trends", "input": "...", "output": "Revenue shows..."}
```

## Understanding the Output

### Database Tables

The service stores data in PostgreSQL:

| Table | Purpose | Key Fields |
|-------|---------|------------|
| `context_docs` | Context documents | `id`, `title`, `version`, `body_text` |
| `context_variants` | Faceted variants | `id`, `domain`, `persona`, `task`, `style`, `body_text` |
| `chunks` | Text chunks for retrieval | `variant_id`, `order`, `text`, `embedding` |
| `feature_vectors` | Extracted features | `variant_id`, `features_json` |
| `underwriting_runs` | Quality scores | `variant_id`, `risk_score`, `utility_score`, `decision` |
| `synthetic_examples` | Generated examples | `variant_id`, `example_type`, `input_json` |
| `teacher_runs` | LLM outputs | `example_id`, `provider`, `model`, `output_json` |
| `targets` | Distilled labels | `example_id`, `y_text`, `y_probs_json` |
| `dataset_manifests` | Dataset metadata | `name`, `version`, `kind`, `file_uris` |

### Inspecting Data

#### Using the Inspect Script

```bash
docker-compose run --rm api python scripts/inspect_data.py
```

**Output Example**:
```
============================================================
📊 DATABASE INSPECTION
============================================================

📄 ContextDocs: 1
   - ctx-finance-001: Financial Analysis Guidelines (v1.0.0)
     Created: 2025-01-XX XX:XX:XX

🔀 ContextVariants: 1
   - var-finance-cfo:
     Domain: finance, Persona: CFO, Task: analyze, Style: formal
     Body length: 156 chars
     Underwriting: approve (risk=15, utility=75)
     Features: finance/CFO/analyze
     Chunks: 1

✅ UnderwritingRuns: 1
   - uw-abc123:
     Variant: var-finance-cfo
     Decision: approve
     Risk: 15/100, Utility: 75/100

📝 SyntheticExamples: 10
   - ex-001:
     Variant: var-finance-cfo
     Type: instruction
     Teacher runs: 1

🎓 TeacherRuns: 10
   - tr-001:
     Example: ex-001
     Provider: openai, Model: gpt-4o-mini
     Output length: 245 chars
     Tokens: 156

📦 DatasetManifests: 1
   - ds-xyz789: finance-analysis-pack v1.0.0
     Kind: finetune_pack
     Variants: 1
     Files: 3
       - train.jsonl
       - eval.jsonl
       - manifest.json
```

#### Using SQL

```bash
docker-compose exec db psql -U postgres -d nex_collector
```

```sql
-- View all contexts
SELECT id, title, version, LENGTH(body_text) as length 
FROM context_docs;

-- View variants with underwriting decisions
SELECT 
    v.id,
    v.domain,
    v.persona,
    v.task,
    u.decision,
    u.risk_score,
    u.utility_score
FROM context_variants v
LEFT JOIN LATERAL (
    SELECT decision, risk_score, utility_score
    FROM underwriting_runs
    WHERE variant_id = v.id
    ORDER BY created_at DESC
    LIMIT 1
) u ON true;

-- Count examples by type
SELECT example_type, COUNT(*) 
FROM synthetic_examples 
GROUP BY example_type;

-- View teacher run outputs
SELECT 
    tr.id,
    tr.example_id,
    tr.model,
    LENGTH(tr.output_json->>'text') as output_length,
    tr.usage_json->>'total_tokens' as tokens
FROM teacher_runs tr
WHERE tr.output_json IS NOT NULL;
```

### Fine-Tune Pack Structure

When you build a `finetune_pack`, it creates:

```
data/packs/{name}@{version}/
├── train.jsonl          # Training examples (90%)
├── eval.jsonl           # Evaluation examples (10%)
└── manifest.json        # Metadata
```

**manifest.json**:
```json
{
  "id": "ds-xyz789",
  "name": "finance-analysis-pack",
  "version": "1.0.0",
  "kind": "finetune_pack",
  "variant_ids": ["var-finance-cfo"],
  "filters": {"has_teacher_output": true},
  "files": [
    {
      "name": "train.jsonl",
      "path": "/code/data/packs/finance-analysis-pack@1.0.0/train.jsonl",
      "hash": "abc123..."
    },
    {
      "name": "eval.jsonl",
      "path": "/code/data/packs/finance-analysis-pack@1.0.0/eval.jsonl",
      "hash": "def456..."
    }
  ],
  "num_examples": 10,
  "train_size": 9,
  "eval_size": 1
}
```

**train.jsonl** (each line):
```json
{"instruction": "Analyze this financial data", "input": "Revenue: $1M, Expenses: $800K", "output": "Based on the financial data provided, the net profit is $200,000..."}
```

## Example Workflows

### Workflow 1: Generate → Underwrite → Build

```bash
# 1. Generate context from OTS LLM
curl -X POST http://localhost:8080/v1/aggregate/sample \
  -H "Authorization: Bearer dev-secret" \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "openai",
    "model": "gpt-4o-mini",
    "prompt": "Generate finance analysis guidelines",
    "domain": "finance",
    "persona": "CFO"
  }'

# 2. Wait for job to complete, then get variant ID
# (Check worker logs or query database)

# 3. Run underwriting
curl -X POST "http://localhost:8080/v1/underwrite/run?variant_id=var-xxx" \
  -H "Authorization: Bearer dev-secret"

# 4. Generate examples
curl -X POST http://localhost:8080/v1/datasets/distill/examples \
  -H "Authorization: Bearer dev-secret" \
  -H "Content-Type: application/json" \
  -d '{
    "variant_ids": ["var-xxx"],
    "example_type": "instruction",
    "quota_per_variant": 10
  }'

# 5. Collect teacher outputs (for each example)
curl -X POST http://localhost:8080/v1/teachers/runs \
  -H "Authorization: Bearer dev-secret" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "tr-001",
    "example_id": "ex-001",
    "provider": "openai",
    "model": "gpt-4o-mini",
    "params_json": {"temperature": 0.7, "max_tokens": 200}
  }'

# 6. Build fine-tune pack
curl -X POST http://localhost:8080/v1/datasets/distill/build \
  -H "Authorization: Bearer dev-secret" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "finance-pack",
    "version": "1.0.0",
    "kind": "finetune_pack",
    "variant_ids": ["var-xxx"],
    "filters": {"has_teacher_output": true}
  }'

# 7. Inspect results
docker-compose run --rm api python scripts/inspect_data.py
```

### Workflow 2: Mix & Match Facets

```bash
# 1. Create multiple variants with different facets
# var-1: finance/CFO/analyze
# var-2: healthcare/doctor/explain

# 2. Compose new variant
curl -X POST http://localhost:8080/v1/contexts/variants/compose \
  -H "Authorization: Bearer dev-secret" \
  -H "Content-Type: application/json" \
  -d '{
    "source_variant_ids": ["var-1", "var-2"],
    "domain": "finance",
    "persona": "CFO",
    "task": "explain",  // Changed from "analyze"
    "composition_strategy": "merge"
  }'

# 3. Use composed variant for dataset building
```

## Customization

### Custom Rubric

Create `rubrics/custom.json`:

```json
{
  "rubric_id": "custom",
  "utility": {
    "min_length": 200,
    "max_length": 5000,
    "require_sections": true
  },
  "safety": {
    "deny_patterns": ["your custom patterns"]
  },
  "scoring": {
    "decision_thresholds": {
      "approve_risk_max": 25,
      "approve_utility_min": 60
    }
  }
}
```

Use it:
```bash
curl -X POST "http://localhost:8080/v1/underwrite/run?variant_id=var-1&rubric_id=custom"
```

### Configuration

Environment variables in `.env`:

```bash
# Database
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/nex_collector

# Redis
REDIS_URL=redis://localhost:6379/0

# OpenAI
OPENAI_API_KEY=sk-...

# Auth
NEX_WRITE_TOKEN=dev-secret

# Aggregator
AGGREGATOR_INTERVAL_SECS=3600  # Run aggregation every hour
REQUIRE_APPROVAL=true          # Only approved variants for datasets

# Embeddings (optional)
EMBEDDINGS_ENABLED=false       # Set to true to enable embeddings
```

## Troubleshooting

### Database Connection Issues

```bash
# Check if database is running
docker-compose ps db

# Check logs
docker-compose logs db

# Reset database (WARNING: deletes all data)
docker-compose down -v
docker-compose up -d db redis
```

### Migration Issues

```bash
# Check current migration version
docker-compose run --rm api alembic current

# Create new migration
docker-compose run --rm api alembic revision --autogenerate -m "fix_schema"

# Apply migrations
docker-compose run --rm api alembic upgrade head
```

### Worker Not Processing Jobs

```bash
# Check worker logs
docker-compose logs worker

# Restart worker
docker-compose restart worker

# Check Redis connection
docker-compose exec redis redis-cli ping
```

## API Reference

Full API documentation available at: **http://localhost:8080/docs**

### Key Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/v1/contexts` | POST | Create ContextDoc |
| `/v1/contexts/{id}/variants` | POST | Create ContextVariant |
| `/v1/contexts/variants/compose` | POST | Compose variant (mix & match) |
| `/v1/aggregate/sample` | POST | Generate context from OTS LLM |
| `/v1/underwrite/run` | POST | Run underwriting |
| `/v1/datasets/distill/examples` | POST | Generate examples |
| `/v1/teachers/runs` | POST | Collect teacher output |
| `/v1/datasets/distill/build` | POST | Build fine-tune pack |
| `/v1/datasets` | GET | List datasets |

## Next Steps

1. **Customize Rubrics** - Edit `rubrics/default.json` to match your quality standards
2. **Add Providers** - Implement Anthropic/Google providers in `app/providers/`
3. **Enable Embeddings** - Set `EMBEDDINGS_ENABLED=true` for semantic search
4. **Scale Workers** - Run multiple workers: `docker-compose up -d --scale worker=3`
5. **Integrate with NEX** - Set `MODE_INTEGRATION=integrated` to link with your NEX backend

## Support

- API Documentation: http://localhost:8080/docs
- Inspect Data: `python scripts/inspect_data.py`
- View Logs: `docker-compose logs api worker`

