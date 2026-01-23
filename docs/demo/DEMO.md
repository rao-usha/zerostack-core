# NEX.AI Demo Guide

> Make jaws drop in 30 seconds. Tell a story in 5 minutes.

---

## Quick Start (Docker)

### 1. Start Everything

```bash
docker-compose up -d
```

Wait for all containers to be healthy (check with `docker-compose ps`).

### 2. Seed Demo Data

```bash
docker-compose exec backend python scripts/seed_demo_data.py
```

You should see:
```
==================================================
DEMO DATA SUMMARY
==================================================
  Customers                   500
  Products                     48
  Orders                    2,000
  Order Items               6,000+
  Customer Segments           500
  Sales Summary             2,900+
  Total Revenue        $2,400,000+
==================================================
```

### 3. Configure API Key

1. Open http://localhost:3000/settings
2. Click **"LLM"** category
3. Enter your **OPENAI_API_KEY** or **ANTHROPIC_API_KEY**
4. Click **Save**, then **Test** to verify

### 4. Verify Demo Works

1. Go to http://localhost:3000/explorer
2. Select **"demo"** from the schema dropdown
3. You should see tables: `customers`, `orders`, `products`, etc.

---

## The 30-Second Demo

1. Open http://localhost:3000/chat
2. Type: `Look at the demo schema and explain the data model to me like I'm new.`
3. Press Enter

**That's it.** The AI understands your entire database from one sentence.

---

## The 5-Minute Story Demo

### The Scenario

*"You're a data engineer. Day 1 at a new company. You inherit a database with dozens of tables. No documentation. What do you do?"*

### Act 1: Explore (1 min)

1. Go to http://localhost:3000/explorer
2. Select **"demo"** schema
3. Click **"customers"** table
4. Run: `SELECT * FROM demo.customers ORDER BY lifetime_value DESC LIMIT 10`

### Act 2: Chat (2 min)

1. Go to http://localhost:3000/chat
2. Ask: `What are the most important tables and how do they relate?`
3. Ask: `Write a query for customers who haven't ordered in 90 days but have high lifetime value`

### Act 3: AI Analysis (1 min)

1. Go to http://localhost:3000/analysis
2. Select tables: `demo.customers`, `demo.orders`
3. Choose **"Column Documentation"**
4. Click **Run Analysis**
5. View results at http://localhost:3000/dictionary

### Act 4: ML Query (30 sec)

Run in Explorer:
```sql
SELECT c.customer_id, c.first_name,
       COUNT(o.order_id) as orders,
       SUM(o.total_amount) as total_spent,
       cs.churn_risk
FROM demo.customers c
JOIN demo.orders o ON c.customer_id = o.customer_id
JOIN demo.customer_segments cs ON c.customer_id = cs.customer_id
WHERE cs.churn_risk > 0.5
GROUP BY c.customer_id, c.first_name, cs.churn_risk
ORDER BY total_spent DESC LIMIT 20
```

---

## Demo URLs

| Page | URL |
|------|-----|
| Dashboard | http://localhost:3000 |
| Data Explorer | http://localhost:3000/explorer |
| Chat | http://localhost:3000/chat |
| Dictionary | http://localhost:3000/dictionary |
| Analysis | http://localhost:3000/analysis |
| Settings | http://localhost:3000/settings |
| API Docs | http://localhost:8000/docs |

---

## Quick Queries

```sql
-- Top customers
SELECT first_name, last_name, lifetime_value
FROM demo.customers ORDER BY lifetime_value DESC LIMIT 10;

-- Churn risk
SELECT c.first_name, c.lifetime_value, cs.churn_risk
FROM demo.customers c
JOIN demo.customer_segments cs ON c.customer_id = cs.customer_id
WHERE cs.churn_risk > 0.7;

-- Revenue by country
SELECT country_code, SUM(total_revenue) as revenue
FROM demo.sales_summary GROUP BY country_code ORDER BY revenue DESC;
```

---

## Troubleshooting

### No tables / No demo schema
```bash
docker-compose exec backend python scripts/seed_demo_data.py
```
Then select "demo" schema in Explorer (not "public").

### API errors / Chat not working
1. Go to Settings > LLM
2. Enter and save your API key
3. Click Test - should show green

### Health check fails
```bash
docker-compose logs backend
docker-compose logs frontend
```

### Rebuild after code changes
```bash
docker-compose up -d --build
```

---

## The Pitch

*"NEX.AI is what happens when you give an AI full access to understand your data. Not just query it - understand it. Every table, every column, every relationship. Then you just... ask questions."*
