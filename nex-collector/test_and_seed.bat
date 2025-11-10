@echo off
REM Test and seed script for Windows

echo 🚀 Starting NEX Context Aggregator Test...

echo 1️⃣ Starting Docker services...
docker-compose up -d db redis

echo 2️⃣ Waiting for services to be ready...
timeout /t 5 /nobreak >nul

echo 3️⃣ Running database migrations...
docker-compose run --rm api alembic revision --autogenerate -m "initial_schema" || echo Migration may already exist
docker-compose run --rm api alembic upgrade head

echo 4️⃣ Running seed script...
docker-compose run --rm -e OPENAI_API_KEY=%OPENAI_API_KEY% api python scripts/seed_demo.py

echo 5️⃣ Inspecting generated data...
docker-compose run --rm api python scripts/inspect_data.py

echo.
echo ✅ Test complete!
echo.
echo 📊 View data: docker-compose run --rm api python scripts/inspect_data.py
echo 🌐 API docs: http://localhost:8080/docs

