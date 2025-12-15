#!/bin/bash

# Setup script for ML Model Development feature
# This script runs the migration and seeds the baseline recipes

set -e

echo "================================================"
echo "  ML Model Development - Setup Script"
echo "================================================"
echo ""

# Check if we're in the project root
if [ ! -d "backend" ] || [ ! -d "frontend" ]; then
    echo "❌ Error: This script must be run from the project root directory"
    exit 1
fi

echo "Step 1/3: Running database migration..."
cd backend
alembic upgrade head
echo "✅ Migration completed"
echo ""

echo "Step 2/3: Seeding baseline ML recipes..."
python scripts/seed_ml_recipes.py
echo "✅ Seed data loaded"
echo ""

echo "Step 3/3: Verifying setup..."
# Check if tables exist
python -c "
from sqlalchemy import create_engine, inspect
from core.config import settings

engine = create_engine(settings.database_url)
inspector = inspect(engine)
tables = inspector.get_table_names()

required_tables = ['ml_recipe', 'ml_recipe_version', 'ml_model', 'ml_run', 'ml_monitor_snapshot', 'ml_synthetic_example']
missing = [t for t in required_tables if t not in tables]

if missing:
    print(f'❌ Missing tables: {missing}')
    exit(1)
else:
    print('✅ All tables verified')
"
echo ""

cd ..

echo "================================================"
echo "  Setup Complete! 🎉"
echo "================================================"
echo ""
echo "Next steps:"
echo "1. Start the backend:  cd backend && uvicorn main:app --reload"
echo "2. Start the frontend: cd frontend && npm run dev"
echo "3. Navigate to /model-development in the app"
echo ""
echo "See docs/ML_MODEL_DEVELOPMENT.md for usage guide"
echo ""


