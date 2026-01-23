# M5 Forecasting Dataset

The M5 Forecasting dataset is a Walmart-style retail demand forecasting dataset from the Kaggle M5 competition, integrated into NEX for ML model development and testing.

## Overview

The M5 dataset provides:
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

---

## Database Tables

### `m5_calendar` - Calendar Dimension

| Column | Type | Description |
|--------|------|-------------|
| `date` | DATE | Calendar date (PK) |
| `d` | VARCHAR(10) | Day identifier (d_1 to d_1969) |
| `wm_yr_wk` | INTEGER | Walmart year-week |
| `weekday` | VARCHAR(10) | Day name |
| `event_name_1` | VARCHAR(50) | Event (SuperBowl, Christmas, etc.) |
| `snap_ca/tx/wi` | INTEGER | SNAP day indicator (0/1) |

### `m5_items` - Item Dimension

| Column | Type | Description |
|--------|------|-------------|
| `id` | VARCHAR(50) | Unique ID: item_id + store_id (PK) |
| `item_id` | VARCHAR(30) | Product identifier |
| `dept_id` | VARCHAR(20) | Department |
| `cat_id` | VARCHAR(20) | Category |
| `store_id` | VARCHAR(10) | Store |
| `state_id` | VARCHAR(5) | State (CA, TX, WI) |

### `m5_prices` - Price Data

| Column | Type | Description |
|--------|------|-------------|
| `store_id` | VARCHAR(10) | Store identifier |
| `item_id` | VARCHAR(30) | Product identifier |
| `wm_yr_wk` | INTEGER | Walmart year-week |
| `sell_price` | NUMERIC(10,2) | Selling price |

### `m5_sales` - Daily Sales

| Column | Type | Description |
|--------|------|-------------|
| `item_store_id` | VARCHAR(50) | FK to m5_items |
| `d` | VARCHAR(10) | Day identifier |
| `date` | DATE | Calendar date |
| `sales` | INTEGER | Unit sales |

---

## Hierarchy Structure

```
State (3)
├── CA → CA_1, CA_2, CA_3, CA_4 (4 stores)
├── TX → TX_1, TX_2, TX_3 (3 stores)
└── WI → WI_1, WI_2, WI_3 (3 stores)

Category (3)
├── FOODS → FOODS_1, FOODS_2, FOODS_3
├── HOBBIES → HOBBIES_1, HOBBIES_2
└── HOUSEHOLD → HOUSEHOLD_1, HOUSEHOLD_2
```

---

## Common Queries

### Daily Sales by Store
```sql
SELECT s.store_id, c.date, SUM(s.sales) as total_units
FROM m5_sales s
JOIN m5_calendar c ON s.d = c.d
GROUP BY s.store_id, c.date
ORDER BY c.date DESC;
```

### Sales with Price (Elasticity Analysis)
```sql
SELECT s.item_id, c.date, s.sales, p.sell_price
FROM m5_sales s
JOIN m5_calendar c ON s.d = c.d
JOIN m5_prices p ON s.item_id = p.item_id 
    AND s.store_id = p.store_id 
    AND c.wm_yr_wk = p.wm_yr_wk
WHERE s.item_id = 'FOODS_1_001';
```

### Event Impact Analysis
```sql
SELECT c.event_name_1, AVG(daily.total_sales) as avg_sales
FROM m5_calendar c
JOIN (
    SELECT d, SUM(sales) as total_sales FROM m5_sales GROUP BY d
) daily ON c.d = daily.d
WHERE c.event_name_1 IS NOT NULL
GROUP BY c.event_name_1;
```

### Time Series for Forecasting
```sql
SELECT c.date, s.sales, p.sell_price, c.event_name_1
FROM m5_sales s
JOIN m5_calendar c ON s.d = c.d
LEFT JOIN m5_prices p ON s.item_id = p.item_id 
    AND s.store_id = p.store_id 
    AND c.wm_yr_wk = p.wm_yr_wk
WHERE s.item_store_id = 'FOODS_1_001_CA_1'
ORDER BY c.date;
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/kaggle/m5/info` | Dataset info |
| `GET` | `/api/v1/kaggle/m5/schema` | Table schemas |
| `POST` | `/api/v1/kaggle/m5/ingest` | Trigger data ingestion |

### Ingestion Options

```json
{
  "force_download": false,
  "limit_items": 100  // Optional: for testing
}
```

---

## Use Cases

### 1. Demand Forecasting
Build time series models (Prophet, ARIMA, etc.) to predict future sales.

### 2. Price Optimization
Analyze price elasticity to optimize pricing strategies.

### 3. Promotional Planning
Identify which events drive the most sales.

### 4. Inventory Management
Use forecasts to optimize stock levels.

### 5. Store Performance
Compare sales across stores and regions.

---

## Connection Details

```
Host: localhost
Port: 5433
Database: nexdata
User: nexdata
Password: nexdata_dev_password
```

Python connection:
```python
from sqlalchemy import create_engine
engine = create_engine('postgresql://nexdata:nexdata_dev_password@localhost:5433/nexdata')
```

---

## Data Quality Notes

- **Missing Sales**: Days with 0 sales are included (not missing)
- **Price Changes**: Prices change weekly (tied to `wm_yr_wk`)
- **Events**: NULL means no special event
- **SNAP Days**: Binary per state (different schedules)

---

## Related Documentation

- [ML Development](./ml-development.md)
- [Forecasting Recipes](./ml-development.md#model-families)
- [Evaluation Packs](./ml-development.md#evaluation-packs)
