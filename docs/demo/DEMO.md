# ZeroStack Demo Guide

> Make jaws drop in 30 seconds. Tell a story in 5 minutes.

---

## Prerequisites

Before running the demo, ensure you have:
- PostgreSQL running (local or Docker)
- Node.js 18+ installed
- Python 3.10+ installed
- API keys configured (at minimum: OpenAI or Anthropic)

---

## Quick Start (5 minutes to demo-ready)

### Step 1: Start the Database

If using Docker:
```bash
docker run -d --name nex-postgres \
  -e POSTGRES_USER=nex \
  -e POSTGRES_PASSWORD=nex \
  -e POSTGRES_DB=nex \
  -p 5432:5432 \
  postgres:15
```

Or ensure your local PostgreSQL is running.

### Step 2: Configure Environment

Create/edit `.env` in the project root:
```bash
# Required
DATABASE_URL=postgresql+psycopg://nex:nex@localhost:5432/nex
ENCRYPTION_KEY=<your-key>  # Generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# At least one LLM provider
OPENAI_API_KEY=sk-...
# Or
ANTHROPIC_API_KEY=sk-ant-...
```

### Step 3: Seed Demo Data

```bash
cd backend
pip install -r requirements-core.txt  # If not already installed
python scripts/seed_demo_data.py
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

### Step 4: Start the Backend

```bash
cd backend
uvicorn main:app --reload --port 8000
```

Wait for: `Uvicorn running on http://0.0.0.0:8000`

### Step 5: Start the Frontend

Open a new terminal:
```bash
cd frontend
npm install  # If not already installed
npm run dev
```

Wait for: `Local: http://localhost:3000/`

### Step 6: Verify It Works

Open http://localhost:3000 - you should see the ZeroStack dashboard.

---

## The 30-Second "Holy Shit" Moment

### Step-by-Step UI Walkthrough

1. **Open your browser** and go to: http://localhost:3000/chat

2. **You'll see the Chat page:**
   - Left side: Navigation sidebar with icons (Dashboard, Explorer, Chat, etc.)
   - Center: Large chat input area with a text box at the bottom
   - The page title says "Chat" at the top

3. **Find the message input:**
   - At the bottom of the screen, there's a text input field
   - It may say "Type a message..." or similar placeholder text

4. **Type your message:**
   ```
   I just joined this company. Look at the demo schema and explain the data model to me like I'm new.
   ```

5. **Send the message:**
   - Press **Enter** on your keyboard, OR
   - Click the **Send button** (arrow icon) to the right of the input field

6. **Watch the response appear:**
   - The AI response streams in the chat area above the input
   - You'll see it describe tables like `customers`, `orders`, `products`
   - It explains relationships and business context

7. **Follow up** by typing:
   ```
   Which customers have the highest churn risk?
   ```

**That's it.** One sentence, and the AI understands your whole database.

---

## The 5-Minute Story Demo

### The Scenario

*"You're a data engineer. Day 1 at a new company. You inherit a database with dozens of tables. No documentation. The last person who understood it left 6 months ago. What do you do?"*

### Act 1: Explore the Database (1 min)

**Navigate to Data Explorer:**

1. **Click "Explorer"** in the left sidebar (database icon)
   - Or go directly to: http://localhost:3000/explorer

2. **You'll see the Data Explorer page:**
   - Top section: Schema selector dropdown + table list
   - Bottom section: SQL editor + results area

3. **Select the demo schema:**
   - Look for a **dropdown menu** near the top-left that shows schemas
   - Click it and select **"demo"** from the list
   - The table list will refresh to show demo tables

4. **Browse the tables:**
   - You'll see a list of tables: `customers`, `orders`, `products`, `order_items`, `customer_segments`, `sales_summary`
   - **Click on "customers"** in the table list
   - A preview of the table data appears automatically below

5. **Run a custom SQL query:**
   - Find the **SQL Editor** text area (usually in the middle/bottom section)
   - Clear any existing text and type:
     ```sql
     SELECT * FROM demo.customers ORDER BY lifetime_value DESC LIMIT 10
     ```
   - Click the **"Run Query"** or **"Execute"** button (usually blue, top-right of the SQL editor)
   - Results appear in a table below the editor

*"In 60 seconds, you've seen more than most people learn in a week."*

### Act 2: Chat with Your Database (2 min)

**Navigate to Chat:**

1. **Click "Chat"** in the left sidebar (chat bubble icon)
   - Or go directly to: http://localhost:3000/chat

2. **Ask about table relationships:**
   - In the message input at the bottom, type:
     ```
     What are the most important tables in the demo schema and how do they relate?
     ```
   - Press **Enter** or click the **Send button**
   - Wait for the AI to explain the data model

3. **Ask for a custom query:**
   - Type this next message:
     ```
     Write me a query to find customers who haven't ordered in 90 days but have high lifetime value
     ```
   - Press **Enter**
   - The AI will generate SQL code for you

4. **Ask about specific columns:**
   - Type:
     ```
     What does the customer_segments table tell us? What's the churn_risk column?
     ```
   - Press **Enter**
   - The AI explains the business meaning

*"You're having a conversation with your database. No docs needed."*

### Act 3: AI-Powered Analysis (1.5 min)

**Run an AI Analysis Job:**

1. **Click "Analysis"** in the left sidebar
   - Or go directly to: http://localhost:3000/analysis

2. **You'll see the Analysis page with:**
   - A multi-select dropdown for tables
   - A dropdown for analysis type
   - A dropdown for AI model
   - A "Run Analysis" button

3. **Select tables to analyze:**
   - Click the **tables dropdown/selector**
   - Check the boxes for:
     - `demo.customers`
     - `demo.orders`
     - `demo.customer_segments`

4. **Choose analysis type:**
   - Click the **analysis type dropdown**
   - Select **"Column Documentation"** or **"Data Quality"**

5. **Pick your AI model:**
   - Click the **model dropdown**
   - Select **"gpt-4o"** (or any available model)

6. **Run the analysis:**
   - Click the **"Run Analysis"** button (usually blue/primary color)
   - Wait for the job to complete (progress indicator appears)

**View Generated Documentation:**

7. **Click "Dictionary"** in the left sidebar
   - Or go directly to: http://localhost:3000/dictionary

8. **Browse the AI-generated docs:**
   - Select the **"demo"** schema from the dropdown at the top
   - Click on a table name like **"customers"**
   - You'll see each column with:
     - Business-friendly names (e.g., "Customer Identifier" instead of `customer_id`)
     - Plain English descriptions
     - Data type information

*"What used to take weeks of interviews... done in 30 seconds."*

### Act 4: ML Feature Engineering Query (30 sec)

**Go back to Data Explorer:**

1. **Click "Explorer"** in the left sidebar

2. **In the SQL Editor, paste this query:**
   ```sql
   SELECT
       c.customer_id,
       c.first_name,
       COUNT(o.order_id) as total_orders,
       SUM(o.total_amount) as total_spent,
       AVG(o.total_amount) as avg_order_value,
       cs.churn_risk,
       cs.segment_name
   FROM demo.customers c
   JOIN demo.orders o ON c.customer_id = o.customer_id
   JOIN demo.customer_segments cs ON c.customer_id = cs.customer_id
   WHERE cs.churn_risk > 0.5
   GROUP BY c.customer_id, c.first_name, cs.churn_risk, cs.segment_name
   ORDER BY total_spent DESC
   LIMIT 20
   ```

3. **Click "Run Query"** or **"Execute"**

4. **View the results:**
   - Shows high-value customers at risk of churning
   - Each row has customer info, order stats, and churn risk score

*"High-value customers at risk of churning. That's an ML feature engineering query that took 10 seconds to write."*

---

## Quick Demo Queries

### How to Run Queries in Data Explorer

1. **Navigate to Explorer** (click in sidebar or go to http://localhost:3000/explorer)
2. **Find the SQL Editor** (large text area in the middle of the page)
3. **Paste a query** (use Ctrl+V or Cmd+V)
4. **Click "Run Query"** or **"Execute"** button (blue button, usually top-right of editor)
5. **View results** in the table below the editor

### Customer Insights
```sql
-- Top customers by revenue
SELECT first_name, last_name, country_name, lifetime_value
FROM demo.customers
ORDER BY lifetime_value DESC
LIMIT 10;

-- Customers at churn risk
SELECT c.first_name, c.last_name, c.lifetime_value, cs.churn_risk, cs.segment_name
FROM demo.customers c
JOIN demo.customer_segments cs ON c.customer_id = cs.customer_id
WHERE cs.churn_risk > 0.7
ORDER BY c.lifetime_value DESC;
```

### Sales Analysis
```sql
-- Revenue by country
SELECT country_code,
       SUM(total_revenue) as revenue,
       SUM(total_orders) as orders,
       ROUND(AVG(avg_order_value), 2) as avg_order
FROM demo.sales_summary
GROUP BY country_code
ORDER BY revenue DESC;

-- Best selling categories
SELECT category,
       SUM(total_revenue) as revenue,
       SUM(total_orders) as orders
FROM demo.sales_summary
GROUP BY category
ORDER BY revenue DESC;
```

### Chat Questions (How to Use)

1. **Navigate to Chat** (click chat icon in sidebar or go to http://localhost:3000/chat)
2. **Type your question** in the input field at the bottom of the screen
3. **Press Enter** or **click the Send button** (arrow icon)
4. **Wait for the AI response** to stream in above your message

Try these questions:
- "What's the average order value by country?"
- "Which product category has the most orders?"
- "Find customers in the Champions segment with orders over $500"
- "Explain the relationship between customers, orders, and customer_segments"

---

## UI Navigation Reference

### Left Sidebar Icons (top to bottom)

| Icon | Name | URL | What It Does |
|------|------|-----|--------------|
| Home/Grid | Dashboard | / | Overview cards for all features |
| Database | Explorer | /explorer | Browse schemas, tables, run SQL |
| Chat bubble | Chat | /chat | Natural language database queries |
| Book | Dictionary | /dictionary | View/edit column documentation |
| Chart | Analysis | /analysis | Run AI analysis jobs on tables |
| Gear | Settings | /settings | Configure API keys and options |

### Data Explorer Page Layout

```
+--------------------------------------------------+
| Schema: [demo v]              [Run Query] button  |
+--------------------------------------------------+
| Tables List    |   SQL Editor                     |
| - customers    |   +----------------------------+ |
| - orders       |   | SELECT * FROM ...          | |
| - products     |   +----------------------------+ |
| - order_items  |                                  |
| - segments     |   Query Results Table            |
| - sales_summary|   +----------------------------+ |
|                |   | col1 | col2 | col3 | ...   | |
+--------------------------------------------------+
```

### Chat Page Layout

```
+--------------------------------------------------+
|                    Chat                           |
+--------------------------------------------------+
|                                                   |
|  [AI Response bubbles appear here]                |
|                                                   |
|  User: What tables are in the demo schema?        |
|                                                   |
|  AI: The demo schema contains 6 tables:           |
|      - customers: stores customer information...  |
|                                                   |
+--------------------------------------------------+
|  [Type a message...                    ] [Send]   |
+--------------------------------------------------+
```

### Settings Page Layout

```
+--------------------------------------------------+
| Settings                                          |
+--------------------------------------------------+
| Categories    |   Setting Cards                   |
| [LLM]         |   +----------------------------+ |
| [Compute]     |   | OPENAI_API_KEY             | |
| [Storage]     |   | [sk-proj-xxx...] [Test]    | |
| [OAuth]       |   +----------------------------+ |
|               |   | ANTHROPIC_API_KEY          | |
|               |   | [Not configured] [Test]    | |
+--------------------------------------------------+
```

---

## Demo URLs

| Feature | URL | What to Show |
|---------|-----|--------------|
| Dashboard | http://localhost:3000 | Overview of all features |
| Data Explorer | http://localhost:3000/explorer | Browse tables, run SQL |
| Chat | http://localhost:3000/chat | Natural language queries |
| Data Dictionary | http://localhost:3000/dictionary | AI-generated documentation |
| Data Analysis | http://localhost:3000/analysis | Run AI analysis jobs |
| Settings | http://localhost:3000/settings | API key configuration |
| Lineage Demo | http://localhost:3000/lineage-full-demo | SQL lineage analysis |
| API Docs | http://localhost:8000/docs | Swagger UI |

---

## If You Only Have 60 Seconds

1. **Open browser**: http://localhost:3000/chat
2. **Click** the message input at the bottom of the screen
3. **Type**: "Look at the demo schema. What tables do I have and how are they connected?"
4. **Press Enter** to send
5. **Wait 5 seconds** for the AI to respond
6. **Read the response** - it lists all tables and explains relationships
7. **Say**: *"That took 5 seconds. The last data engineer took 3 months to figure this out."*

---

## Troubleshooting

### "No tables found" in Data Explorer
1. Make sure you ran `python scripts/seed_demo_data.py` in the backend folder
2. In Data Explorer, **click the schema dropdown** at the top
3. **Select "demo"** (not "public" or "information_schema")
4. The table list should now show: customers, orders, products, etc.

### "API key not configured" error
1. **Click "Settings"** in the left sidebar (gear icon)
2. **Click on "LLM"** category in the left panel
3. **Find "OPENAI_API_KEY"** card
4. **Click the input field** and paste your API key
5. **Click "Save"** button on the card
6. **Click "Test"** button to verify it works (should show green checkmark)

### "Connection refused" error
- Is PostgreSQL running? Check with `pg_isready` in terminal
- Is the backend running? Open http://localhost:8000/health in browser
- Is the frontend running? Open http://localhost:3000 in browser

### Chat not responding
1. **Open browser DevTools**: Press F12 or right-click > "Inspect"
2. **Click "Console" tab**: Look for red error messages
3. **Go to Settings** (gear icon in sidebar)
4. **Click "Test"** next to your API key - should show green if working
5. **Check terminal** where backend is running for error messages

---

## What NOT To Do

- Don't show empty databases - always seed data first
- Don't forget to select the `demo` schema in Data Explorer
- Don't use `public` schema (it may be empty)
- Don't apologize for rough edges - own it
- Don't list features - just demonstrate them

---

## The Pitch (If Asked)

*"ZeroStack is what happens when you give an AI full access to understand your data. Not just query it - understand it. Every table, every column, every relationship. Then you just... ask questions."*

*"It's like having a senior data engineer who's been at the company for 10 years, available 24/7, for every database you have."*
