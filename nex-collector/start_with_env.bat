@echo off
REM Helper script to copy OPENAI_API_KEY from root .env to nex-collector

echo 🔧 Setting up environment variables...

REM Check if root .env exists
if not exist "..\.env" (
    echo ❌ Root .env file not found at: %CD%\..\.env
    echo    Please create a .env file at the project root with OPENAI_API_KEY
    exit /b 1
)

REM Read OPENAI_API_KEY from root .env
for /f "tokens=2 delims==" %%a in ('findstr /C:"OPENAI_API_KEY" "..\.env"') do set OPENAI_API_KEY=%%a

if "%OPENAI_API_KEY%"=="" (
    echo ❌ OPENAI_API_KEY not found in root .env file
    echo    Please add: OPENAI_API_KEY=sk-...
    exit /b 1
)

echo ✅ Found OPENAI_API_KEY in root .env
echo.
echo Starting services with OPENAI_API_KEY from root .env...
echo.

REM Set environment variable and run docker-compose
set OPENAI_API_KEY=%OPENAI_API_KEY%
cd /d %~dp0
docker-compose up -d db redis

timeout /t 8 /nobreak >nul

docker-compose run --rm api alembic upgrade head 2>nul
if errorlevel 1 (
    echo    ⚠️  Creating initial migration...
    docker-compose run --rm api alembic revision --autogenerate -m "initial" 2>nul
    docker-compose run --rm api alembic upgrade head
)

docker-compose up -d api worker

echo.
echo ✅ Services started!
echo.
echo 📊 API: http://localhost:8080
echo 📚 Docs: http://localhost:8080/docs

