# Data Dictionary

The Data Dictionary system provides AI-powered, persistent documentation for database columns with versioning, approval workflows, and semantic enrichment.

## Overview

The Data Dictionary enables you to:
- **AI-Generated Documentation**: Automatically generate business descriptions, technical details, tags, and examples for all columns
- **Human-in-the-Loop Editing**: Refine AI suggestions with manual edits that are protected from overwrites
- **Full Versioning**: Track all changes with version history and ability to restore previous versions
- **Approval Workflow**: Draft → Approved → Published workflow for governance
- **Semantic Enrichment**: Decision context, guarantees, validation states, and relationship intelligence

## Quick Start

### 1. Generate Initial Documentation

1. Navigate to **Data Analysis** (`/analysis`)
2. Select database and tables
3. Choose **"Column Documentation"** as analysis type
4. Select LLM provider and model
5. Click **"Create Job"**

### 2. View Documentation

1. Navigate to **Data Dictionary** (`/dictionary`)
2. Browse entries grouped by schema and table
3. Filter by schema, table, or search terms

### 3. Edit Entries

1. Click **Edit** on any column
2. Update business description, tags, etc.
3. Click **Save** (optionally create new version)
4. Entry marked as `human_edited` (protected from AI overwrites)

---

## Features

### Core Data Dictionary

| Feature | Description |
|---------|-------------|
| **Business Name** | Human-friendly column name |
| **Business Description** | Plain-language meaning |
| **Technical Description** | Precise technical definition |
| **Data Type** | Observed data type |
| **Examples** | Sample values from data |
| **Tags** | Categories: PII, metric, identifier, foreign_key, etc. |
| **Source** | `llm_initial` or `human_edited` |

### Versioning System

- **Version Numbers**: Auto-incrementing (v1, v2, v3...)
- **Active Version**: Only one version active at a time
- **Version History**: View all previous versions
- **Restore**: Activate any previous version with one click
- **Version Notes**: Add context for each version

### Approval Workflow

| State | Description |
|-------|-------------|
| **Draft** | Newly created or edited entries |
| **Approved** | Reviewed and approved for use |
| **Published** | Available to all consumers |

### Enhanced Dictionary (Sections 1 & 2)

#### Table-Level Metadata (`DictionaryAsset`)
- Business semantics (name, definition, domain, grain)
- Ownership (owner, steward)
- Trust & quality (tier, score, approval flags)
- Usage metrics (query counts, last queried)

#### Column-Level Metadata (`DictionaryField`)
- Business semantics (name, definition, entity role)
- Trust & quality (tier, score, approval flags)
- Usage metrics (query counts, filters, group-bys)

#### Trust Tiers
- `certified` - Highest quality, approved for production
- `trusted` - Good quality, suitable for most uses
- `experimental` - New or unverified
- `deprecated` - Should not be used

### Relationship Intelligence

- **Join Intelligence**: Explicit FK tracking with cardinality
- **Confidence Levels**: `declared`, `inferred`, `assumed`
- **Automatic Inference**: Discover FK-like relationships from data patterns
- **Manual Curation**: Create and approve relationships

### Semantic Context

- **Decision Context**: What decisions use this data, frequency, impact
- **Semantic Guarantees**: Invariants, temporal behavior, failure modes
- **Validation State**: Confidence scores, upstream sources, validators
- **Grain Definitions**: Entity type, primary/natural keys, time grain

---

## API Reference

### Core Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/data-dictionary/` | List entries (with filters) |
| `GET` | `/api/v1/data-dictionary/tables/{db}/{schema}/{table}` | Get entries for table |
| `PATCH` | `/api/v1/data-dictionary/{id}` | Update entry |
| `GET` | `/api/v1/data-dictionary/versions/{db}/{schema}/{table}/{column}` | Get version history |
| `POST` | `/api/v1/data-dictionary/activate/{id}` | Activate specific version |

### Enhanced Dictionary Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/data-dictionary/enhanced/sync` | Sync from information_schema |
| `GET` | `/api/v1/data-dictionary/enhanced/assets` | List/search assets |
| `PATCH` | `/api/v1/data-dictionary/enhanced/assets/{id}` | Update asset |
| `GET` | `/api/v1/data-dictionary/enhanced/context/{conn}/{schema}/{table}` | Get full context |

### Relationship Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/data-dictionary/relationships` | List relationships |
| `POST` | `/api/v1/data-dictionary/relationships` | Create relationship |
| `POST` | `/api/v1/data-dictionary/relationships/infer` | Run inference job |

---

## Database Schema

### `data_dictionary_entries` Table

```sql
CREATE TABLE data_dictionary_entries (
    id SERIAL PRIMARY KEY,
    database_name VARCHAR(255) NOT NULL,
    schema_name VARCHAR(255) NOT NULL,
    table_name VARCHAR(255) NOT NULL,
    column_name VARCHAR(255) NOT NULL,
    business_name VARCHAR(255),
    business_description TEXT,
    technical_description TEXT,
    data_type VARCHAR(100),
    examples JSON,
    tags JSON,
    source VARCHAR(50) NOT NULL DEFAULT 'llm_initial',
    version_number INTEGER DEFAULT 1,
    is_active BOOLEAN DEFAULT true,
    version_notes TEXT,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    CONSTRAINT uq_dictionary_entry UNIQUE 
        (database_name, schema_name, table_name, column_name, version_number)
);
```

---

## Integration with Other Features

### Chat/LLM Grounding
```python
context = get_dictionary_context(session, connection_id, schema, table)
# Returns complete context including semantics, grain, relationships
```

### Data Explorer
The Columns tab automatically displays dictionary documentation with:
- Green background for documented columns
- Business descriptions and tags
- Example values

### ML Development
```python
context = get_context_blob(entry_id)
upstream_sources = context.validation_state.upstream_sources
relationships = context.relationships
```

---

## Tag Vocabulary

Common tags generated by AI:

| Tag | Description |
|-----|-------------|
| `PII` | Personally Identifiable Information |
| `metric` | Numeric measurement |
| `identifier` | Unique ID or key |
| `category` | Categorical/enum value |
| `currency` | Monetary value |
| `timestamp` | Date/time field |
| `enumeration` | Fixed set of values |
| `foreign_key` | Reference to another table |
| `free_text` | Unstructured text |

---

## Related Documentation

- [Data Explorer Setup](../setup/DATA_EXPLORER_ENV_SETUP.md)
- [MCP Data Explorer](../mcp-data-explorer.md)
- [API Reference](../api.md)
