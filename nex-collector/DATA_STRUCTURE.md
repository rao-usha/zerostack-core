# NEX Context Aggregator - Data Structure Guide

This document explains the data structure, relationships, and provides examples from the insurance underwriter seed data.

## Table of Contents

1. [Overview](#overview)
2. [Data Flow](#data-flow)
3. [Entity Relationships](#entity-relationships)
4. [Core Entities](#core-entities)
5. [Example Data](#example-data)
6. [Querying Data](#querying-data)

## Overview

The NEX Context Aggregator stores **contexts** (documents) that can be used to generate training data for smaller models. The system follows this hierarchy:

```
ContextDoc (Document)
  └── ContextVariant (Domain/Persona/Task specific view)
      ├── Chunk (Text chunks for retrieval)
      ├── FeatureVector (Extracted features)
      └── SyntheticExample (Training examples)
          ├── TeacherRun (LLM outputs)
          └── Targets (Distilled labels)
  └── DatasetManifest (Exported datasets)
```

## Data Flow

```
1. Create ContextDoc
   ↓
2. Create ContextVariant (with domain/persona/task)
   ↓
3. Generate SyntheticExamples from Variant
   ↓
4. Run TeacherRuns (get LLM outputs)
   ↓
5. Extract Targets (distill labels)
   ↓
6. Build DatasetManifest (export fine-tune pack)
```

## Entity Relationships

```
ContextDoc (1) ──< (many) ContextVariant
ContextVariant (1) ──< (many) Chunk
ContextVariant (1) ──< (1) FeatureVector
ContextVariant (1) ──< (many) SyntheticExample
SyntheticExample (1) ──< (many) TeacherRun
SyntheticExample (1) ──< (1) Targets
ContextDoc (1) ──< (many) DatasetManifest
```

## Core Entities

### 1. ContextDoc

**Purpose**: A versioned document containing context text (guidelines, policies, instructions).

**Fields**:
- `id` (String, PK): Unique identifier (e.g., `ctx-insurance-underwriter-v1`)
- `title` (String): Human-readable title
- `version` (String): Version number (e.g., `1.0.0`)
- `body_text` (Text): The actual context content
- `metadata_json` (JSON): Additional metadata
- `nex_context_id` (String, optional): Link to NEX system
- `embedding_centroid` (JSON, optional): Average embedding vector per version for concept drift detection
- `created_at` (DateTime): Creation timestamp

**Example**:
```json
{
  "id": "ctx-insurance-underwriter-v1",
  "title": "Insurance Underwriting Guidelines",
  "version": "1.0.0",
  "body_text": "# Insurance Underwriting Context\n\n## Role: Senior Insurance Underwriter\n\nYou are an experienced insurance underwriter...",
  "metadata_json": {},
  "embedding_centroid": [0.1, 0.2, 0.3, ...],
  "created_at": "2025-01-15T10:30:00Z"
}
```

### 2. ContextVariant

**Purpose**: A specific view of a context with domain/persona/task facets. Enables mix-and-match and filtering.

**Fields**:
- `id` (String, PK): Unique identifier (e.g., `var-insurance-underwriter-risk-assessment`)
- `context_id` (String, FK): References `ContextDoc.id`
- `domain` (String, indexed): Domain category (e.g., `insurance`, `finance`, `healthcare`)
- `persona` (String, indexed): Persona/role (e.g., `underwriter`, `CFO`, `doctor`)
- `task` (String, indexed): Task type (e.g., `risk_assessment`, `explain`, `classify`)
- `style` (String): Style descriptor (e.g., `formal`, `conversational`)
- `constraints_json` (JSON): Task-specific constraints
- `body_text` (Text): Variant-specific text (may be same as ContextDoc or modified)
- `parent_variant_id` (String, FK, optional): For variant composition
- `created_at` (DateTime): Creation timestamp

**Example**:
```json
{
  "id": "var-insurance-underwriter-risk-assessment",
  "context_id": "ctx-insurance-underwriter-v1",
  "domain": "insurance",
  "persona": "underwriter",
  "task": "risk_assessment",
  "style": "professional",
  "constraints_json": {},
  "body_text": "# Insurance Underwriting Context\n\n## Role: Senior Insurance Underwriter...",
  "created_at": "2025-01-15T10:31:00Z"
}
```

**Querying**: You can filter variants by domain, persona, or task:
```sql
SELECT * FROM context_variants 
WHERE domain = 'insurance' 
  AND persona = 'underwriter';
```

### 3. Chunk

**Purpose**: Text chunks for semantic search and embeddings.

**Fields**:
- `id` (String, PK): Unique identifier
- `variant_id` (String, FK): References `ContextVariant.id`
- `order` (Integer): Chunk order in document
- `text` (Text): Chunk text content
- `embedding` (JSON): Vector embedding (if embeddings enabled)
- `source_uri` (String, optional): URI of source document for provenance tracking
- `source_span` (JSON, optional): Character offsets `{start: int, end: int}` indicating where this chunk came from in the source
- `citation_ids` (Array[String], optional): Array of citation IDs referencing source material
- `text_hash` (String, optional, indexed): Hash of text content for de-duplication
- `license` (String, optional): License information for compliance
- `usage_rights` (String, optional): Usage rights information
- `quality_scores_json` (JSON, optional): Quality scores (e.g., `{coherence: 0.9, faithfulness: 0.85, toxicity: 0.1, pii_flags: []}`)
- `confidence` (Float, optional): Overall confidence score (0.0-1.0)
- `neighbors` (Array[String], optional): Bidirectional links to neighboring chunk IDs for document structure retention
- `section_hierarchy` (JSON, optional): Document structure (e.g., `{level: 1, section: "Introduction", subsection: "Overview"}`)
- `chunk_type` (String, optional): Structural type: `"heading"`, `"bullet"`, `"paragraph"`, `"code"`, etc.
- `overlap_start` (Integer, optional): Start character offset for overlap window (for semantic chunking)
- `overlap_end` (Integer, optional): End character offset for overlap window (for semantic chunking)
- `created_at` (DateTime): Creation timestamp

**Example**:
```json
{
  "id": "chunk-var-insurance-underwriter-risk-assessment-0",
  "variant_id": "var-insurance-underwriter-risk-assessment",
  "order": 0,
  "text": "# Insurance Underwriting Context\n\n## Role: Senior Insurance Underwriter\n\nYou are an experienced insurance underwriter responsible for evaluating risk...",
  "embedding": null,
  "source_uri": "https://example.com/insurance-guidelines.pdf",
  "source_span": {"start": 0, "end": 245},
  "citation_ids": ["cite-guidelines-2024"],
  "text_hash": "sha256:abc123...",
  "license": "CC-BY-4.0",
  "usage_rights": "commercial-use-allowed",
  "quality_scores_json": {
    "coherence": 0.92,
    "faithfulness": 0.88,
    "toxicity": 0.05,
    "pii_flags": []
  },
  "confidence": 0.90,
  "neighbors": ["chunk-var-insurance-underwriter-risk-assessment-1", "chunk-var-insurance-underwriter-risk-assessment-2"],
  "section_hierarchy": {
    "level": 1,
    "section": "Introduction",
    "subsection": "Role Definition"
  },
  "chunk_type": "heading",
  "overlap_start": 0,
  "overlap_end": 50,
  "created_at": "2025-01-15T10:31:05Z"
}
```

### 4. FeatureVector

**Purpose**: Extracted structured features for mix-and-match composition.

**Fields**:
- `id` (String, PK): Unique identifier
- `variant_id` (String, FK, unique): References `ContextVariant.id`
- `features_json` (JSON): Extracted features
- `created_at` (DateTime): Creation timestamp

**Example**:
```json
{
  "id": "fv-var-insurance-underwriter-risk-assessment",
  "variant_id": "var-insurance-underwriter-risk-assessment",
  "features_json": {
    "domain": "insurance",
    "persona": "underwriter",
    "task": "risk_assessment",
    "style": "professional",
    "complexity": "medium",
    "formality": "high",
    "length_category": "long"
  },
  "created_at": "2025-01-15T10:31:10Z"
}
```

### 5. SyntheticExample

**Purpose**: Training examples generated from variants.

**Fields**:
- `id` (String, PK): Unique identifier (e.g., `ex-abc123def456`)
- `variant_id` (String, FK): References `ContextVariant.id`
- `example_type` (Enum): `instruction`, `qa`, or `task`
- `input_json` (JSON): Example input data
- `constraints_json` (JSON): Constraints for this example
- `tags` (Array[String]): Tags for filtering (e.g., `["domain:insurance", "persona:underwriter"]`)
- `source_uri` (String, optional): URI of source document for provenance tracking
- `source_span` (JSON, optional): Character offsets `{start: int, end: int}` indicating where this example came from
- `citation_ids` (Array[String], optional): Array of citation IDs referencing source material
- `text_hash` (String, optional, indexed): Hash of input_json for de-duplication
- `license` (String, optional): License information for compliance
- `usage_rights` (String, optional): Usage rights information
- `retrieval_context_ids` (Array[String], optional): Chunk IDs used during retrieval (for MMR/query-aware selection)
- `semantic_hash` (String, optional, indexed): SimHash/MinHash for near-duplicate detection
- `created_at` (DateTime): Creation timestamp

**Example Types**:

**Task Example**:
```json
{
  "id": "ex-abc123def456",
  "variant_id": "var-insurance-underwriter-risk-assessment",
  "example_type": "task",
  "input_json": {
    "task": "risk_assessment",
    "input": "Process this insurance context",
    "context_preview": "# Insurance Underwriting Context\n\n## Role: Senior Insurance Underwriter...",
    "domain": "insurance",
    "persona": "underwriter"
  },
  "constraints_json": {},
  "tags": ["domain:insurance", "persona:underwriter", "task:risk_assessment"],
  "retrieval_context_ids": ["chunk-var-insurance-underwriter-risk-assessment-0", "chunk-var-insurance-underwriter-risk-assessment-1"],
  "created_at": "2025-01-15T10:35:00Z"
}
```

**QA Example**:
```json
{
  "id": "ex-def456ghi789",
  "variant_id": "var-insurance-underwriter-risk-assessment",
  "example_type": "qa",
  "input_json": {
    "question": "What does the insurance context say about risk_assessment?",
    "context_preview": "# Insurance Underwriting Context...",
    "domain": "insurance"
  },
  "constraints_json": {},
  "tags": ["domain:insurance", "persona:underwriter", "task:risk_assessment"],
  "created_at": "2025-01-15T10:35:05Z"
}
```

**Instruction Example**:
```json
{
  "id": "ex-ghi789jkl012",
  "variant_id": "var-insurance-underwriter-risk-assessment",
  "example_type": "instruction",
  "input_json": {
    "instruction": "Based on the insurance context, provide instructions for: risk_assessment",
    "context_preview": "# Insurance Underwriting Context...",
    "domain": "insurance",
    "persona": "underwriter"
  },
  "constraints_json": {},
  "tags": ["domain:insurance", "persona:underwriter", "task:risk_assessment"],
  "created_at": "2025-01-15T10:35:10Z"
}
```

### 6. TeacherRun

**Purpose**: Outputs from off-the-shelf LLMs (e.g., GPT-4) used to label examples.

**Fields**:
- `id` (String, PK): Unique identifier
- `example_id` (String, FK): References `SyntheticExample.id`
- `provider` (String): LLM provider (e.g., `openai`)
- `model` (String): Model name (e.g., `gpt-4o-mini`)
- `params_json` (JSON): Generation parameters
- `output_json` (JSON): Model output (text, usage, logprobs)
- `usage_json` (JSON): Token usage statistics
- `rand_seed` (Integer, optional): Random seed for reproducibility
- `temperature` (Float, optional): Temperature parameter used for generation
- `decoding_params` (JSON, optional): Additional decoding parameters (e.g., `{top_p: 0.9, top_k: 50}`)
- `quality_scores_json` (JSON, optional): Quality scores (e.g., `{coherence: 0.9, faithfulness: 0.85, toxicity: 0.1, pii_flags: []}`)
- `confidence` (Float, optional): Overall confidence score (0.0-1.0)
- `created_at` (DateTime): Creation timestamp

**Example**:
```json
{
  "id": "tr-xyz789abc123",
  "example_id": "ex-abc123def456",
  "provider": "openai",
  "model": "gpt-4o-mini",
  "params_json": {
    "temperature": 0.7,
    "max_tokens": 200
  },
  "rand_seed": 42,
  "temperature": 0.7,
  "decoding_params": {
    "top_p": 0.9,
    "top_k": 50
  },
  "output_json": {
    "text": "Based on the provided context, I would assess the risk level as moderate...",
    "usage": {
      "prompt_tokens": 150,
      "completion_tokens": 85,
      "total_tokens": 235
    }
  },
  "usage_json": {
    "prompt_tokens": 150,
    "completion_tokens": 85,
    "total_tokens": 235
  },
  "quality_scores_json": {
    "coherence": 0.88,
    "faithfulness": 0.92,
    "toxicity": 0.02,
    "pii_flags": []
  },
  "confidence": 0.87,
  "rationale_json": {
    "reasoning_steps": [
      "First, I need to analyze the risk factors mentioned in the context",
      "Then, I'll compare them against standard underwriting criteria",
      "Finally, I'll determine the appropriate risk level"
    ],
    "conclusion": "Based on the analysis, the risk level is moderate."
  },
  "created_at": "2025-01-15T10:40:00Z"
}
```

### 7. Targets

**Purpose**: Distilled labels/soft-labels extracted from teacher runs.

**Fields**:
- `id` (String, PK): Unique identifier
- `example_id` (String, FK, unique): References `SyntheticExample.id`
- `y_text` (Text): Target text (from teacher output)
- `y_probs_json` (JSON): Soft label probabilities
- `y_scores_json` (JSON): Quality scores
- `source_uri` (String, optional): URI of source document for provenance tracking
- `source_span` (JSON, optional): Character offsets `{start: int, end: int}` indicating where this target came from
- `citation_ids` (Array[String], optional): Array of citation IDs referencing source material
- `quality_scores_json` (JSON, optional): Quality scores (e.g., `{coherence: 0.9, faithfulness: 0.85, toxicity: 0.1, pii_flags: []}`)
- `confidence` (Float, optional): Overall confidence score (0.0-1.0)
- `justification` (Text, optional): Short, verifiable justification distilled from teacher rationales (safe for student, no private CoT)
- `faithfulness_score` (Float, optional): Score from critic pass (0.0-1.0) indicating faithfulness to source material
- `created_at` (DateTime): Creation timestamp

**Example**:
```json
{
  "id": "target-abc123def456",
  "example_id": "ex-abc123def456",
  "y_text": "Based on the provided context, I would assess the risk level as moderate...",
  "y_probs_json": {
    "token_probs": {
      "moderate": 0.45,
      "low": 0.30,
      "high": 0.25
    },
    "class_probs": {
      "moderate": 0.50,
      "low": 0.30,
      "high": 0.20
    },
    "num_runs": 3,
    "aggregation_method": "weighted_mean"
  },
  "y_scores_json": {
    "quality": 0.85,
    "relevance": 0.92
  },
  "source_uri": "https://example.com/insurance-guidelines.pdf",
  "source_span": {"start": 150, "end": 300},
  "citation_ids": ["cite-guidelines-2024", "cite-risk-assessment-section"],
  "quality_scores_json": {
    "coherence": 0.90,
    "faithfulness": 0.93,
    "toxicity": 0.01,
    "pii_flags": []
  },
  "confidence": 0.91,
  "justification": "Based on risk assessment guidelines, the risk level is moderate due to standard factors.",
  "faithfulness_score": 0.88,
  "created_at": "2025-01-15T10:41:00Z"
}
```

### 8. DatasetManifest

**Purpose**: Metadata for exported datasets/fine-tune packs.

**Fields**:
- `id` (String, PK): Unique identifier (e.g., `ds-abc123def456`)
- `name` (String): Dataset name (e.g., `insurance-underwriter-risk-assessment`)
- `version` (String): Version (e.g., `1.0.0`)
- `kind` (Enum): `train`, `eval`, `synthetic`, or `finetune_pack`
- `context_id` (String, FK, optional): References `ContextDoc.id`
- `variant_ids` (Array[String]): Variant IDs included in dataset
- `file_uris` (Array[String]): Paths to dataset files
- `filters_json` (JSON): Filters applied when building dataset
- `created_at` (DateTime): Creation timestamp

**Example**:
```json
{
  "id": "ds-insurance-underwriter-v1",
  "name": "insurance-underwriter-risk-assessment",
  "version": "1.0.0",
  "kind": "finetune_pack",
  "context_id": "ctx-insurance-underwriter-v1",
  "variant_ids": ["var-insurance-underwriter-risk-assessment"],
  "file_uris": [
    "nex-collector/data/packs/insurance-underwriter-risk-assessment@1.0.0/train.jsonl",
    "nex-collector/data/packs/insurance-underwriter-risk-assessment@1.0.0/eval.jsonl",
    "nex-collector/data/packs/insurance-underwriter-risk-assessment@1.0.0/manifest.json"
  ],
  "filters_json": {},
  "created_at": "2025-01-15T10:45:00Z"
}
```

## Example Data

### Insurance Underwriter Seed Data

When you run `seed_insurance_underwriter.py`, it creates:

1. **ContextDoc**: `ctx-insurance-underwriter-v1`
   - Title: "Insurance Underwriting Guidelines"
   - Contains comprehensive underwriting guidelines

2. **ContextVariant**: `var-insurance-underwriter-risk-assessment`
   - Domain: `insurance`
   - Persona: `underwriter`
   - Task: `risk_assessment`
   - Style: `professional`

When you run `seed_insurance_dataset.py`, it creates:

3. **SyntheticExamples**: 10 examples
   - 5 task examples
   - 3 QA examples
   - 2 instruction examples

4. **DatasetManifest**: `ds-insurance-underwriter-v1`
   - Fine-tune pack with train/eval splits
   - Files saved to `nex-collector/data/packs/insurance-underwriter-risk-assessment@1.0.0/`

### Fine-Tune Pack Format

The fine-tune pack contains JSONL files:

**train.jsonl**:
```jsonl
{"instruction": "Based on the insurance context, provide instructions for: risk_assessment", "input": "# Insurance Underwriting Context...", "output": ""}
{"instruction": "What does the insurance context say about risk_assessment?", "input": "# Insurance Underwriting Context...", "output": ""}
...
```

**eval.jsonl**:
```jsonl
{"instruction": "...", "input": "...", "output": ""}
...
```

**manifest.json**:
```json
{
  "id": "ds-insurance-underwriter-v1",
  "name": "insurance-underwriter-risk-assessment",
  "version": "1.0.0",
  "kind": "finetune_pack",
  "variant_ids": ["var-insurance-underwriter-risk-assessment"],
  "files": [
    {"name": "train.jsonl", "path": "...", "hash": "..."},
    {"name": "eval.jsonl", "path": "...", "hash": "..."}
  ],
  "num_examples": 10,
  "train_size": 9,
  "eval_size": 1
}
```

## Querying Data

### Via API

**Get all insurance variants**:
```bash
curl "http://localhost:8080/v1/contexts/variants?domain=insurance" \
  -H "Authorization: Bearer dev-secret"
```

**Get specific variant**:
```bash
curl "http://localhost:8080/v1/contexts/variants/var-insurance-underwriter-risk-assessment" \
  -H "Authorization: Bearer dev-secret"
```

**List datasets**:
```bash
curl "http://localhost:8080/v1/datasets" \
  -H "Authorization: Bearer dev-secret"
```

**Get dataset manifest**:
```bash
curl "http://localhost:8080/v1/datasets/ds-insurance-underwriter-v1" \
  -H "Authorization: Bearer dev-secret"
```

### Via SQL

**Find all variants for a domain**:
```sql
SELECT id, domain, persona, task 
FROM context_variants 
WHERE domain = 'insurance';
```

**Count examples by type**:
```sql
SELECT example_type, COUNT(*) 
FROM synthetic_examples 
WHERE variant_id = 'var-insurance-underwriter-risk-assessment'
GROUP BY example_type;
```

**Get examples with teacher outputs**:
```sql
SELECT se.id, se.example_type, tr.output_json->>'text' as teacher_output
FROM synthetic_examples se
LEFT JOIN teacher_runs tr ON se.id = tr.example_id
WHERE se.variant_id = 'var-insurance-underwriter-risk-assessment'
  AND tr.output_json IS NOT NULL;
```

## Data Storage Locations

- **Database**: PostgreSQL (`nex_collector` database in `nex_db` container)
- **Files**: `nex-collector/data/packs/{name}@{version}/`
  - `train.jsonl`: Training examples
  - `eval.jsonl`: Evaluation examples
  - `manifest.json`: Dataset metadata

## Key Concepts

### Domains

Domains are **scalable** - you can add any domain without schema changes:
- `insurance`
- `finance`
- `healthcare`
- `legal`
- `education`
- etc.

### Facets (Mix & Match)

Variants are composed of facets:
- **Domain**: What industry/domain?
- **Persona**: What role/perspective?
- **Task**: What task to perform?
- **Style**: What communication style?

This enables:
- Querying by any facet
- Composing new variants from existing ones
- Filtering datasets by facets

### Example Types

Three types of training examples:
1. **Task**: Task-oriented examples
2. **QA**: Question-answer pairs
3. **Instruction**: Instruction-following examples

### Knowledge Distillation Flow

1. **Context** → Document with guidelines
2. **Variant** → Domain/persona/task specific view
3. **Examples** → Synthetic training examples
4. **Teacher Runs** → LLM outputs (labels)
5. **Targets** → Distilled labels
6. **Dataset** → Fine-tune pack ready for training

## Next Steps

- **Inspect Data**: Run `python scripts/inspect_data.py` to see what's in the database
- **Add More Domains**: Create new ContextDocs and Variants for other domains
- **Generate More Examples**: Use `/v1/datasets/distill/examples` to generate more examples
- **Run Teacher Runs**: Use `/v1/teachers/runs` to get LLM outputs for examples
- **Build Datasets**: Use `/v1/datasets/distill/build` to create fine-tune packs

