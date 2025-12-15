@echo off
echo ========================================
echo ML Development Quick Setup (Windows)
echo ========================================
echo.

echo Step 1: Checking if tables exist...
docker exec -T nex-backend-dev python check_ml_tables.py
if errorlevel 1 (
    echo.
    echo Tables don't exist. Running migration...
    docker exec -T nex-backend-dev alembic upgrade head
    if errorlevel 1 (
        echo ERROR: Migration failed!
        pause
        exit /b 1
    )
)

echo.
echo Step 2: Seeding baseline recipes...
docker exec -T nex-backend-dev python scripts/seed_ml_recipes.py
if errorlevel 1 (
    echo ERROR: Seeding failed!
    pause
    exit /b 1
)

echo.
echo Step 3: Verifying setup...
docker exec -T nex-backend-dev python check_ml_tables.py

echo.
echo Step 4: Testing API endpoint...
curl http://localhost:8000/api/v1/ml-development/recipes

echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo Now:
echo 1. Refresh your browser at http://localhost:3000/model-development
echo 2. You should see 4 baseline recipes!
echo.
pause

