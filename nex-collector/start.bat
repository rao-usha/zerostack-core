@echo off
REM Quick start script for NEX Context Aggregator

echo 🚀 Starting NEX Context Aggregator...

REM Check if Docker is running
docker ps >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker is not running. Please start Docker Desktop first.
    exit /b 1
)

REM Try to read OPENAI_API_KEY from root .env and set it
set OPENAI_API_KEY=
if exist "..\.env" (
    for /f "usebackq tokens=2 delims==" %%a in (`findstr /C:"OPENAI_API_KEY" "..\.env" 2^>nul`) do (
        set OPENAI_API_KEY=%%a
        goto :found
    )
)
:found
if "%OPENAI_API_KEY%"=="" (
    echo ⚠️  Warning: OPENAI_API_KEY not found in root .env
    echo    Set it with: $env:OPENAI_API_KEY = "sk-..."
    echo    Or create nex-collector\.env with: OPENAI_API_KEY=sk-...
) else (
    echo ✅ Found OPENAI_API_KEY from root .env
)

echo.
echo 1️⃣ Checking for main NEX database...
docker ps | findstr nex_db >nul
if errorlevel 1 (
    echo ⚠️  Main NEX database (nex_db) not found!
    echo    Please start main NEX first: docker-compose up -d db
    echo    Or start entire NEX: docker-compose up -d
    exit /b 1
)
echo ✅ Found main NEX database

echo.
echo 2️⃣ Creating nex_collector database (if needed)...
docker exec nex_db psql -U nex -d postgres -c "CREATE DATABASE nex_collector;" 2>nul || echo Database may already exist

echo.
echo 3️⃣ Starting Redis...
cd /d %~dp0
docker-compose up -d redis

echo.
echo 4️⃣ Waiting for services to be ready...
timeout /t 5 /nobreak >nul

echo.
echo 5️⃣ Running database migrations...
docker-compose run --rm api alembic upgrade head 2>nul
if errorlevel 1 (
    echo    ⚠️  No migrations found. Creating initial migration...
    docker-compose run --rm api alembic revision --autogenerate -m "initial" 2>nul
    docker-compose run --rm api alembic upgrade head
)

echo.
echo 6️⃣ Starting API and Worker...
docker-compose up -d api worker

echo.
echo ✅ NEX Context Aggregator is running!
echo.
echo 📊 API: http://localhost:8080
echo 📚 Docs: http://localhost:8080/docs
echo 🔍 Health: http://localhost:8080/healthz
echo.
echo 📁 Data Storage:
echo    - Database: Docker volume (nex-collector_pgdata)
echo    - Files: nex-collector\data\ (local directory)
echo.
echo To view logs:
echo   docker-compose logs -f
echo.
echo To stop:
echo   docker-compose down
