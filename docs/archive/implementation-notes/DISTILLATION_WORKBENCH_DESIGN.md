# Distillation Workbench - Design Document

## Overview

The Distillation Workbench is a unified tool for capturing domain knowledge from SOTA AI models (GPT-4, Claude, Gemini), curating high-quality responses, and building training datasets for fine-tuning smaller models.

## Core Concepts

### Knowledge Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         DISTILLATION WORKBENCH                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                        CAPTURE LAYER                                  │  │
│  │                                                                       │  │
│  │   ┌─────────────────┐              ┌─────────────────┐               │  │
│  │   │   INTERACTIVE   │              │    AUTOMATED    │               │  │
│  │   │                 │              │                 │               │  │
│  │   │ • Chat with     │              │ • Task Library  │               │  │
│  │   │   SOTA models   │              │ • Schedules     │               │  │
│  │   │ • Bank good     │              │ • Multi-model   │               │  │
│  │   │   responses     │              │   execution     │               │  │
│  │   └────────┬────────┘              └────────┬────────┘               │  │
│  │            │                                │                         │  │
│  │            └────────────────┬───────────────┘                        │  │
│  │                             ▼                                         │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                │                                            │
│                                ▼                                            │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                        RESPONSE BANK                                  │  │
│  │                                                                       │  │
│  │   • Raw responses from all models                                     │  │
│  │   • Domain → Topic hierarchy                                          │  │
│  │   • Freeform tags                                                     │  │
│  │   • Quality scores                                                    │  │
│  │   • Embeddings for similarity search                                  │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                │                                            │
│                                ▼                                            │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                        CURATION LAYER                                 │  │
│  │                                                                       │  │
│  │   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐                │  │
│  │   │  COMPARE    │   │  STRUCTURE  │   │   REVIEW    │                │  │
│  │   │             │   │             │   │             │                │  │
│  │   │ • Side-by-  │   │ • Extract   │   │ • Expert    │                │  │
│  │   │   side      │   │   to schema │   │   queue     │                │  │
│  │   │ • Blind     │   │ • Tag →     │   │ • Export    │                │  │
│  │   │   voting    │   │   schema    │   │ • Re-import │                │  │
│  │   │ • A/B pref  │   │   mapping   │   │   ratings   │                │  │
│  │   └─────────────┘   └─────────────┘   └─────────────┘                │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                │                                            │
│                                ▼                                            │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                        DATASET BUILDER                                │  │
│  │                                                                       │  │
│  │   • Training sets (JSONL, Parquet)                                    │  │
│  │   • Evaluation benchmarks                                             │  │
│  │   • Expert review queues                                              │  │
│  │   • Version control                                                   │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Data Model

### 1. Domain & Topic Hierarchy

```sql
-- Flexible domain/topic hierarchy for organizing knowledge
CREATE TABLE distillation_domains (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL UNIQUE,      -- 'insurance', 'finance', 'retail'
    description TEXT,
    icon VARCHAR(50),                        -- For UI
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE distillation_topics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    domain_id UUID REFERENCES distillation_domains(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,              -- 'underwriting', 'claims', 'policy'
    description TEXT,
    parent_topic_id UUID REFERENCES distillation_topics(id),  -- For sub-topics
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(domain_id, name)
);

-- Freeform tags (not tied to hierarchy)
CREATE TABLE distillation_tags (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL UNIQUE,
    color VARCHAR(7),                        -- Hex color for UI
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 2. Task Library (Automated Capture)

```sql
-- Reusable task templates for automated knowledge extraction
CREATE TABLE distillation_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- Organization
    domain_id UUID REFERENCES distillation_domains(id),
    topic_id UUID REFERENCES distillation_topics(id),
    
    -- Task configuration
    task_type VARCHAR(50) NOT NULL,          -- 'qa', 'summary', 'instruction', 'freeform'
    prompt_template TEXT NOT NULL,           -- "Generate {count} Q&A pairs about {topic}"
    system_prompt TEXT,                      -- Optional system context
    variables JSONB DEFAULT '[]',            -- [{name, type, default, required}]
    
    -- Model targeting
    target_models TEXT[] NOT NULL,           -- ['gpt-4o', 'claude-3.5-sonnet', 'gemini-pro']
    
    -- Scheduling
    schedule_cron VARCHAR(100),              -- null = manual only, '0 * * * *' = hourly
    schedule_enabled BOOLEAN DEFAULT false,
    
    -- Metadata
    created_by VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Task execution runs
CREATE TABLE distillation_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID REFERENCES distillation_tasks(id),
    
    -- For ad-hoc runs without a task
    ad_hoc_prompt TEXT,
    ad_hoc_models TEXT[],
    
    -- Execution context
    variables_used JSONB DEFAULT '{}',       -- Actual values used
    trigger_type VARCHAR(20) NOT NULL,       -- 'manual', 'scheduled', 'interactive'
    
    -- Status tracking
    status VARCHAR(20) DEFAULT 'pending',    -- 'pending', 'running', 'completed', 'failed'
    error_message TEXT,
    
    -- Timing
    scheduled_for TIMESTAMPTZ,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    
    created_by VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 3. Response Bank

```sql
-- All responses from SOTA models
CREATE TABLE distillation_responses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id UUID REFERENCES distillation_runs(id),
    
    -- Model info
    provider VARCHAR(50) NOT NULL,           -- 'openai', 'anthropic', 'google'
    model VARCHAR(100) NOT NULL,             -- 'gpt-4o', 'claude-3.5-sonnet'
    
    -- Request/Response
    prompt_sent TEXT NOT NULL,
    system_prompt_used TEXT,
    response_text TEXT NOT NULL,             -- Raw response
    
    -- Metrics
    tokens_input INT,
    tokens_output INT,
    latency_ms INT,
    
    -- For similarity search & dedup
    embedding vector(1536),
    
    -- Organization (can be set later)
    domain_id UUID REFERENCES distillation_domains(id),
    topic_id UUID REFERENCES distillation_topics(id),
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Many-to-many: responses <-> tags
CREATE TABLE distillation_response_tags (
    response_id UUID REFERENCES distillation_responses(id) ON DELETE CASCADE,
    tag_id UUID REFERENCES distillation_tags(id) ON DELETE CASCADE,
    PRIMARY KEY (response_id, tag_id)
);

-- Banked (curated) responses
CREATE TABLE distillation_banked (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    response_id UUID REFERENCES distillation_responses(id),
    
    -- Can override organization from response
    domain_id UUID REFERENCES distillation_domains(id),
    topic_id UUID REFERENCES distillation_topics(id),
    
    -- Curation
    quality_score FLOAT,                     -- 0.0 - 1.0
    notes TEXT,
    
    -- Status
    status VARCHAR(20) DEFAULT 'draft',      -- 'draft', 'reviewed', 'approved', 'rejected'
    
    banked_by VARCHAR(100),
    banked_at TIMESTAMPTZ DEFAULT NOW(),
    reviewed_by VARCHAR(100),
    reviewed_at TIMESTAMPTZ
);

-- Structured extractions from banked responses
CREATE TABLE distillation_structured (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    banked_id UUID REFERENCES distillation_banked(id),
    
    -- The extracted structure
    schema_name VARCHAR(100),                -- 'qa_pair', 'instruction', 'summary'
    structured_data JSONB NOT NULL,          -- The actual structured content
    
    -- Extraction metadata
    extraction_method VARCHAR(50),           -- 'manual', 'llm_assisted', 'rule_based'
    extracted_by VARCHAR(100),
    extracted_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 4. Comparison & Preferences

```sql
-- Model comparison sessions
CREATE TABLE distillation_comparisons (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id UUID REFERENCES distillation_runs(id),
    
    -- Comparison setup
    comparison_type VARCHAR(20) NOT NULL,    -- 'side_by_side', 'blind', 'ab_preference'
    prompt_used TEXT NOT NULL,
    
    -- Status
    status VARCHAR(20) DEFAULT 'pending',    -- 'pending', 'completed'
    
    created_by VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Responses included in a comparison
CREATE TABLE distillation_comparison_responses (
    comparison_id UUID REFERENCES distillation_comparisons(id) ON DELETE CASCADE,
    response_id UUID REFERENCES distillation_responses(id),
    display_order INT,                       -- For UI ordering
    display_label VARCHAR(10),               -- 'A', 'B', 'C' for blind comparisons
    PRIMARY KEY (comparison_id, response_id)
);

-- Votes/preferences on comparisons
CREATE TABLE distillation_votes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    comparison_id UUID REFERENCES distillation_comparisons(id),
    
    -- The vote
    winner_response_id UUID REFERENCES distillation_responses(id),
    vote_type VARCHAR(20) NOT NULL,          -- 'winner', 'ranking', 'rating'
    rankings JSONB,                          -- For ranked votes: [{response_id, rank}]
    ratings JSONB,                           -- For rated votes: [{response_id, score}]
    
    -- Voter info
    voter VARCHAR(100),
    voter_type VARCHAR(20) DEFAULT 'user',   -- 'user', 'expert', 'automated'
    notes TEXT,
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 5. Expert Review

```sql
-- Review queues for expert evaluation
CREATE TABLE distillation_review_queues (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- Filtering criteria for auto-populating
    domain_id UUID REFERENCES distillation_domains(id),
    topic_id UUID REFERENCES distillation_topics(id),
    min_quality_score FLOAT,
    
    -- Assignment
    assigned_experts TEXT[],                 -- List of expert usernames
    
    created_by VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Items in review queue
CREATE TABLE distillation_review_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    queue_id UUID REFERENCES distillation_review_queues(id),
    banked_id UUID REFERENCES distillation_banked(id),
    
    -- Review status
    status VARCHAR(20) DEFAULT 'pending',    -- 'pending', 'in_review', 'approved', 'rejected'
    assigned_to VARCHAR(100),
    
    -- Review outcome
    review_notes TEXT,
    review_score FLOAT,
    reviewed_at TIMESTAMPTZ,
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Export/import tracking for offline review
CREATE TABLE distillation_review_exports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    queue_id UUID REFERENCES distillation_review_queues(id),
    
    -- Export details
    export_format VARCHAR(20) NOT NULL,      -- 'csv', 'json', 'xlsx'
    file_path VARCHAR(500),
    item_count INT,
    
    -- Import tracking
    imported_at TIMESTAMPTZ,
    items_updated INT,
    
    exported_by VARCHAR(100),
    exported_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 6. Dataset Builder

```sql
-- Curated datasets for training/evaluation
CREATE TABLE distillation_datasets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    version VARCHAR(50) NOT NULL,
    description TEXT,
    
    -- Type
    dataset_type VARCHAR(50) NOT NULL,       -- 'training', 'evaluation', 'benchmark'
    
    -- Organization
    domain_id UUID REFERENCES distillation_domains(id),
    
    -- Filtering/selection criteria (how items were chosen)
    selection_criteria JSONB DEFAULT '{}',
    
    -- Stats
    item_count INT DEFAULT 0,
    
    -- Export
    export_format VARCHAR(20),               -- 'jsonl', 'parquet', 'csv'
    export_path VARCHAR(500),
    
    -- Status
    status VARCHAR(20) DEFAULT 'draft',      -- 'draft', 'building', 'ready', 'exported'
    
    created_by VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(name, version)
);

-- Items in a dataset (links to banked or structured)
CREATE TABLE distillation_dataset_items (
    dataset_id UUID REFERENCES distillation_datasets(id) ON DELETE CASCADE,
    banked_id UUID REFERENCES distillation_banked(id),
    structured_id UUID REFERENCES distillation_structured(id),
    
    -- For train/val/test splits
    split VARCHAR(20) DEFAULT 'train',       -- 'train', 'validation', 'test'
    
    -- Order in dataset
    sequence_order INT,
    
    added_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## Structured Schemas

Predefined schemas for structuring raw responses:

### Q&A Pair Schema
```json
{
  "schema_name": "qa_pair",
  "fields": {
    "question": "string",
    "answer": "string",
    "context": "string (optional)",
    "difficulty": "string (easy/medium/hard)",
    "category": "string"
  }
}
```

### Instruction Schema
```json
{
  "schema_name": "instruction",
  "fields": {
    "instruction": "string",
    "input": "string (optional)",
    "output": "string",
    "reasoning": "string (optional)"
  }
}
```

### Summary Schema
```json
{
  "schema_name": "summary",
  "fields": {
    "source_text": "string",
    "summary": "string",
    "key_points": "string[]",
    "summary_type": "string (brief/detailed/bullet)"
  }
}
```

### Freeform Schema
```json
{
  "schema_name": "freeform",
  "fields": {
    "content": "string",
    "metadata": "object"
  }
}
```

---

## UI Screens

### 1. Workbench Home
- Overview dashboard
- Recent runs
- Quick actions (New Task, Start Chat, Browse Bank)
- Schedule status

### 2. Task Library
- List all tasks
- Create/edit task templates
- Configure schedules
- Test run a task

### 3. Interactive Chat
- Multi-model chat interface
- "Bank This" button on good responses
- Quick tagging
- Domain/topic assignment

### 4. Run Console
- Execute tasks manually
- See live progress
- View all responses from a run
- Quick compare button

### 5. Response Bank
- Browse all responses
- Filter by domain/topic/tags/model
- Search by content
- Bulk actions (tag, bank, delete)
- Similarity search

### 6. Compare View
- Side-by-side model outputs
- Blind comparison mode
- A/B preference voting
- Winner selection

### 7. Structuring Editor
- Select banked response
- Choose schema
- Extract fields (manual or LLM-assisted)
- Preview structured output

### 8. Expert Review
- Review queue list
- Individual item review
- Approve/reject workflow
- Export for offline review
- Import ratings

### 9. Dataset Builder
- Create new dataset
- Add items from bank
- Configure splits
- Export to format
- Version management

### 10. Schedule Monitor
- View all scheduled tasks
- See upcoming runs
- Review past runs
- Enable/disable schedules

---

## API Endpoints

### Domains & Topics
```
GET    /api/v1/distillation/domains
POST   /api/v1/distillation/domains
GET    /api/v1/distillation/domains/{id}/topics
POST   /api/v1/distillation/topics
```

### Tasks
```
GET    /api/v1/distillation/tasks
POST   /api/v1/distillation/tasks
GET    /api/v1/distillation/tasks/{id}
PATCH  /api/v1/distillation/tasks/{id}
DELETE /api/v1/distillation/tasks/{id}
POST   /api/v1/distillation/tasks/{id}/run
```

### Runs & Responses
```
GET    /api/v1/distillation/runs
GET    /api/v1/distillation/runs/{id}
GET    /api/v1/distillation/runs/{id}/responses
POST   /api/v1/distillation/runs/adhoc          # Ad-hoc run without task
```

### Response Bank
```
GET    /api/v1/distillation/responses
GET    /api/v1/distillation/responses/{id}
PATCH  /api/v1/distillation/responses/{id}      # Update tags, domain, topic
POST   /api/v1/distillation/responses/{id}/bank
POST   /api/v1/distillation/responses/search    # Semantic search
```

### Comparisons
```
POST   /api/v1/distillation/comparisons
GET    /api/v1/distillation/comparisons/{id}
POST   /api/v1/distillation/comparisons/{id}/vote
```

### Banked & Structured
```
GET    /api/v1/distillation/banked
GET    /api/v1/distillation/banked/{id}
PATCH  /api/v1/distillation/banked/{id}
POST   /api/v1/distillation/banked/{id}/structure
```

### Expert Review
```
GET    /api/v1/distillation/review-queues
POST   /api/v1/distillation/review-queues
GET    /api/v1/distillation/review-queues/{id}/items
POST   /api/v1/distillation/review-queues/{id}/export
POST   /api/v1/distillation/review-queues/{id}/import
PATCH  /api/v1/distillation/review-items/{id}   # Review action
```

### Datasets
```
GET    /api/v1/distillation/datasets
POST   /api/v1/distillation/datasets
GET    /api/v1/distillation/datasets/{id}
POST   /api/v1/distillation/datasets/{id}/items
POST   /api/v1/distillation/datasets/{id}/export
```

### Tags
```
GET    /api/v1/distillation/tags
POST   /api/v1/distillation/tags
```

---

## Implementation Phases

### Phase 1: Foundation (Week 1)
- [ ] Database migrations for all tables
- [ ] Domain/Topic/Tag management (backend + UI)
- [ ] Basic response storage

### Phase 2: Capture Layer (Week 2)
- [ ] Interactive chat with multi-model support
- [ ] "Bank This" functionality
- [ ] Task library CRUD
- [ ] Manual task execution

### Phase 3: Response Bank (Week 3)
- [ ] Response browser with filters
- [ ] Tagging interface
- [ ] Domain/topic assignment
- [ ] Semantic search with embeddings

### Phase 4: Comparison & Voting (Week 4)
- [ ] Side-by-side comparison view
- [ ] Blind comparison mode
- [ ] A/B preference voting
- [ ] Preference tracking

### Phase 5: Structuring (Week 5)
- [ ] Schema definitions
- [ ] Manual structuring UI
- [ ] LLM-assisted extraction
- [ ] Tag → schema mapping

### Phase 6: Expert Review (Week 6)
- [ ] Review queue management
- [ ] In-app review workflow
- [ ] Export for offline review
- [ ] Import ratings

### Phase 7: Dataset Builder (Week 7)
- [ ] Dataset creation
- [ ] Item curation
- [ ] Train/val/test splits
- [ ] Export formats (JSONL, Parquet)

### Phase 8: Scheduling (Week 8)
- [ ] Cron-based task scheduling
- [ ] Schedule monitor UI
- [ ] Background job runner

---

## File Structure

```
backend/
├── domains/
│   └── distillation/
│       ├── __init__.py
│       ├── router.py              # All API endpoints
│       ├── service.py             # Business logic
│       ├── models.py              # SQLAlchemy models
│       ├── schemas.py             # Pydantic schemas
│       ├── scheduler.py           # Background scheduling
│       └── providers/
│           ├── __init__.py
│           ├── base.py            # Provider interface
│           ├── openai.py
│           ├── anthropic.py
│           └── google.py
│
├── migrations/
│   └── versions/
│       └── xxx_add_distillation_tables.py

frontend/
├── src/
│   ├── pages/
│   │   ├── DistillationWorkbench.tsx    # Main workbench
│   │   ├── DistillationTasks.tsx        # Task library
│   │   ├── DistillationChat.tsx         # Interactive chat
│   │   ├── DistillationBank.tsx         # Response bank
│   │   ├── DistillationCompare.tsx      # Comparison view
│   │   ├── DistillationReview.tsx       # Expert review
│   │   └── DistillationDatasets.tsx     # Dataset builder
│   │
│   └── components/
│       └── distillation/
│           ├── TaskForm.tsx
│           ├── ResponseCard.tsx
│           ├── ComparisonPanel.tsx
│           ├── StructuringEditor.tsx
│           └── DatasetBuilder.tsx
```

---

## Next Steps

1. **Review this design** - Any changes needed?
2. **Start with Phase 1** - Create migrations and basic CRUD
3. **Build incrementally** - Each phase adds functionality

Ready to start implementation?
