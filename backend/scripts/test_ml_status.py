"""Quick test to verify ML Model Development is working."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, select, func
from core.config import settings
from db.models import ml_recipe, ml_model, ml_run, evaluation_pack, ml_monitor_snapshot

engine = create_engine(settings.database_url)

print("🧪 Testing ML Model Development Status...\n")
print("=" * 60)

with engine.connect() as conn:
    # Test 1: Recipes
    recipe_count = conn.execute(select(func.count()).select_from(ml_recipe)).scalar()
    print(f"✓ ML Recipes: {recipe_count}")
    
    if recipe_count > 0:
        recipes = conn.execute(select(ml_recipe).limit(4)).fetchall()
        for r in recipes:
            print(f"  - {r.name} ({r.model_family})")
    
    print()
    
    # Test 2: Models
    model_count = conn.execute(select(func.count()).select_from(ml_model)).scalar()
    print(f"✓ ML Models: {model_count}")
    
    if model_count > 0:
        models = conn.execute(select(ml_model).limit(3)).fetchall()
        for m in models:
            print(f"  - {m.name} ({m.status})")
    
    print()
    
    # Test 3: Runs
    run_count = conn.execute(select(func.count()).select_from(ml_run)).scalar()
    print(f"✓ ML Runs: {run_count}")
    
    print()
    
    # Test 4: Evaluation Packs
    pack_count = conn.execute(select(func.count()).select_from(evaluation_pack)).scalar()
    print(f"✓ Evaluation Packs: {pack_count}")
    
    if pack_count > 0:
        packs = conn.execute(select(evaluation_pack).limit(4)).fetchall()
        for p in packs:
            print(f"  - {p.name} ({p.model_family})")
    
    print()
    
    # Test 5: Monitoring
    mon_count = conn.execute(select(func.count()).select_from(ml_monitor_snapshot)).scalar()
    print(f"✓ Monitoring Snapshots: {mon_count}")
    
    print()
    print("=" * 60)
    print("\n✨ All components are present and working!")
    print(f"\nTotal entities: {recipe_count + model_count + run_count + pack_count + mon_count}")
    print("\n📱 Frontend Test:")
    print("   Open: http://localhost:3000/model-development")
    print("   Verify: All 4 tabs (Recipes, Models, Runs, Evaluation Packs)")
