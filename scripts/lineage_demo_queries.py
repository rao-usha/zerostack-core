"""
Lineage Demo Queries

This script contains sample queries that demonstrate various lineage features.
Run these through the lineage tracker to populate the system with realistic examples.
"""

# ============================================
# Demo Queries organized by feature
# ============================================

DEMO_QUERIES = {
    "basic_select": {
        "name": "Simple SELECT with Filter",
        "sql": """
            SELECT customer_id, name, email, country
            FROM customers_clean
            WHERE country = 'USA'
            LIMIT 100
        """,
        "demonstrates": ["Basic table lineage", "WHERE clause filter"],
        "expected_lineage": {
            "source_tables": ["customers_clean"],
            "has_filter": True,
            "has_aggregation": False
        }
    },
    
    "inner_join": {
        "name": "INNER JOIN with Aggregation",
        "sql": """
            SELECT 
                c.country,
                COUNT(DISTINCT c.customer_id) as customer_count,
                SUM(s.amount) as total_revenue,
                AVG(s.amount) as avg_order_value
            FROM customers_clean c
            INNER JOIN sales_clean s ON c.customer_id = s.customer_id
            GROUP BY c.country
            ORDER BY total_revenue DESC
        """,
        "demonstrates": ["INNER JOIN", "Multiple aggregations", "GROUP BY"],
        "expected_lineage": {
            "source_tables": ["customers_clean", "sales_clean"],
            "join_type": "INNER",
            "has_aggregation": True
        }
    },
    
    "left_join_complex": {
        "name": "LEFT JOIN with Multiple Aggregations",
        "sql": """
            SELECT 
                c.customer_segment,
                COUNT(c.customer_id) as total_customers,
                COUNT(s.sale_id) as total_sales,
                COALESCE(SUM(s.amount), 0) as revenue,
                COALESCE(AVG(s.amount), 0) as avg_order_value,
                COUNT(s.sale_id)::FLOAT / NULLIF(COUNT(c.customer_id), 0) as sales_per_customer
            FROM customers_clean c
            LEFT JOIN sales_clean s ON c.customer_id = s.customer_id
            WHERE c.signup_date >= '2024-01-01'
            GROUP BY c.customer_segment
        """,
        "demonstrates": ["LEFT JOIN", "NULL handling", "Calculated fields"],
        "expected_lineage": {
            "source_tables": ["customers_clean", "sales_clean"],
            "join_type": "LEFT",
            "has_aggregation": True,
            "has_filter": True
        }
    },
    
    "multi_table_join": {
        "name": "Three-Way JOIN",
        "sql": """
            SELECT 
                p.category,
                p.product_name,
                COUNT(s.sale_id) as units_sold,
                SUM(s.amount) as revenue,
                COUNT(DISTINCT s.customer_id) as unique_customers
            FROM raw_products p
            INNER JOIN sales_clean s ON p.product_id = s.product_id
            INNER JOIN customers_clean c ON s.customer_id = c.customer_id
            WHERE c.country IN ('USA', 'UK', 'Canada')
            GROUP BY p.category, p.product_name
            HAVING SUM(s.amount) > 1000
            ORDER BY revenue DESC
        """,
        "demonstrates": ["Multi-table JOIN", "HAVING clause", "IN filter"],
        "expected_lineage": {
            "source_tables": ["raw_products", "sales_clean", "customers_clean"],
            "join_type": "INNER",
            "has_aggregation": True,
            "has_filter": True
        }
    },
    
    "window_functions": {
        "name": "Window Functions for Time Series",
        "sql": """
            SELECT 
                DATE(sale_date) as date,
                SUM(amount) as daily_revenue,
                AVG(SUM(amount)) OVER (
                    ORDER BY DATE(sale_date) 
                    ROWS BETWEEN 7 PRECEDING AND CURRENT ROW
                ) as moving_avg_7d,
                LAG(SUM(amount), 1) OVER (ORDER BY DATE(sale_date)) as prev_day_revenue,
                LAG(SUM(amount), 7) OVER (ORDER BY DATE(sale_date)) as prev_week_revenue
            FROM sales_clean
            WHERE sale_date >= '2024-01-01'
            GROUP BY DATE(sale_date)
            ORDER BY date
        """,
        "demonstrates": ["Window functions", "LAG", "Moving averages", "Time series"],
        "expected_lineage": {
            "source_tables": ["sales_clean"],
            "has_aggregation": True,
            "has_filter": True
        },
        "ml_likelihood": "high"
    },
    
    "ml_features_customer": {
        "name": "ML Features - Customer Churn Prediction",
        "sql": """
            SELECT 
                c.customer_id,
                c.country,
                DATE_PART('day', NOW() - c.signup_date) as days_since_signup,
                COUNT(s.sale_id) as total_orders,
                SUM(s.amount) as total_spent,
                AVG(s.amount) as avg_order_value,
                STDDEV(s.amount) as order_value_stddev,
                DATE_PART('day', NOW() - MAX(s.sale_date)) as days_since_last_purchase,
                LOG(GREATEST(SUM(s.amount), 1)) as log_total_spent,
                SQRT(GREATEST(COUNT(s.sale_id), 1)) as sqrt_order_count,
                CASE 
                    WHEN DATE_PART('day', NOW() - MAX(s.sale_date)) > 90 THEN 1
                    ELSE 0
                END as is_churned
            FROM customers_clean c
            LEFT JOIN sales_clean s ON c.customer_id = s.customer_id
            GROUP BY c.customer_id, c.country, c.signup_date
            HAVING COUNT(s.sale_id) > 0
        """,
        "demonstrates": ["ML feature engineering", "LOG transformation", "SQRT", "Statistical functions", "Label creation"],
        "expected_lineage": {
            "source_tables": ["customers_clean", "sales_clean"],
            "join_type": "LEFT",
            "has_aggregation": True
        },
        "ml_likelihood": "very_high",
        "ml_query_type": "FEATURE_EXTRACTION"
    },
    
    "ml_features_timeseries": {
        "name": "ML Features - Sales Forecasting",
        "sql": """
            SELECT 
                DATE(sale_date) as date,
                EXTRACT(year FROM sale_date) as year,
                EXTRACT(month FROM sale_date) as month,
                EXTRACT(day FROM sale_date) as day,
                EXTRACT(dow FROM sale_date) as day_of_week,
                EXTRACT(hour FROM sale_date) as hour,
                SUM(amount) as daily_revenue,
                COUNT(*) as daily_orders,
                LAG(SUM(amount), 1) OVER (ORDER BY DATE(sale_date)) as prev_day_revenue,
                LAG(SUM(amount), 7) OVER (ORDER BY DATE(sale_date)) as prev_week_revenue,
                AVG(SUM(amount)) OVER (
                    ORDER BY DATE(sale_date) 
                    ROWS BETWEEN 7 PRECEDING AND CURRENT ROW
                ) as rolling_avg_7d
            FROM sales_clean
            GROUP BY DATE(sale_date), sale_date
            ORDER BY date
        """,
        "demonstrates": ["Time features", "LAG features", "Rolling windows", "Temporal encoding"],
        "expected_lineage": {
            "source_tables": ["sales_clean"],
            "has_aggregation": True
        },
        "ml_likelihood": "very_high",
        "ml_query_type": "TRAINING_DATA"
    },
    
    "column_transformations": {
        "name": "Column-Level Transformations",
        "sql": """
            SELECT 
                customer_id,
                UPPER(TRIM(name)) as name_normalized,
                LOWER(email) as email_normalized,
                DATE_PART('year', signup_date) as signup_year,
                country,
                CASE 
                    WHEN country IN ('USA', 'Canada') THEN 'North America'
                    WHEN country IN ('UK', 'Germany', 'France') THEN 'Europe'
                    ELSE 'Other'
                END as region,
                CASE 
                    WHEN DATE_PART('day', NOW() - signup_date) < 30 THEN 'new'
                    WHEN DATE_PART('day', NOW() - signup_date) < 365 THEN 'active'
                    ELSE 'veteran'
                END as customer_lifecycle
            FROM raw_customers
            WHERE email IS NOT NULL
        """,
        "demonstrates": ["Multiple column transformations", "String functions", "Date functions", "CASE statements"],
        "expected_lineage": {
            "source_tables": ["raw_customers"],
            "has_filter": True
        }
    },
    
    "subquery": {
        "name": "Subquery with Aggregation",
        "sql": """
            SELECT 
                customer_id,
                total_orders,
                total_spent,
                CASE 
                    WHEN total_spent > 5000 THEN 'VIP'
                    WHEN total_spent > 1000 THEN 'Regular'
                    ELSE 'Occasional'
                END as customer_tier
            FROM (
                SELECT 
                    customer_id,
                    COUNT(*) as total_orders,
                    SUM(amount) as total_spent
                FROM sales_clean
                GROUP BY customer_id
            ) customer_summary
            WHERE total_orders >= 5
            ORDER BY total_spent DESC
        """,
        "demonstrates": ["Subquery", "Nested aggregation", "Derived columns"],
        "expected_lineage": {
            "source_tables": ["sales_clean"],
            "has_aggregation": True,
            "has_filter": True
        }
    },
    
    "union": {
        "name": "UNION for Combined Reporting",
        "sql": """
            SELECT 'Electronics' as category, COUNT(*) as product_count, SUM(price) as total_value
            FROM raw_products
            WHERE category = 'Electronics'
            UNION ALL
            SELECT 'Clothing', COUNT(*), SUM(price)
            FROM raw_products
            WHERE category = 'Clothing'
            UNION ALL
            SELECT 'Home & Garden', COUNT(*), SUM(price)
            FROM raw_products
            WHERE category = 'Home & Garden'
            ORDER BY total_value DESC
        """,
        "demonstrates": ["UNION ALL", "Multiple scans of same table"],
        "expected_lineage": {
            "source_tables": ["raw_products"],
            "has_aggregation": True,
            "has_filter": True
        }
    },
    
    "pipeline_stage_1": {
        "name": "Pipeline Stage 1: Clean Raw Sales",
        "sql": """
            CREATE TABLE sales_clean_demo AS
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
              AND customer_id IS NOT NULL
        """,
        "demonstrates": ["CREATE TABLE AS SELECT", "Data cleaning", "Pipeline stage"],
        "expected_lineage": {
            "source_tables": ["raw_sales"],
            "target_table": "sales_clean_demo",
            "has_filter": True
        },
        "pipeline_stage": 1
    },
    
    "pipeline_stage_2": {
        "name": "Pipeline Stage 2: Daily Aggregation",
        "sql": """
            CREATE TABLE daily_summary_demo AS
            SELECT 
                DATE(sale_date) as sale_date,
                COUNT(*) as order_count,
                SUM(amount) as total_revenue,
                AVG(amount) as avg_order_value
            FROM sales_clean_demo
            GROUP BY DATE(sale_date)
        """,
        "demonstrates": ["Pipeline continuation", "Aggregation on cleaned data"],
        "expected_lineage": {
            "source_tables": ["sales_clean_demo"],
            "target_table": "daily_summary_demo",
            "has_aggregation": True
        },
        "pipeline_stage": 2
    },
    
    "pipeline_stage_3": {
        "name": "Pipeline Stage 3: Final Report",
        "sql": """
            CREATE TABLE sales_report_demo AS
            SELECT 
                d.sale_date,
                d.total_revenue,
                d.order_count,
                AVG(d.total_revenue) OVER (
                    ORDER BY d.sale_date 
                    ROWS BETWEEN 7 PRECEDING AND CURRENT ROW
                ) as revenue_7d_ma,
                (d.total_revenue - LAG(d.total_revenue, 7) OVER (ORDER BY d.sale_date)) / 
                    NULLIF(LAG(d.total_revenue, 7) OVER (ORDER BY d.sale_date), 0) * 100 as wow_growth_pct
            FROM daily_summary_demo d
            ORDER BY d.sale_date
        """,
        "demonstrates": ["Final pipeline stage", "Window functions on aggregated data"],
        "expected_lineage": {
            "source_tables": ["daily_summary_demo"],
            "target_table": "sales_report_demo",
            "has_aggregation": False
        },
        "pipeline_stage": 3
    }
}

# ============================================
# Query Categories for Testing
# ============================================

QUERY_CATEGORIES = {
    "table_lineage": [
        "basic_select",
        "inner_join",
        "left_join_complex",
        "multi_table_join"
    ],
    "column_lineage": [
        "column_transformations",
        "ml_features_customer"
    ],
    "ml_queries": [
        "ml_features_customer",
        "ml_features_timeseries",
        "window_functions"
    ],
    "pipeline": [
        "pipeline_stage_1",
        "pipeline_stage_2",
        "pipeline_stage_3"
    ],
    "advanced": [
        "subquery",
        "union",
        "window_functions"
    ]
}

def get_query(query_key: str) -> dict:
    """Get a demo query by key"""
    return DEMO_QUERIES.get(query_key)

def get_queries_by_category(category: str) -> list:
    """Get all queries in a category"""
    query_keys = QUERY_CATEGORIES.get(category, [])
    return [DEMO_QUERIES[key] for key in query_keys if key in DEMO_QUERIES]

def get_all_queries() -> dict:
    """Get all demo queries"""
    return DEMO_QUERIES
