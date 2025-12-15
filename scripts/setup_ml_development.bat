@echo off
REM Setup script for ML Model Development feature (Windows)
REM This script runs the migration and seeds the baseline recipes

echo ================================================
echo   ML Model Development - Setup Script
echo ================================================
echo.

REM Check if we're in the project root
if not exist "backend\" (
    echo Error: This script must be run from the project root directory
    exit /b 1
)
if not exist "frontend\" (
    echo Error: This script must be run from the project root directory
    exit /b 1
)

echo Step 1/3: Running database migration...
cd backend
call alembic upgrade head
if errorlevel 1 (
    echo Migration failed!
    exit /b 1
)
echo Migration completed
echo.

echo Step 2/3: Seeding baseline ML recipes...
python scripts\seed_ml_recipes.py
if errorlevel 1 (
    echo Seeding failed!
    exit /b 1
)
echo Seed data loaded
echo.

echo Step 3/3: Verifying setup...
python -c "from sqlalchemy import create_engine, inspect; from core.config import settings; engine = create_engine(settings.database_url); inspector = inspect(engine); tables = inspector.get_table_names(); required_tables = ['ml_recipe', 'ml_recipe_version', 'ml_model', 'ml_run', 'ml_monitor_snapshot', 'ml_synthetic_example']; missing = [t for t in required_tables if t not in tables]; exit(1) if missing else print('All tables verified')"
if errorlevel 1 (
    echo Verification failed!
    exit /b 1
)
echo.

cd ..

echo ================================================
echo   Setup Complete!
echo ================================================
echo.
echo Next steps:
echo 1. Start the backend:  cd backend ^&^& uvicorn main:app --reload
echo 2. Start the frontend: cd frontend ^&^& npm run dev
echo 3. Navigate to /model-development in the app
echo.
echo See docs\ML_MODEL_DEVELOPMENT.md for usage guide
echo.


