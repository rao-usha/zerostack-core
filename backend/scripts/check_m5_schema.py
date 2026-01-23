#!/usr/bin/env python3
"""Check M5 table schemas."""
import psycopg

conn = psycopg.connect(
    host='host.docker.internal',
    port=5433,
    user='nexdata',
    password='nexdata_dev_password',
    dbname='nexdata'
)
cur = conn.cursor()

m5_tables = ['m5_calendar', 'm5_items', 'm5_prices', 'm5_sales']

for table in m5_tables:
    print(f"\n{'='*60}")
    print(f"TABLE: {table}")
    print('='*60)
    
    # Get columns
    cur.execute(f"""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_name = '{table}'
        ORDER BY ordinal_position
    """)
    columns = cur.fetchall()
    
    print("Columns:")
    for col in columns:
        print(f"  {col[0]}: {col[1]} {'(nullable)' if col[2] == 'YES' else ''}")
    
    # Sample data
    cur.execute(f'SELECT * FROM {table} LIMIT 3')
    rows = cur.fetchall()
    col_names = [c[0] for c in columns]
    
    print(f"\nSample data ({len(rows)} rows):")
    for row in rows:
        print(f"  {dict(zip(col_names, row))}")

conn.close()
