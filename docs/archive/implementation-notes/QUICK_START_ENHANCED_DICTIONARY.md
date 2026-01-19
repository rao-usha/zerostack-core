# Enhanced Data Dictionary - Quick Start Guide

## 🚀 Get Started in 5 Minutes

### Step 1: Run Migration (30 seconds)

```bash
docker exec nex-backend-dev alembic upgrade head
```

**Expected**: Creates 5 new tables (dictionary_assets, dictionary_fields, dictionary_relationships, dictionary_profiles, dictionary_usage_logs)

---

### Step 2: Sync Your Database (1 minute)

```bash
curl -X POST http://localhost:8000/api/v1/data-dictionary/enhanced/sync \
  -H "Content-Type: application/json" \
  -d '{"connection_id": "default", "schema": "public"}'
```

**Expected**: `{"tables_synced": N, "columns_synced": M}`

This auto-discovers all your tables and columns!

---

### Step 3: Browse What Was Created (30 seconds)

```bash
# List all assets
curl "http://localhost:8000/api/v1/data-dictionary/enhanced/assets?connection_id=default&limit=5"
```

**You'll see**:
- All your tables as "assets"
- Default business names (prettified table names)
- trust_tier="experimental", trust_score=50
- All structural metadata (schema, table, type)

---

### Step 4: Add Business Meaning (2 minutes)

Pick a table from the list above and update it:

```bash
# Replace {asset_id} with an ID from step 3
curl -X PATCH http://localhost:8000/api/v1/data-dictionary/enhanced/assets/{asset_id} \
  -H "Content-Type: application/json" \
  -d '{
    "business_name": "Customer Orders",
    "business_definition": "Transactional records of customer purchases",
    "business_domain": "Sales",
    "grain": "one row per order",
    "owner": "sales-team@company.com",
    "trust_tier": "trusted",
    "trust_score": 80,
    "approved_for_reporting": true,
    "tags": ["core", "transactional", "revenue"]
  }'
```

---

### Step 5: Get Context for Chat/LLM (1 minute)

```bash
# Replace with your schema.table
curl "http://localhost:8000/api/v1/data-dictionary/enhanced/context/default/public/your_table_name"
```

**You'll get**:
- Table business metadata
- All columns with business definitions
- Relationships (if any)
- Profile stats (if profiled)

**Perfect for grounding LLM prompts!**

---

## 🎯 What You Can Do Now

### ✅ Semantic Search
```bash
curl "http://localhost:8000/api/v1/data-dictionary/enhanced/assets?search=customer&trust_tier=trusted"
```

### ✅ Add Relationships
```bash
curl -X POST http://localhost:8000/api/v1/data-dictionary/enhanced/relationships \
  -H "Content-Type: application/json" \
  -d '{
    "connection_id": "default",
    "source_schema": "public",
    "source_table": "orders",
    "source_column": "customer_id",
    "target_schema": "public",
    "target_table": "customers",
    "target_column": "id",
    "cardinality": "many_to_one",
    "confidence": "declared"
  }'
```

### ✅ Filter by Domain
```bash
curl "http://localhost:8000/api/v1/data-dictionary/enhanced/assets?business_domain=Sales"
```

### ✅ Update Column Metadata
```bash
# Get fields for an asset
curl "http://localhost:8000/api/v1/data-dictionary/enhanced/assets/{asset_id}/fields"

# Update a field
curl -X PATCH http://localhost:8000/api/v1/data-dictionary/enhanced/fields/{field_id} \
  -H "Content-Type: application/json" \
  -d '{
    "business_name": "Customer ID",
    "business_definition": "Unique identifier linking to customers table",
    "entity_role": "foreign_key",
    "trust_tier": "certified",
    "tags": ["identifier", "join_key"]
  }'
```

---

## 📊 Key Concepts

### Trust Tiers
- **certified** - Highest quality, production-approved
- **trusted** - Good quality, suitable for most uses
- **experimental** - New or unverified (default)
- **deprecated** - Should not be used

### Entity Roles
- **primary_identifier** - Primary key
- **foreign_key** - Foreign key
- **measure** - Numeric metric
- **dimension** - Categorical attribute
- **status_flag** - Boolean/enum status
- **timestamp** - Date/time field
- **free_text** - Unstructured text
- **other** - Other/unknown (default)

### Business Domains
Organize tables by business area:
- Sales
- Marketing
- Finance
- Operations
- Identity
- Analytics
- (Your custom domains)

---

## 🔗 Integration Points

### In Data Explorer
When showing table metadata, fetch dictionary context:
```python
dict_ctx = get_dictionary_context(session, conn_id, schema, table)
# Show business_name, definition, trust_tier alongside technical info
```

### In Chat/LLM
Include dictionary context in prompts:
```python
context = get_dictionary_context(session, conn_id, schema, table)
prompt = f"""
Table: {context['table']['business_name']}
Definition: {context['table']['definition']}
Trust: {context['table']['trust_tier']}

Columns:
{format_columns(context['columns'])}
"""
```

### In MCP Tools
Add dictionary enrichment to tool outputs:
```python
# When returning table metadata
metadata = {
    "technical": get_table_info(schema, table),
    "business": get_dictionary_context(session, conn_id, schema, table)
}
```

---

## 📝 Next Steps

### Immediate (You can do now)
1. ✅ Sync all your schemas
2. ✅ Add business metadata to key tables
3. ✅ Document important columns
4. ✅ Add relationships between tables
5. ✅ Use context endpoint in chat

### Coming Soon (Needs implementation)
1. ⏳ **Profiling Service** - Auto-compute column stats
2. ⏳ **Usage Tracking** - Log which tables/columns are queried
3. ⏳ **MCP Integration** - Enrich tool outputs
4. ⏳ **UI** - Browse and edit in frontend

---

## 🆘 Troubleshooting

### Migration fails
```bash
# Check current version
docker exec nex-backend-dev alembic current

# If stuck, check migration history
docker exec nex-backend-dev alembic history
```

### Sync returns 0 tables
- Check connection_id is correct ("default" by default)
- Verify schema name ("public" is common)
- Check database connection is working

### Can't find asset_id
```bash
# List all assets to get IDs
curl "http://localhost:8000/api/v1/data-dictionary/enhanced/assets?connection_id=default"
```

### Context endpoint returns 404
- Make sure you've run sync first
- Check schema.table exists in your database
- Verify connection_id is correct

---

## 📚 Full Documentation

See `ENHANCED_DICTIONARY_COMPLETE.md` for:
- Complete API reference
- All endpoints with examples
- Design decisions explained
- Future roadmap
- Testing checklist

---

## ✨ Key Benefits

**For Data Teams**:
- 📖 Document once, use everywhere
- 🔍 Searchable business glossary
- 🤝 Shared understanding of data
- ✅ Trust indicators guide usage

**For AI/Chat**:
- 🎯 Accurate context for LLMs
- 🧠 Business meaning, not just schema
- 🔗 Relationship awareness
- 📊 Quality indicators

**For Governance**:
- 👥 Clear ownership
- 🏷️ Consistent tagging
- 📈 Usage tracking (coming soon)
- 🔒 Approval workflows

---

**You're all set!** 🎉

Start with Step 1 above and you'll have a working enhanced data dictionary in 5 minutes.


