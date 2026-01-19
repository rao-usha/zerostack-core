@echo off
REM Docker wrapper script to set up Nex database (Windows)
REM Run this from the project root

echo 🐳 Setting up Nex database via Docker...
echo.

REM Check if backend container is running
docker ps | findstr "nex-backend-dev" >nul
if errorlevel 1 (
    echo ⚠️  Backend container is not running. Starting services...
    docker-compose up -d
    echo ⏳ Waiting for services to initialize...
    timeout /t 5 /nobreak >nul
)

REM Run the setup script inside the backend container
docker exec -it nex-backend-dev bash /app/scripts/setup_database.sh

echo.
echo ✅ Setup complete! You can now use Nex.
pause









