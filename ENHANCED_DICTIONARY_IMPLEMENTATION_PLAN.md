

# Enhanced Data Dictionary Implementation Plan

## Overview
Extending the existing data dictionary system with:
1. **Core Enhancements**: Semantic meaning, relationships, usage signals
2. **Data Quality & Trust**: Profiling, trust tiers, quality metrics

## Current Status
✅ **Models Created** (`dictionary_enhanced_models.py`):
- `DictionaryAsset` - Table-level metadata
- `DictionaryField` - Column-level metadata
- `DictionaryRelationship` - Join intelligence
- `DictionaryProfile` - Profiling snapshots (append-only)
- `DictionaryUsageLog` - Usage tracking

✅ **Migration Created** (`011_add_enhanced_dictionary.py`):
- All 5 tables with proper indexes and constraints
- Ready to run: `alembic upgrade head`

✅ **Service Layer Created** (`dictionary_enhanced_service.py`):
- `sync_assets_from_information_schema()` - Introspection sync
- CRUD operations for assets, fields, relationships
- Profile querying (latest, historical)
- Usage logging and aggregation
- `get_dictionary_context()` - LLM grounding helper

## Next Steps

### 1. API Router (`dictionary_enhanced_router.py`)
**Status**: IN PROGRESS

Endpoints to implement:
- `POST /api/v1/data-dictionary/sync` - Introspection sync
- `GET /api/v1/data-dictionary/assets` - List/search assets
- `GET /api/v1/data-dictionary/assets/{id}` - Get single asset
- `PATCH /api/v1/data-dictionary/assets/{id}` - Update asset metadata
- `GET /api/v1/data-dictionary/assets/{id}/fields` - Get asset fields
- `PATCH /api/v1/data-dictionary/fields/{id}` - Update field metadata
- `GET /api/v1/data-dictionary/relationships` - List relationships
- `POST /api/v1/data-dictionary/relationships` - Create relationship
- `DELETE /api/v1/data-dictionary/relationships/{id}` - Delete relationship
- `GET /api/v1/data-dictionary/profiles` - Get profiles
- `POST /api/v1/data-dictionary/profile/run` - Trigger profiling job

### 2. Profiling Service (`dictionary_profiling_service.py`)
**Status**: NOT STARTED

Functions to implement:
- `profile_column()` - Profile a single column with safety limits
- `profile_table()` - Profile all columns in a table
- `profile_schema()` - Profile entire schema with throttling
- Safety mechanisms:
  - TABLESAMPLE for large tables
  - Statement timeouts
  - Row limits
  - Concurrent connection limits

### 3. Usage Tracking Integration
**Status**: NOT STARTED

Modify existing query execution:
- `backend/domains/data_explorer/service.py` - Add usage logging
- Parse SQL to extract tables/columns
- Call `log_usage_event()` after successful queries
- Background job to aggregate stats

### 4. MCP Tool Enhancement
**Status**: NOT STARTED

Update MCP tool outputs to include dictionary enrichment:
- Add optional `include_dictionary=true` parameter
- Return business_name, definitions, trust_tier with metadata
- Use `get_dictionary_context()` for chat grounding

### 5. Frontend Integration (Optional)
**Status**: NOT STARTED

Add UI sections:
- Asset browser with trust tier filters
- Relationship visualizer
- Profile viewer with charts
- Usage dashboard

## Design Decisions

### 1. Coexistence with Existing System
**Decision**: Keep `data_dictionary_entries` table, add complementary tables

**Rationale**:
- Existing table has versioning that works well
- New tables provide richer semantics without breaking current features
- Future: Can migrate/merge if needed

### 2. Profile Storage Strategy
**Decision**: Append-only snapshots

**Rationale**:
- Track quality changes over time
- Support "profile drift" detection
- Query latest with `ORDER BY computed_at DESC LIMIT 1`
- Cleanup old profiles with retention policy

### 3. Usage Tracking
**Decision**: Two-tier approach

**Tier 1**: Detailed logs in `dictionary_usage_logs`
- Raw events with full query text
- Retention: 30-90 days
- Used for analysis and aggregation

**Tier 2**: Aggregated counters in `dictionary_assets` and `dictionary_fields`
- Rolling 30-day counts
- Updated by background job
- Fast for UI display

### 4. Trust Scoring
**Decision**: Start simple, evolve

**Initial Rules**:
- New assets: `trust_tier=experimental`, `trust_score=50`
- Boost score based on:
  - Has business definition (+10)
  - Has recent profile (+10)
  - Low null fraction (+10)
  - High usage (+10)
  - Manual approval (+20)
- Lower score for:
  - Known issues (-20)
  - No recent usage (-10)
  - High null fraction (-10)

**Future**: ML-based scoring

### 5. Profiling Safety
**Decision**: Conservative by default

**Limits**:
- Default sample: 10,000 rows or 10% of table
- Use TABLESAMPLE BERNOULLI for large tables (>100k rows)
- Statement timeout: 30 seconds per column
- Concurrent limit: 5 tables at once
- Skip profiling if table >10M rows (unless forced)

**Overrides**: Allow admin to force full profiling

## Migration Path

### Phase 1: Foundation (Current)
- [x] Create models
- [x] Create migration
- [x] Create service layer
- [ ] Create API router
- [ ] Run migration
- [ ] Test basic CRUD

### Phase 2: Profiling
- [ ] Implement profiling service
- [ ] Add profiling endpoint
- [ ] Test on small tables
- [ ] Add background scheduler

### Phase 3: Usage Tracking
- [ ] Add logging to query execution
- [ ] Implement aggregation job
- [ ] Test usage counters

### Phase 4: Integration
- [ ] Update MCP tools
- [ ] Add dictionary context to chat
- [ ] Test end-to-end

### Phase 5: UI (Optional)
- [ ] Asset browser page
- [ ] Profile viewer
- [ ] Relationship visualizer

## File Structure

```
backend/
├── domains/
│   └── data_explorer/
│       ├── dictionary_enhanced_models.py      ✅ Done
│       ├── dictionary_enhanced_service.py     ✅ Done
│       ├── dictionary_enhanced_router.py      🔄 Next
│       ├── dictionary_profiling_service.py    ⏳ TODO
│       └── dictionary_usage_service.py        ⏳ TODO
├── migrations/
│   └── versions/
│       └── 011_add_enhanced_dictionary.py     ✅ Done
```

## API Examples

### Sync Assets
```bash
POST /api/v1/data-dictionary/sync
{
  "connection_id": "default",
  "schema": "public"
}

Response:
{
  "tables_synced": 25,
  "columns_synced": 150
}
```

### Search Assets
```bash
GET /api/v1/data-dictionary/assets?connection_id=default&search=user&trust_tier=trusted&limit=10

Response:
{
  "results": [
    {
      "id": "uuid",
      "schema_name": "public",
      "table_name": "users",
      "business_name": "User Accounts",
      "business_definition": "Core user account information",
      "trust_tier": "trusted",
      "trust_score": 85,
      "query_count_30d": 1250
    }
  ],
  "total": 3,
  "limit": 10,
  "offset": 0
}
```

### Get Dictionary Context for Chat
```bash
GET /api/v1/data-dictionary/context/default/public/users

Response:
{
  "table": {
    "name": "public.users",
    "business_name": "User Accounts",
    "definition": "...",
    "trust_tier": "trusted",
    "trust_score": 85
  },
  "columns": [
    {
      "name": "user_id",
      "business_name": "User ID",
      "role": "primary_identifier",
      "profile": {
        "null_fraction": 0.0,
        "distinct_count": 10000
      }
    }
  ],
  "relationships": [
    {
      "direction": "outgoing",
      "from": "public.users.user_id",
      "to": "public.orders.user_id",
      "cardinality": "one_to_many"
    }
  ]
}
```

### Trigger Profiling
```bash
POST /api/v1/data-dictionary/profile/run
{
  "connection_id": "default",
  "schema": "public",
  "table": "users",
  "sample_size": 10000
}

Response:
{
  "status": "started",
  "job_id": "uuid",
  "estimated_duration": "30s"
}
```

## Testing Checklist

### Unit Tests
- [ ] Model creation and validation
- [ ] Service layer functions
- [ ] Profile computation logic
- [ ] Usage aggregation logic

### Integration Tests
- [ ] Sync from information_schema
- [ ] API CRUD operations
- [ ] Profiling with real data
- [ ] Usage logging and aggregation

### End-to-End Tests
- [ ] Sync → Profile → Query → Aggregate
- [ ] Dictionary context in chat
- [ ] MCP tool enrichment

## Performance Considerations

### Indexes
- All foreign keys indexed
- Composite indexes for common queries
- Partial indexes for filtered queries (e.g., `WHERE trust_tier='certified'`)

### Query Optimization
- Use CTEs for complex aggregations
- Limit result sets with pagination
- Cache frequently accessed data (Redis optional)

### Profiling Performance
- Use sampling for large tables
- Parallel profiling with connection pooling
- Skip profiling for very large tables by default

### Usage Logging
- Async logging (don't block queries)
- Batch inserts
- Regular cleanup of old logs

## Security Considerations

- **Read-only operations**: Profiling and usage tracking never modify source data
- **Connection isolation**: Respect existing connection permissions
- **Rate limiting**: Profiling and sync endpoints need rate limits
- **User authentication**: Inherit from existing auth system

## Documentation

### User Docs
- [ ] How to sync assets
- [ ] How to add business metadata
- [ ] How to create relationships
- [ ] How to trigger profiling
- [ ] Understanding trust tiers

### Developer Docs
- [ ] API reference
- [ ] Model schemas
- [ ] Profiling algorithm details
- [ ] Usage tracking implementation

### Admin Docs
- [ ] Migration guide
- [ ] Configuration options
- [ ] Monitoring and maintenance
- [ ] Performance tuning

## Next Immediate Steps

1. **Complete API Router** (30 min)
2. **Run Migration** (2 min)
3. **Test Basic CRUD** (15 min)
4. **Implement Profiling Service** (1 hour)
5. **Add Profiling Endpoint** (15 min)
6. **Test Profiling** (30 min)

**Total Estimate**: ~2.5 hours for MVP

## Long-term Roadmap

### Q1 2025
- ✅ Core models and CRUD
- ⏳ Profiling service
- ⏳ Usage tracking
- ⏳ MCP integration

### Q2 2025
- Relationship inference from FK constraints
- Relationship inference from data patterns
- Advanced trust scoring (ML-based)
- UI for asset browsing

### Q3 2025
- Lineage tracking
- Impact analysis
- Automated tagging
- Anomaly detection

### Q4 2025
- Recommendation engine
- Auto-documentation
- Semantic search
- Knowledge graph visualization



