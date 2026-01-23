-- ============================================
-- Synthetic Data for Lineage Demo
-- ============================================
-- This script creates realistic sample data to demonstrate:
-- 1. Table-level lineage
-- 2. Column-level transformations
-- 3. Cross-query pipelines
-- 4. ML feature extraction

-- Connect to your demo database
-- \c nexdata

-- ============================================
-- Stage 1: Raw Data Tables
-- ============================================

-- Raw customer data (as if from a CRM export)
DROP TABLE IF EXISTS raw_customers CASCADE;
CREATE TABLE raw_customers (
    customer_id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(100),
    signup_date DATE,
    country VARCHAR(50),
    segment VARCHAR(20), -- will be NULL initially
    created_at TIMESTAMP DEFAULT NOW()
);

INSERT INTO raw_customers (name, email, signup_date, country, segment)
SELECT 
    'Customer ' || generate_series,
    'customer' || generate_series || '@example.com',
    DATE '2023-01-01' + (random() * 365)::INT,
    CASE (random() * 5)::INT
        WHEN 0 THEN 'USA'
        WHEN 1 THEN 'UK'
        WHEN 2 THEN 'Canada'
        WHEN 3 THEN 'Germany'
        ELSE 'France'
    END,
    NULL
FROM generate_series(1, 1000);

-- Raw sales transactions (messy data with nulls)
DROP TABLE IF EXISTS raw_sales CASCADE;
CREATE TABLE raw_sales (
    sale_id SERIAL PRIMARY KEY,
    customer_id INT,
    product_id INT,
    amount DECIMAL(10, 2),
    quantity INT,
    sale_date TIMESTAMP,
    status VARCHAR(20), -- can be 'completed', 'cancelled', 'pending'
    created_at TIMESTAMP DEFAULT NOW()
);

INSERT INTO raw_sales (customer_id, product_id, amount, quantity, sale_date, status)
SELECT 
    (random() * 999 + 1)::INT,
    (random() * 50 + 1)::INT,
    (random() * 500 + 10)::DECIMAL(10, 2),
    (random() * 10 + 1)::INT,
    TIMESTAMP '2024-01-01' + (random() * 365 || ' days')::INTERVAL + (random() * 24 || ' hours')::INTERVAL,
    CASE (random() * 10)::INT
        WHEN 0 THEN 'cancelled'
        WHEN 1 THEN 'pending'
        ELSE 'completed'
    END
FROM generate_series(1, 5000);

-- Raw products
DROP TABLE IF EXISTS raw_products CASCADE;
CREATE TABLE raw_products (
    product_id SERIAL PRIMARY KEY,
    product_name VARCHAR(100),
    category VARCHAR(50),
    price DECIMAL(10, 2),
    cost DECIMAL(10, 2),
    created_at TIMESTAMP DEFAULT NOW()
);

INSERT INTO raw_products (product_name, category, price, cost)
SELECT 
    'Product ' || generate_series,
    CASE (random() * 4)::INT
        WHEN 0 THEN 'Electronics'
        WHEN 1 THEN 'Clothing'
        WHEN 2 THEN 'Home & Garden'
        ELSE 'Sports'
    END,
    (random() * 500 + 20)::DECIMAL(10, 2),
    (random() * 300 + 10)::DECIMAL(10, 2)
FROM generate_series(1, 50);

-- ============================================
-- Stage 2: Cleaned Data (Transformation 1)
-- ============================================

-- Cleaned sales (filter out bad records)
DROP TABLE IF EXISTS sales_clean CASCADE;
CREATE TABLE sales_clean AS
SELECT 
    sale_id,
    customer_id,
    product_id,
    amount,
    quantity,
    sale_date,
    status
FROM raw_sales
WHERE status = 'completed'
  AND amount > 0
  AND quantity > 0
  AND customer_id IS NOT NULL;

-- Cleaned customers (deduplicate and enrich)
DROP TABLE IF EXISTS customers_clean CASCADE;
CREATE TABLE customers_clean AS
SELECT DISTINCT ON (customer_id)
    customer_id,
    UPPER(TRIM(name)) as name, -- Data cleaning transformation
    LOWER(TRIM(email)) as email,
    signup_date,
    country,
    CASE 
        WHEN DATE_PART('day', NOW() - signup_date) < 30 THEN 'new'
        WHEN DATE_PART('day', NOW() - signup_date) < 365 THEN 'active'
        ELSE 'veteran'
    END as customer_segment
FROM raw_customers
WHERE email IS NOT NULL;

-- ============================================
-- Stage 3: Aggregated Data (Transformation 2)
-- ============================================

-- Daily sales summary
DROP TABLE IF EXISTS daily_sales_summary CASCADE;
CREATE TABLE daily_sales_summary AS
SELECT 
    DATE(sale_date) as sale_date,
    COUNT(*) as order_count,
    COUNT(DISTINCT customer_id) as unique_customers,
    SUM(amount) as total_revenue,
    AVG(amount) as avg_order_value,
    MAX(amount) as max_order_value,
    SUM(quantity) as total_quantity
FROM sales_clean
GROUP BY DATE(sale_date);

-- Customer lifetime value
DROP TABLE IF EXISTS customer_ltv CASCADE;
CREATE TABLE customer_ltv AS
SELECT 
    c.customer_id,
    c.name,
    c.email,
    c.country,
    c.customer_segment,
    COUNT(s.sale_id) as total_orders,
    SUM(s.amount) as lifetime_value,
    AVG(s.amount) as avg_order_value,
    MIN(s.sale_date) as first_purchase,
    MAX(s.sale_date) as last_purchase,
    DATE_PART('day', MAX(s.sale_date) - MIN(s.sale_date)) as customer_age_days
FROM customers_clean c
LEFT JOIN sales_clean s ON c.customer_id = s.customer_id
GROUP BY c.customer_id, c.name, c.email, c.country, c.customer_segment;

-- Product performance
DROP TABLE IF EXISTS product_performance CASCADE;
CREATE TABLE product_performance AS
SELECT 
    p.product_id,
    p.product_name,
    p.category,
    p.price,
    p.cost,
    COUNT(s.sale_id) as units_sold,
    SUM(s.amount) as total_revenue,
    SUM(s.quantity * p.cost) as total_cost,
    SUM(s.amount) - SUM(s.quantity * p.cost) as total_profit,
    (SUM(s.amount) - SUM(s.quantity * p.cost)) / NULLIF(SUM(s.amount), 0) as profit_margin
FROM raw_products p
LEFT JOIN sales_clean s ON p.product_id = s.product_id
GROUP BY p.product_id, p.product_name, p.category, p.price, p.cost;

-- ============================================
-- Stage 4: ML Features (Transformation 3)
-- ============================================

-- Customer features for churn prediction model
DROP TABLE IF EXISTS ml_customer_features CASCADE;
CREATE TABLE ml_customer_features AS
SELECT 
    c.customer_id,
    -- Demographic features
    c.country,
    DATE_PART('day', NOW() - c.signup_date) as days_since_signup,
    
    -- Behavioral features (aggregations)
    COUNT(s.sale_id) as total_orders,
    SUM(s.amount) as total_spent,
    AVG(s.amount) as avg_order_value,
    STDDEV(s.amount) as order_value_stddev,
    
    -- Temporal features
    DATE_PART('day', NOW() - MAX(s.sale_date)) as days_since_last_purchase,
    DATE_PART('day', MAX(s.sale_date) - MIN(s.sale_date)) as customer_lifetime_days,
    
    -- Frequency features
    COUNT(s.sale_id)::FLOAT / NULLIF(DATE_PART('day', MAX(s.sale_date) - MIN(s.sale_date)), 0) as purchase_frequency,
    
    -- Trend features (window functions)
    AVG(s.amount) OVER (PARTITION BY s.customer_id ORDER BY s.sale_date ROWS BETWEEN 3 PRECEDING AND CURRENT ROW) as moving_avg_3,
    
    -- Mathematical transformations (common in ML)
    LOG(GREATEST(SUM(s.amount), 1)) as log_total_spent,
    SQRT(GREATEST(COUNT(s.sale_id), 1)) as sqrt_order_count,
    
    -- Target variable (label)
    CASE 
        WHEN DATE_PART('day', NOW() - MAX(s.sale_date)) > 90 THEN 1
        ELSE 0
    END as is_churned
    
FROM customers_clean c
LEFT JOIN sales_clean s ON c.customer_id = s.customer_id
GROUP BY c.customer_id, c.country, c.signup_date
HAVING COUNT(s.sale_id) > 0;

-- Time series features for sales forecasting
DROP TABLE IF EXISTS ml_sales_timeseries CASCADE;
CREATE TABLE ml_sales_timeseries AS
SELECT 
    DATE(sale_date) as date,
    
    -- Date features (common in time series ML)
    EXTRACT(year FROM sale_date) as year,
    EXTRACT(month FROM sale_date) as month,
    EXTRACT(day FROM sale_date) as day,
    EXTRACT(dow FROM sale_date) as day_of_week,
    EXTRACT(hour FROM sale_date) as hour,
    EXTRACT(quarter FROM sale_date) as quarter,
    
    -- Target variables
    SUM(amount) as daily_revenue,
    COUNT(*) as daily_orders,
    
    -- Lag features (previous values)
    LAG(SUM(amount), 1) OVER (ORDER BY DATE(sale_date)) as prev_day_revenue,
    LAG(SUM(amount), 7) OVER (ORDER BY DATE(sale_date)) as prev_week_revenue,
    LAG(SUM(amount), 30) OVER (ORDER BY DATE(sale_date)) as prev_month_revenue,
    
    -- Rolling aggregations
    AVG(SUM(amount)) OVER (ORDER BY DATE(sale_date) ROWS BETWEEN 7 PRECEDING AND CURRENT ROW) as rolling_avg_7d,
    AVG(SUM(amount)) OVER (ORDER BY DATE(sale_date) ROWS BETWEEN 30 PRECEDING AND CURRENT ROW) as rolling_avg_30d
    
FROM sales_clean
GROUP BY DATE(sale_date), sale_date
ORDER BY DATE(sale_date);

-- ============================================
-- Stage 5: Final Reports (Transformation 4)
-- ============================================

-- Executive dashboard summary
DROP TABLE IF EXISTS executive_dashboard CASCADE;
CREATE TABLE executive_dashboard AS
SELECT 
    ds.sale_date,
    ds.total_revenue,
    ds.order_count,
    ds.unique_customers,
    ds.avg_order_value,
    
    -- Moving averages
    AVG(ds.total_revenue) OVER (ORDER BY ds.sale_date ROWS BETWEEN 7 PRECEDING AND CURRENT ROW) as revenue_7d_ma,
    AVG(ds.total_revenue) OVER (ORDER BY ds.sale_date ROWS BETWEEN 30 PRECEDING AND CURRENT ROW) as revenue_30d_ma,
    
    -- Growth rates
    (ds.total_revenue - LAG(ds.total_revenue, 7) OVER (ORDER BY ds.sale_date)) / 
        NULLIF(LAG(ds.total_revenue, 7) OVER (ORDER BY ds.sale_date), 0) * 100 as wow_growth_pct,
    
    -- Category breakdown (join)
    COALESCE(SUM(CASE WHEN p.category = 'Electronics' THEN s.amount END), 0) as electronics_revenue,
    COALESCE(SUM(CASE WHEN p.category = 'Clothing' THEN s.amount END), 0) as clothing_revenue,
    COALESCE(SUM(CASE WHEN p.category = 'Home & Garden' THEN s.amount END), 0) as home_revenue,
    COALESCE(SUM(CASE WHEN p.category = 'Sports' THEN s.amount END), 0) as sports_revenue

FROM daily_sales_summary ds
LEFT JOIN sales_clean s ON DATE(s.sale_date) = ds.sale_date
LEFT JOIN raw_products p ON s.product_id = p.product_id
GROUP BY ds.sale_date, ds.total_revenue, ds.order_count, ds.unique_customers, ds.avg_order_value
ORDER BY ds.sale_date;

-- ============================================
-- Create Indexes for Performance
-- ============================================

CREATE INDEX idx_sales_clean_customer ON sales_clean(customer_id);
CREATE INDEX idx_sales_clean_date ON sales_clean(sale_date);
CREATE INDEX idx_sales_clean_product ON sales_clean(product_id);
CREATE INDEX idx_customers_clean_id ON customers_clean(customer_id);

-- ============================================
-- Summary Statistics
-- ============================================

-- Display what was created
SELECT 'raw_customers' as table_name, COUNT(*) as row_count FROM raw_customers
UNION ALL
SELECT 'raw_sales', COUNT(*) FROM raw_sales
UNION ALL
SELECT 'raw_products', COUNT(*) FROM raw_products
UNION ALL
SELECT 'sales_clean', COUNT(*) FROM sales_clean
UNION ALL
SELECT 'customers_clean', COUNT(*) FROM customers_clean
UNION ALL
SELECT 'daily_sales_summary', COUNT(*) FROM daily_sales_summary
UNION ALL
SELECT 'customer_ltv', COUNT(*) FROM customer_ltv
UNION ALL
SELECT 'product_performance', COUNT(*) FROM product_performance
UNION ALL
SELECT 'ml_customer_features', COUNT(*) FROM ml_customer_features
UNION ALL
SELECT 'ml_sales_timeseries', COUNT(*) FROM ml_sales_timeseries
UNION ALL
SELECT 'executive_dashboard', COUNT(*) FROM executive_dashboard
ORDER BY table_name;

-- ============================================
-- Data Pipeline Summary
-- ============================================
SELECT '
===============================================
LINEAGE DEMO DATA CREATED SUCCESSFULLY!
===============================================

Data Pipeline Stages:
1. RAW DATA (3 tables)
   - raw_customers (1,000 rows)
   - raw_sales (5,000 rows)
   - raw_products (50 rows)

2. CLEANED DATA (2 tables)
   - sales_clean (filtered raw_sales)
   - customers_clean (enriched raw_customers)

3. AGGREGATED DATA (3 tables)
   - daily_sales_summary
   - customer_ltv
   - product_performance

4. ML FEATURES (2 tables)
   - ml_customer_features (churn prediction)
   - ml_sales_timeseries (forecasting)

5. REPORTS (1 table)
   - executive_dashboard

This demonstrates:
✓ Table-level lineage (raw → clean → agg → ml → report)
✓ Column transformations (UPPER, LOG, LAG, etc.)
✓ Cross-query pipelines (multi-stage flows)
✓ ML feature extraction (window functions, stats)

Next: Run the demo queries to populate lineage!
===============================================
' as summary;
