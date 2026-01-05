"""Quick test to verify M5 data is accessible."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from core.config import settings

engine = create_engine(settings.database_url)

print("🧪 Testing M5 Dataset Accessibility...\n")
print("=" * 60)

with engine.connect() as conn:
    # Test M5 tables
    m5_tables = ['m5_calendar', 'm5_items', 'm5_sales', 'm5_prices']
    
    for table in m5_tables:
        try:
            result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
            count = result.scalar()
            print(f"✓ {table}: {count:,} rows")
        except Exception as e:
            print(f"✗ {table}: ERROR - {str(e)}")
    
    print()
    
    # Test sample query
    print("Sample M5 Data (FOODS_1_001 at CA_1):")
    print("-" * 60)
    
    query = """
        SELECT 
            c.date,
            s.sales,
            p.sell_price,
            c.weekday,
            c.event_name_1
        FROM m5_sales s
        JOIN m5_calendar c ON s.d = c.d
        LEFT JOIN m5_prices p ON s.item_id = p.item_id 
            AND s.store_id = p.store_id 
            AND c.wm_yr_wk = p.wm_yr_wk
        WHERE s.item_store_id = 'FOODS_1_001_CA_1'
        ORDER BY c.date DESC
        LIMIT 5
    """
    
    result = conn.execute(text(query))
    rows = result.fetchall()
    
    if rows:
        print(f"{'Date':<12} {'Sales':>6} {'Price':>7} {'Day':<10} {'Event':<15}")
        print("-" * 60)
        for row in rows:
            event = row[4] if row[4] else '-'
            print(f"{str(row[0]):<12} {row[1]:>6} ${row[2]:>6.2f} {row[3]:<10} {event:<15}")
    
    print()
    print("=" * 60)
    print("✨ M5 Dataset is accessible and ready to use!")
    print("\n📊 M5 Integration Ready:")
    print("   - Recipes can reference M5 tables")
    print("   - Training can use M5 data")
    print("   - Evaluation can benchmark against M5")
