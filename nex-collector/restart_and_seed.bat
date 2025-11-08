@echo off
REM Restart and seed nex-collector with insurance underwriter context

echo 🔄 Restarting NEX Context Aggregator...

cd /d %~dp0

REM Stop existing services
echo.
echo 1️⃣ Stopping services...
docker-compose down

REM Wait a moment
timeout /t 2 /nobreak >nul

REM Start services
echo.
echo 2️⃣ Starting services...
docker-compose up -d redis
timeout /t 3 /nobreak >nul

REM Ensure database exists
echo.
echo 3️⃣ Ensuring database exists...
docker exec nex_db psql -U nex -d postgres -c "CREATE DATABASE nex_collector;" 2>nul || echo Database may already exist

REM Run migrations
echo.
echo 4️⃣ Running migrations...
docker-compose run --rm api alembic upgrade head

REM Start API and worker
echo.
echo 5️⃣ Starting API and Worker...
docker-compose up -d api worker

REM Wait for API to be ready
echo.
echo 6️⃣ Waiting for API to be ready...
timeout /t 5 /nobreak >nul

REM Check health
echo.
echo 7️⃣ Checking health...
curl -s http://localhost:8080/healthz | findstr "ok" >nul
if errorlevel 1 (
    echo ⚠️  API not ready yet, waiting a bit more...
    timeout /t 5 /nobreak >nul
)

REM Seed insurance underwriter context
echo.
echo 8️⃣ Seeding Insurance Underwriter context...
docker-compose run --rm -e API_BASE=http://api:8080 api python scripts/seed_insurance_underwriter.py

echo.
echo ✅ Done!
echo.
echo 📊 API: http://localhost:8080
echo 📚 Docs: http://localhost:8080/docs
echo 🔍 Query: http://localhost:8080/v1/contexts/variants?domain=insurance^&persona=underwriter

