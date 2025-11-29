#!/bin/bash
# Test and seed script for Docker environment

set -e

echo "🚀 Starting NEX Context Aggregator Test..."

# Start services
echo "1️⃣ Starting Docker services..."
docker-compose up -d db redis

# Wait for services to be ready
echo "2️⃣ Waiting for services to be ready..."
sleep 5

# Run migrations
echo "3️⃣ Running database migrations..."
docker-compose run --rm api alembic revision --autogenerate -m "initial_schema" || echo "Migration may already exist"
docker-compose run --rm api alembic upgrade head

# Run seed script
echo "4️⃣ Running seed script..."
docker-compose run --rm -e OPENAI_API_KEY="${OPENAI_API_KEY}" api python scripts/seed_demo.py

# Inspect data
echo "5️⃣ Inspecting generated data..."
docker-compose run --rm api python scripts/inspect_data.py

echo ""
echo "✅ Test complete!"
echo ""
echo "📊 View data: docker-compose run --rm api python scripts/inspect_data.py"
echo "🌐 API docs: http://localhost:8080/docs"

