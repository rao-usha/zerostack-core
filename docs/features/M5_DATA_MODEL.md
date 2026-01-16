# M5 Forecasting Dataset - Quick Start Guide

## Overview

The **M5 Forecasting** dataset is a Walmart-style retail demand forecasting dataset from the [Kaggle M5 competition](https://www.kaggle.com/competitions/m5-forecasting-accuracy). It's ideal for:

- **Hierarchical demand forecasting** (item → category → department → store → state)
- **Price elasticity analysis**
- **Promotional impact modeling**
- **Inventory optimization**
- **Forecasting model evaluation**

## Dataset Summary

| Attribute | Value |
|-----------|-------|
| **Source** | Kaggle M5 Forecasting Competition |
| **Date Range** | 2011-01-29 to 2016-06-19 (1,969 days) |
| **Stores** | 10 stores across 3 states (CA, TX, WI) |
| **Items** | ~3,049 unique products |
| **Categories** | 3 (FOODS, HOBBIES, HOUSEHOLD) |
| **Departments** | 7 |
| **License** | Kaggle Competition Data License |

---

## Database Tables

### `m5_calendar` - Calendar Dimension
Date information with events and SNAP (food stamp) indicators.

| Column | Type | Description |
|--------|------|-------------|
| `date` | DATE | Calendar date (PK) |
| `d` | VARCHAR(10) | Day identifier (d_1 to d_1969) |
| `wm_yr_wk` | INTEGER | Walmart year-week |
| `weekday` | VARCHAR(10) | Day name (Monday, Tuesday, etc.) |
| `wday` | INTEGER | Day of week (1-7) |
| `month` | INTEGER | Month (1-12) |
| `year` | INTEGER | Year |
| `event_name_1` | VARCHAR(50) | Primary event name (e.g., SuperBowl, Christmas) |
| `event_type_1` | VARCHAR(30) | Event type (Sporting, Cultural, National, Religious) |
| `event_name_2` | VARCHAR(50) | Secondary event name |
| `event_type_2` | VARCHAR(30) | Secondary event type |
| `snap_ca` | INTEGER | SNAP day for California (0/1) |
| `snap_tx` | INTEGER | SNAP day for Texas (0/1) |
| `snap_wi` | INTEGER | SNAP day for Wisconsin (0/1) |

### `m5_items` - Item Dimension
Product hierarchy information.

| Column | Type | Description |
|--------|------|-------------|
| `id` | VARCHAR(50) | Unique ID: item_id + store_id (PK) |
| `item_id` | VARCHAR(30) | Product identifier (e.g., FOODS_1_001) |
| `dept_id` | VARCHAR(20) | Department (FOODS_1, FOODS_2, FOODS_3, HOBBIES_1, HOBBIES_2, HOUSEHOLD_1, HOUSEHOLD_2) |
| `cat_id` | VARCHAR(20) | Category (FOODS, HOBBIES, HOUSEHOLD) |
| `store_id` | VARCHAR(10) | Store (CA_1, CA_2, CA_3, CA_4, TX_1, TX_2, TX_3, WI_1, WI_2, WI_3) |
| `state_id` | VARCHAR(5) | State (CA, TX, WI) |

### `m5_prices` - Price Data
Weekly prices by store and item.

| Column | Type | Description |
|--------|------|-------------|
| `store_id` | VARCHAR(10) | Store identifier |
| `item_id` | VARCHAR(30) | Product identifier |
| `wm_yr_wk` | INTEGER | Walmart year-week |
| `sell_price` | NUMERIC(10,2) | Selling price |

**Primary Key:** (store_id, item_id, wm_yr_wk)

### `m5_sales` - Daily Sales (Long Format)
Daily unit sales per item-store combination.

| Column | Type | Description |
|--------|------|-------------|
| `item_store_id` | VARCHAR(50) | FK to m5_items.id |
| `d` | VARCHAR(10) | Day identifier (FK to m5_calendar.d) |
| `item_id` | VARCHAR(30) | Product identifier |
| `store_id` | VARCHAR(10) | Store identifier |
| `date` | DATE | Calendar date |
| `sales` | INTEGER | Unit sales for the day |

**Primary Key:** (item_store_id, d)

---

## Common Queries

### 1. Daily Sales by Store
```sql
SELECT 
    s.store_id,
    c.date,
    SUM(s.sales) as total_units
FROM m5_sales s
JOIN m5_calendar c ON s.d = c.d
GROUP BY s.store_id, c.date
ORDER BY c.date DESC, s.store_id;
```

### 2. Weekly Sales by Category
```sql
SELECT 
    i.cat_id as category,
    c.year,
    c.wm_yr_wk,
    SUM(s.sales) as total_units
FROM m5_sales s
JOIN m5_items i ON s.item_store_id = i.id
JOIN m5_calendar c ON s.d = c.d
GROUP BY i.cat_id, c.year, c.wm_yr_wk
ORDER BY c.year, c.wm_yr_wk, i.cat_id;
```

### 3. Sales with Price Data (Price Elasticity)
```sql
SELECT 
    s.item_id,
    s.store_id,
    c.date,
    s.sales,
    p.sell_price
FROM m5_sales s
JOIN m5_calendar c ON s.d = c.d
JOIN m5_prices p ON s.item_id = p.item_id 
    AND s.store_id = p.store_id 
    AND c.wm_yr_wk = p.wm_yr_wk
WHERE s.item_id = 'FOODS_1_001'
ORDER BY c.date;
```

### 4. Event Impact Analysis
```sql
SELECT 
    c.event_name_1 as event,
    c.event_type_1 as event_type,
    COUNT(DISTINCT c.date) as days,
    AVG(daily_sales.total_sales) as avg_daily_sales
FROM m5_calendar c
JOIN (
    SELECT d, SUM(sales) as total_sales
    FROM m5_sales
    GROUP BY d
) daily_sales ON c.d = daily_sales.d
WHERE c.event_name_1 IS NOT NULL
GROUP BY c.event_name_1, c.event_type_1
ORDER BY avg_daily_sales DESC;
```

### 5. SNAP Day Impact by State
```sql
SELECT 
    i.state_id,
    CASE 
        WHEN (i.state_id = 'CA' AND c.snap_ca = 1)
          OR (i.state_id = 'TX' AND c.snap_tx = 1)
          OR (i.state_id = 'WI' AND c.snap_wi = 1)
        THEN 'SNAP Day'
        ELSE 'Non-SNAP Day'
    END as day_type,
    AVG(s.sales) as avg_sales
FROM m5_sales s
JOIN m5_items i ON s.item_store_id = i.id
JOIN m5_calendar c ON s.d = c.d
WHERE i.cat_id = 'FOODS'  -- SNAP typically affects food sales
GROUP BY i.state_id, day_type
ORDER BY i.state_id, day_type;
```

### 6. Hierarchical Aggregation (State → Store → Department)
```sql
SELECT 
    i.state_id,
    i.store_id,
    i.dept_id,
    SUM(s.sales) as total_units,
    COUNT(DISTINCT s.d) as days_with_sales
FROM m5_sales s
JOIN m5_items i ON s.item_store_id = i.id
GROUP BY i.state_id, i.store_id, i.dept_id
ORDER BY i.state_id, i.store_id, i.dept_id;
```

### 7. Time Series for Forecasting (Single Item)
```sql
SELECT 
    c.date,
    c.weekday,
    c.wm_yr_wk,
    s.sales,
    p.sell_price,
    c.event_name_1,
    CASE WHEN c.snap_ca = 1 THEN 1 ELSE 0 END as is_snap_day
FROM m5_sales s
JOIN m5_calendar c ON s.d = c.d
LEFT JOIN m5_prices p ON s.item_id = p.item_id 
    AND s.store_id = p.store_id 
    AND c.wm_yr_wk = p.wm_yr_wk
WHERE s.item_store_id = 'FOODS_1_001_CA_1'
ORDER BY c.date;
```

### 8. Top Selling Items by Store
```sql
SELECT 
    s.store_id,
    s.item_id,
    i.cat_id,
    i.dept_id,
    SUM(s.sales) as total_units
FROM m5_sales s
JOIN m5_items i ON s.item_store_id = i.id
GROUP BY s.store_id, s.item_id, i.cat_id, i.dept_id
ORDER BY s.store_id, total_units DESC;
```

---

## Hierarchy Structure

```
State (3)
├── CA (California)
│   ├── CA_1, CA_2, CA_3, CA_4 (4 stores)
├── TX (Texas)
│   ├── TX_1, TX_2, TX_3 (3 stores)
└── WI (Wisconsin)
    └── WI_1, WI_2, WI_3 (3 stores)

Category (3)
├── FOODS
│   ├── FOODS_1 (department)
│   ├── FOODS_2
│   └── FOODS_3
├── HOBBIES
│   ├── HOBBIES_1
│   └── HOBBIES_2
└── HOUSEHOLD
    ├── HOUSEHOLD_1
    └── HOUSEHOLD_2
```

---

## API Endpoints

### Get M5 Dataset Info
```bash
GET /api/v1/kaggle/m5/info
```

### View Table Schema
```bash
GET /api/v1/kaggle/m5/schema
```

### Ingest M5 Data
```bash
# Full ingestion (~30K items, ~60M rows) - takes 30-60 minutes
POST /api/v1/kaggle/m5/ingest
Content-Type: application/json
{"force_download": false}

# Test ingestion (limited items)
POST /api/v1/kaggle/m5/ingest
Content-Type: application/json
{"force_download": false, "limit_items": 100}
```

### Check Ingestion Status
```bash
GET /api/v1/jobs/{job_id}
```

---

## Use Cases

### 1. Demand Forecasting
Build time series models to predict future sales at various hierarchy levels.

```sql
-- Get training data for Prophet/ARIMA
SELECT date, SUM(sales) as y
FROM m5_sales s
JOIN m5_calendar c ON s.d = c.d
WHERE store_id = 'CA_1'
GROUP BY date
ORDER BY date;
```

### 2. Price Optimization
Analyze price elasticity to optimize pricing strategies.

```sql
-- Price vs demand correlation
SELECT 
    item_id,
    CORR(sell_price, avg_sales) as price_elasticity
FROM (
    SELECT 
        s.item_id,
        p.sell_price,
        AVG(s.sales) as avg_sales
    FROM m5_sales s
    JOIN m5_calendar c ON s.d = c.d
    JOIN m5_prices p ON s.item_id = p.item_id 
        AND s.store_id = p.store_id 
        AND c.wm_yr_wk = p.wm_yr_wk
    GROUP BY s.item_id, p.sell_price
) price_sales
GROUP BY item_id
HAVING COUNT(*) > 10;
```

### 3. Promotional Planning
Identify which events drive the most sales.

### 4. Inventory Management
Use forecasts to optimize stock levels and reduce stockouts.

### 5. Store Performance Analysis
Compare sales performance across stores and regions.

---

## Data Quality Notes

- **Missing Sales:** Days with 0 sales are included (not missing data)
- **Price Changes:** Prices change weekly (tied to `wm_yr_wk`)
- **Events:** Not all days have events; NULL means no special event
- **SNAP Days:** Binary indicator per state (not all states have SNAP on same days)

---

## Connection Details

```
Host: localhost
Port: 5433
Database: nexdata
User: nexdata
Password: nexdata_dev_password
```

**Example connection:**
```bash
psql -h localhost -p 5433 -U nexdata -d nexdata
```

**Python (SQLAlchemy):**
```python
from sqlalchemy import create_engine
engine = create_engine('postgresql://nexdata:nexdata_dev_password@localhost:5433/nexdata')
```

**Python (pandas):**
```python
import pandas as pd
from sqlalchemy import create_engine

engine = create_engine('postgresql://nexdata:nexdata_dev_password@localhost:5433/nexdata')
df = pd.read_sql("SELECT * FROM m5_sales LIMIT 1000", engine)
```

---

## References

- [M5 Forecasting Competition](https://www.kaggle.com/competitions/m5-forecasting-accuracy)
- [M5 Competitors Guide (PDF)](https://mofc.unic.ac.cy/m5-competition/)
- [Winning Solutions](https://www.kaggle.com/competitions/m5-forecasting-accuracy/discussion/163684)
