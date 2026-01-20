# ZeroStack Demo

> Make jaws drop in 30 seconds. Tell a story in 5 minutes.

---

## The 30-Second "Holy Shit" Moment

Open the chat. Type this:

> "I just joined this company. Explain the data model to me like I'm new."

Watch it:
1. Scan your entire database
2. Identify tables, relationships, and patterns
3. Explain the business domain in plain English
4. Suggest where to start exploring

**That's it.** One sentence, and the AI understands your whole database.

Follow up with:
> "Which tables have data quality issues I should know about?"

---

## The 5-Minute Story Demo

### Setup: The Scenario

*"You're a data engineer. Day 1 at a new company. You inherit a database with 50+ tables. No documentation. The last person who understood it left 6 months ago. What do you do?"*

### Act 1: Explore (1 min)

**Open Data Explorer** → `localhost:3000/explorer`

1. Click through schemas - *"Here's everything in the database"*
2. Click a table → **Profile** - *"Instant statistics without writing SQL"*
3. Click **Sample** - *"Preview data safely, read-only"*

*"In 60 seconds, you've seen more than most people learn in a week."*

### Act 2: Understand (2 min)

**Open Chat** → `localhost:3000/chat`

Ask:
> "What are the most important tables and how do they relate?"

Then:
> "Show me a query to find the top 10 customers by lifetime value"

Then:
> "What does the order_status column mean? What are the valid values?"

*"You're having a conversation with your database. No docs needed."*

### Act 3: Document (1.5 min)

**Open Data Analysis** → `localhost:3000/analysis`

1. Select 5 tables
2. Choose "Column Documentation"
3. Pick Claude or GPT
4. Click **Create Job**

*"Watch this..."*

**Open Data Dictionary** → `localhost:3000/dictionary`

Show the AI-generated documentation:
- Business names (not just `cust_id` but "Customer ID")
- Plain English descriptions
- PII detection (email, phone flagged automatically)
- Trust tiers assigned

*"What used to take weeks of interviews and documentation... done in 30 seconds. And it's editable - AI proposes, humans approve."*

### Act 4: The Kicker (30 sec)

*"But here's the real magic..."*

Open Claude Desktop. Show MCP integration.

> "Using ZeroStack, show me tables with more than 10% null values"

Claude calls your MCP server, queries your database, returns results.

*"Your database is now a tool that any AI can use."*

---

## One-Liner Demos

For quick feature showcases:

### Chat understands context
```
"What would break if I deleted the customers table?"
```

### Lineage in one question
```
"Where does the revenue column in the dashboard come from?"
```

### Quality check
```
"Are there any columns that are mostly null?"
```

### Relationship discovery
```
"How do I join orders to products?"
```

### Business translation
```
"Explain the billing tables to someone in finance, not engineering"
```

---

## Demo Data Setup

Before demoing, seed compelling data:

```bash
cd backend
python scripts/seed_demo_data.py
```

This creates:
- **E-commerce schema**: customers, orders, products, reviews
- **Realistic volume**: 10K customers, 50K orders
- **Data quality issues**: Some nulls, duplicates, format problems (intentional)
- **Pre-generated documentation**: So dictionary isn't empty

---

## URLs

| What | Where |
|------|-------|
| Dashboard | http://localhost:3000 |
| Data Explorer | http://localhost:3000/explorer |
| Chat | http://localhost:3000/chat |
| Data Dictionary | http://localhost:3000/dictionary |
| ML Workbench | http://localhost:3000/ml-workbench |
| API Docs | http://localhost:8000/docs |

---

## If You Only Have 60 Seconds

1. Open Chat
2. Type: *"Explain this database to me"*
3. Wait 5 seconds
4. Read the response out loud
5. Say: *"That took 5 seconds. The last data engineer took 3 months to figure this out."*

---

## What NOT To Do

- ❌ Don't show curl commands (boring, no visual impact)
- ❌ Don't list features (it's not a spec sheet)
- ❌ Don't say "it can do X" - just do X
- ❌ Don't use empty databases
- ❌ Don't apologize for rough edges - own it

---

## Backup: API Commands (If UI Breaks)

<details>
<summary>Click to expand</summary>

```bash
# Chat
curl -X POST http://localhost:8000/api/v1/chat/message \
  -H "Content-Type: application/json" \
  -d '{"message": "Explain the data model"}'

# List tables
curl http://localhost:8000/api/v1/data-explorer/schemas/public/tables

# Profile a table
curl http://localhost:8000/api/v1/data-explorer/schemas/public/tables/orders/profile

# Get documentation
curl http://localhost:8000/api/v1/data-dictionary/enhanced/assets

# Quality check
curl http://localhost:8000/api/v1/quality/assess/public.orders
```

</details>

---

## The Pitch (If Asked)

*"ZeroStack is what happens when you give an AI full access to understand your data. Not query it - understand it. Every table, every column, every relationship. Then you just... ask questions."*

*"It's like having a senior data engineer who's been at the company for 10 years, available 24/7, for every database you have."*
