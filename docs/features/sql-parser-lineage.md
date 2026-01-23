# SQL Parser & Automatic Lineage Tracking

## Overview

The SQL Parser feature automatically extracts data lineage from SQL queries executed in the Data Explorer. It parses SELECT, INSERT, and CREATE TABLE queries to identify source tables, transformations, and data flows without any manual tracking required.

## Key Features

### 1. **Automatic Source Table Detection**
- Detects all tables referenced in FROM and JOIN clauses
- Handles schema-qualified names (e.g., `schema.table`)
- Tracks table aliases
- Supports subqueries and nested SELECT statements

### 2. **Transformation Detection**
- **JOIN Types**: INNER, LEFT, RIGHT, FULL, CROSS
- **Aggregations**: SUM, AVG, COUNT, MIN, MAX, GROUP BY
- **Filters**: WHERE clause detection
- **Column Usage**: Tracks which columns are used in SELECT

### 3. **Write Operation Tracking**
- **INSERT INTO ... SELECT**: Detects target and source tables
- **CREATE TABLE AS SELECT**: Tracks new table creation and sources
- Automatically creates lineage edges for write operations

## Technical Architecture

### Backend Components

```
backend/domains/lineage/
├── sql_parser.py          # Core SQL parsing logic
├── auto_tracker.py        # Lineage tracking integration
├── service.py             # Lineage storage and querying
├── models.py              # Data models for lineage
└── router.py              # API endpoints
```

#### sql_parser.py
- **SQLLineageParser**: Main parser class using `sqlparse` library
- **TableReference**: Represents a table (schema, name, alias)
- **ColumnReference**: Represents a column (table, name)
- **QueryLineage**: Parsed lineage information

#### auto_tracker.py
- **AutoLineageTracker**: Integrates parser with lineage service
- `track_query_execution()`: Records lineage after query execution
- `parse_query_preview()`: Parses SQL without recording (for preview)

### API Endpoints

#### Parse SQL (Preview)
```http
POST /api/v1/lineage/parse-sql
Content-Type: application/json

{
  "sql": "SELECT * FROM sales JOIN customers ON sales.customer_id = customers.id"
}
```

**Response:**
```json
{
  "success": true,
  "lineage": {
    "query_type": "SELECT",
    "source_tables": [
      {
        "schema": null,
        "table": "sales",
        "alias": null,
        "full_name": "sales"
      },
      {
        "schema": null,
        "table": "customers",
        "alias": null,
        "full_name": "customers"
      }
    ],
    "transformations": {
      "join_type": "INNER",
      "has_aggregation": false,
      "has_filter": false
    },
    "columns_used": [...]
  }
}
```

#### Track Query Execution
```http
POST /api/v1/lineage/track-query
Content-Type: application/json

{
  "sql": "SELECT date, SUM(amount) FROM sales GROUP BY date",
  "result_dataset_name": "daily_sales_summary",
  "result_row_count": 365,
  "execution_time_ms": 45.2
}
```

**Response:**
```json
{
  "success": true,
  "query_type": "SELECT",
  "source_tables": ["sales"],
  "edges_created": [
    {
      "edge_id": "uuid-here",
      "source": "sales",
      "target": "daily_sales_summary",
      "edge_type": "AGGREGATED"
    }
  ],
  "has_aggregation": true
}
```

### Data Explorer Integration

The SQL parser is automatically integrated with Data Explorer's query execution. When you run a query:

1. Query is executed and results returned
2. SQL is parsed to extract lineage
3. Lineage info is added to response (without saving)
4. Frontend displays lineage preview below query results

**In DataExplorer.tsx:**
```typescript
const queryResponse = await executeExplorerQuery(sql, page, pageSize, selectedDbId);

// lineage_info is automatically included in response
if (queryResponse.lineage_info) {
  // Display lineage preview
  <QueryLineageView lineageInfo={queryResponse.lineage_info} />
}
```

## Frontend Components

### QueryLineageView Component
`frontend/src/components/QueryLineageView.tsx`

**Props:**
- `lineageInfo`: QueryLineageInfo object from API
- `compact`: Boolean for compact single-line view

**Features:**
- **Compact View**: Single line showing "Sources: table1, table2 (INNER JOIN, AGGREGATE)"
- **Full View**: Detailed breakdown with:
  - Source tables as pills
  - Target table (for INSERT/CREATE)
  - Transformation badges (JOIN, AGGREGATE, FILTER)
  - Columns used (first 10 shown)
  - Simple data flow diagram

**Example Usage:**
```tsx
// Compact view above query results
<QueryLineageView lineageInfo={lineageInfo} compact={true} />

// Full view in a dedicated section
<QueryLineageView lineageInfo={lineageInfo} compact={false} />
```

## Supported SQL Patterns

### ✅ Fully Supported

1. **Simple SELECT**
   ```sql
   SELECT * FROM sales WHERE amount > 100
   ```

2. **INNER JOIN**
   ```sql
   SELECT s.*, c.name 
   FROM sales s 
   INNER JOIN customers c ON s.customer_id = c.id
   ```

3. **LEFT/RIGHT/FULL JOIN**
   ```sql
   SELECT * 
   FROM customers c 
   LEFT JOIN sales s ON c.id = s.customer_id
   ```

4. **Multi-table JOIN**
   ```sql
   SELECT p.name, c.category, SUM(s.amount)
   FROM sales s
   JOIN products p ON s.product_id = p.id
   JOIN categories c ON p.category_id = c.id
   GROUP BY p.name, c.category
   ```

5. **Schema-qualified tables**
   ```sql
   SELECT * 
   FROM prod_schema.orders o
   JOIN staging_schema.customers c ON o.customer_id = c.id
   ```

6. **Aggregation**
   ```sql
   SELECT category, COUNT(*), AVG(price)
   FROM products
   GROUP BY category
   ```

7. **INSERT INTO SELECT**
   ```sql
   INSERT INTO summary (date, total)
   SELECT DATE(created_at), SUM(amount)
   FROM sales
   GROUP BY DATE(created_at)
   ```

8. **CREATE TABLE AS SELECT**
   ```sql
   CREATE TABLE high_value_customers AS
   SELECT customer_id, SUM(amount) as total_spend
   FROM sales
   GROUP BY customer_id
   HAVING SUM(amount) > 10000
   ```

9. **Subqueries**
   ```sql
   SELECT *
   FROM (
     SELECT customer_id, SUM(amount) as total
     FROM sales
     GROUP BY customer_id
   ) customer_totals
   WHERE total > 5000
   ```

10. **UNION**
    ```sql
    SELECT 'sales' as source, COUNT(*) FROM sales
    UNION ALL
    SELECT 'returns' as source, COUNT(*) FROM returns
    ```

### ⚠️ Partial Support

1. **CTEs (WITH clauses)** - Detected but not fully parsed yet
   ```sql
   WITH monthly_sales AS (
     SELECT DATE_TRUNC('month', date) as month, SUM(amount) as total
     FROM sales
     GROUP BY month
   )
   SELECT * FROM monthly_sales WHERE total > 10000
   ```

2. **Window Functions** - Detected as aggregation
   ```sql
   SELECT customer_id, amount,
          ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY date) as rn
   FROM sales
   ```

### ❌ Not Supported (MVP)

1. **Complex nested subqueries** - May miss some tables
2. **Dynamic SQL / EXECUTE statements**
3. **PL/pgSQL functions**
4. **Foreign table references**

## Configuration

No configuration required! The SQL parser works out of the box.

**Optional:** Disable automatic lineage tracking for a specific query:

```http
POST /api/v1/data-explorer/query?track_lineage=false
```

## Performance Considerations

- **Parsing Overhead**: ~1-5ms per query (negligible)
- **No Database Impact**: All parsing happens in Python, no extra DB queries
- **Memory**: Lightweight - only stores extracted metadata

## Testing

### Backend Test Suite
```bash
cd backend/domains/lineage
python test_sql_parser.py
```

Runs 10+ test cases covering:
- Simple SELECT
- Various JOIN types
- Aggregation queries
- INSERT and CREATE TABLE
- Subqueries and UNION

### Example Test Output
```
1. Simple SELECT
✓ Query Type: SELECT
✓ Source Tables:
  - sales
✓ Transformations:
  - FILTER: Yes (WHERE clause)

2. INNER JOIN
✓ Query Type: SELECT
✓ Source Tables:
  - sales (alias: s)
  - customers (alias: c)
✓ Transformations:
  - JOIN: INNER
```

## Future Enhancements

### Planned (Phase 2)
1. **Full CTE Support** - Parse WITH clauses recursively
2. **Column-Level Lineage** - Track column transformations (e.g., `sales.amount -> summary.total_amount`)
3. **Function Detection** - Identify UDFs and built-in functions used
4. **Query Optimization Hints** - Suggest indexes based on lineage patterns

### Planned (Phase 3)
1. **Cross-Query Lineage** - Connect queries that share intermediate tables
2. **ML Model Training Data Tracking** - Detect queries used for ML feature extraction
3. **Data Quality Rules** - Infer data quality constraints from WHERE clauses
4. **Impact Analysis** - "What breaks if I drop this table?"

## Troubleshooting

### Parser Fails to Detect Tables
**Issue:** Source tables not showing up in lineage

**Solutions:**
1. Check query syntax - must be valid SQL
2. Ensure tables are in FROM or JOIN clauses (not in comments)
3. Verify schema names don't have special characters

### Lineage Not Appearing in Data Explorer
**Issue:** Query executes but no lineage shown

**Solutions:**
1. Check that `track_lineage=true` in query params (default)
2. Verify lineage service is running (no errors in backend logs)
3. Try calling `/api/v1/lineage/parse-sql` directly to test parser

### Performance Issues
**Issue:** Queries slow after enabling lineage

**Solutions:**
1. Lineage adds <5ms - check query itself is optimized
2. Disable lineage for specific queries if needed (`track_lineage=false`)
3. Check backend logs for lineage service errors

## Examples

### Example 1: Data Explorer Query with Lineage

**Query:**
```sql
SELECT 
  c.segment,
  COUNT(DISTINCT c.id) as customer_count,
  SUM(s.amount) as total_sales,
  AVG(s.amount) as avg_order_value
FROM customers c
LEFT JOIN sales s ON c.id = s.customer_id
WHERE s.date >= '2024-01-01'
GROUP BY c.segment
ORDER BY total_sales DESC
```

**Lineage Output:**
```
📊 Lineage: customers, sales
Transformations: LEFT JOIN, AGGREGATE, FILTER
```

**Full View Shows:**
- Source Tables: `customers` (c), `sales` (s)
- Transformations: LEFT JOIN, AGGREGATE, FILTER
- Columns: c.segment, c.id, s.amount, s.date, s.customer_id
- Flow: customers + sales → Result

### Example 2: Tracking a Data Pipeline Query

**Query:**
```sql
INSERT INTO daily_summaries (date, revenue, order_count, customer_count)
SELECT 
  DATE(created_at) as date,
  SUM(amount) as revenue,
  COUNT(*) as order_count,
  COUNT(DISTINCT customer_id) as customer_count
FROM sales
WHERE status = 'completed'
GROUP BY DATE(created_at)
```

**Tracking:**
```javascript
const result = await fetch('/api/v1/lineage/track-query', {
  method: 'POST',
  body: JSON.stringify({
    sql: query,
    result_dataset_name: 'daily_summaries',
    result_row_count: 365,
    execution_time_ms: 123.4
  })
});
```

**Result:**
- Creates lineage edge: `sales` → `daily_summaries`
- Edge type: `AGGREGATED` (because of SUM/COUNT/GROUP BY)
- Stores transformation SQL for future reference
- Now visible in lineage graph for both tables

## API Reference Summary

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/lineage/parse-sql` | POST | Preview lineage without tracking |
| `/api/v1/lineage/track-query` | POST | Track lineage from executed query |
| `/api/v1/data-explorer/query` | POST | Execute query (auto-tracks lineage) |

## Related Documentation

- [Data Lineage Overview](./data-lineage.md)
- [Data Explorer Guide](../../backend/DATA_EXPLORER.md)
- [Lineage API Reference](../../backend/domains/lineage/README.md)

---

**Last Updated:** 2026-01-16  
**Version:** 1.0.0 (MVP)  
**Status:** ✅ Production Ready
