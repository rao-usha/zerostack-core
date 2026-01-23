"""
Test SQL Parser with realistic queries

Run this to see how the parser extracts lineage from various SQL patterns.
"""
from sql_parser import SQLLineageParser


def test_queries():
    """Test parser with various SQL queries"""
    parser = SQLLineageParser()
    
    test_cases = [
        {
            "name": "Simple SELECT",
            "sql": "SELECT * FROM sales WHERE amount > 100"
        },
        {
            "name": "INNER JOIN",
            "sql": """
            SELECT s.date, s.amount, c.name, c.segment
            FROM sales s
            INNER JOIN customers c ON s.customer_id = c.id
            WHERE s.date >= '2024-01-01'
            """
        },
        {
            "name": "LEFT JOIN with aggregation",
            "sql": """
            SELECT 
                c.segment,
                COUNT(*) as customer_count,
                SUM(s.amount) as total_sales
            FROM customers c
            LEFT JOIN sales s ON c.id = s.customer_id
            GROUP BY c.segment
            """
        },
        {
            "name": "Multi-table JOIN",
            "sql": """
            SELECT 
                p.product_name,
                c.category_name,
                SUM(s.quantity) as total_sold
            FROM sales s
            JOIN products p ON s.product_id = p.id
            JOIN categories c ON p.category_id = c.id
            WHERE s.date >= '2024-01-01'
            GROUP BY p.product_name, c.category_name
            """
        },
        {
            "name": "Schema-qualified tables",
            "sql": """
            SELECT t1.*, t2.value
            FROM prod_schema.transactions t1
            JOIN staging_schema.reference t2 ON t1.ref_id = t2.id
            """
        },
        {
            "name": "INSERT INTO SELECT",
            "sql": """
            INSERT INTO summary_table (date, total_amount, customer_count)
            SELECT 
                DATE_TRUNC('day', created_at) as date,
                SUM(amount) as total_amount,
                COUNT(DISTINCT customer_id) as customer_count
            FROM sales
            GROUP BY DATE_TRUNC('day', created_at)
            """
        },
        {
            "name": "CREATE TABLE AS SELECT",
            "sql": """
            CREATE TABLE customer_segments AS
            SELECT 
                customer_id,
                CASE 
                    WHEN total_spend > 10000 THEN 'VIP'
                    WHEN total_spend > 1000 THEN 'Regular'
                    ELSE 'Occasional'
                END as segment
            FROM (
                SELECT customer_id, SUM(amount) as total_spend
                FROM sales
                GROUP BY customer_id
            ) customer_totals
            """
        },
        {
            "name": "Subquery",
            "sql": """
            SELECT *
            FROM (
                SELECT customer_id, SUM(amount) as total
                FROM sales
                GROUP BY customer_id
            ) customer_totals
            WHERE total > 5000
            """
        },
        {
            "name": "UNION",
            "sql": """
            SELECT 'sales' as source, COUNT(*) as count FROM sales
            UNION ALL
            SELECT 'returns' as source, COUNT(*) as count FROM returns
            """
        },
    ]
    
    print("=" * 80)
    print("SQL PARSER LINEAGE TEST SUITE")
    print("=" * 80)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. {test_case['name']}")
        print("-" * 80)
        print(f"SQL: {test_case['sql'].strip()}")
        print()
        
        try:
            lineage = parser.parse(test_case['sql'])
            
            print(f"✓ Query Type: {lineage.query_type}")
            
            if lineage.source_tables:
                print(f"✓ Source Tables:")
                for table in lineage.source_tables:
                    alias_info = f" (alias: {table.alias})" if table.alias else ""
                    print(f"  - {table.full_name}{alias_info}")
            else:
                print("✗ No source tables detected")
            
            if lineage.target_table:
                print(f"✓ Target Table: {lineage.target_table.full_name}")
            
            if lineage.columns_used:
                print(f"✓ Columns Used: {len(lineage.columns_used)}")
                for col in lineage.columns_used[:5]:  # Show first 5
                    table_prefix = f"{col.table}." if col.table else ""
                    print(f"  - {table_prefix}{col.column}")
                if len(lineage.columns_used) > 5:
                    print(f"  ... and {len(lineage.columns_used) - 5} more")
            
            print(f"✓ Transformations:")
            if lineage.join_type:
                print(f"  - JOIN: {lineage.join_type}")
            if lineage.has_aggregation:
                print(f"  - AGGREGATION: Yes")
            if lineage.has_filter:
                print(f"  - FILTER: Yes (WHERE clause)")
            
            if not lineage.join_type and not lineage.has_aggregation and not lineage.has_filter:
                print(f"  - None detected")
                
        except Exception as e:
            print(f"✗ Error parsing query: {e}")
    
    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    test_queries()
