"""Quick script to check if ML tables exist."""
import sys
from sqlalchemy import create_engine, inspect, text
from core.config import settings

def check_tables():
    """Check if ML development tables exist."""
    try:
        engine = create_engine(settings.database_url)
        inspector = inspect(engine)
        all_tables = inspector.get_table_names()
        
        required_tables = [
            'ml_recipe',
            'ml_recipe_version', 
            'ml_model',
            'ml_run',
            'ml_monitor_snapshot',
            'ml_synthetic_example'
        ]
        
        print("Checking ML Development tables...")
        print("-" * 50)
        
        missing = []
        for table in required_tables:
            exists = table in all_tables
            status = "✓" if exists else "✗"
            print(f"{status} {table}")
            if not exists:
                missing.append(table)
        
        print("-" * 50)
        
        if missing:
            print(f"\n❌ Missing {len(missing)} tables: {', '.join(missing)}")
            print("\nTo fix this, run:")
            print("1. cd backend")
            print("2. alembic upgrade head")
            print("3. python scripts/seed_ml_recipes.py")
            return False
        else:
            print("\n✅ All ML tables exist!")
            
            # Check if we have seed data
            with engine.connect() as conn:
                result = conn.execute(text("SELECT COUNT(*) FROM ml_recipe"))
                count = result.scalar()
                print(f"\nRecipes in database: {count}")
                
                if count == 0:
                    print("\n⚠️  No recipes found. Run seed script:")
                    print("   python scripts/seed_ml_recipes.py")
                else:
                    print("✅ Seed data exists!")
            
            return True
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure:")
        print("1. Database is running")
        print("2. DATABASE_URL is correctly set in .env")
        return False

if __name__ == "__main__":
    success = check_tables()
    sys.exit(0 if success else 1)

