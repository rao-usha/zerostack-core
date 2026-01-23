#!/usr/bin/env python3
"""Check nexdata database for M5 tables."""
import psycopg

try:
    conn = psycopg.connect(
        host='host.docker.internal',
        port=5433,
        user='nexdata',
        password='nexdata_dev_password',
        dbname='nexdata'
    )
    cur = conn.cursor()

    # List all tables
    cur.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        ORDER BY table_name
    """)
    tables = cur.fetchall()
    print('Tables in nexdata:')
    for t in tables:
        print(f'  - {t[0]}')

    # Check for M5-related tables
    m5_keywords = ['m5', 'sales', 'calendar', 'price', 'train', 'eval']
    m5_tables = [t[0] for t in tables if any(k in t[0].lower() for k in m5_keywords)]
    
    if m5_tables:
        print(f'\nPotential M5 tables:')
        for table in m5_tables:
            try:
                cur.execute(f'SELECT COUNT(*) FROM "{table}"')
                count = cur.fetchone()[0]
                print(f'  {table}: {count:,} rows')
            except Exception as e:
                print(f'  {table}: error - {e}')
    else:
        print('\nNo M5-related tables found')
        print('Looking for any table with data...')
        for t in tables[:10]:
            try:
                cur.execute(f'SELECT COUNT(*) FROM "{t[0]}"')
                count = cur.fetchone()[0]
                if count > 0:
                    print(f'  {t[0]}: {count:,} rows')
            except:
                pass

    conn.close()
    print('\n✅ Connection successful!')
    
except Exception as e:
    print(f'❌ Connection failed: {e}')
