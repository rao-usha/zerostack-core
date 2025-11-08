#!/bin/bash
# Quick start script for NEX Context Aggregator

set -e

echo "🚀 Starting NEX Context Aggregator..."

# Check if Docker is running
if ! docker ps > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

echo ""
echo "1️⃣ Starting database and Redis..."
docker-compose -f nex-collector/docker-compose.yml up -d db redis

echo ""
echo "2️⃣ Waiting for services to be ready..."
sleep 5

echo ""
echo "3️⃣ Running database migrations..."
if ! docker-compose -f nex-collector/docker-compose.yml run --rm api alembic upgrade head 2>/dev/null; then
    echo "   ⚠️  No migrations found. Creating initial migration..."
    docker-compose -f nex-collector/docker-compose.yml run --rm api alembic revision --autogenerate -m "initial" 2>/dev/null || true
    docker-compose -f nex-collector/docker-compose.yml run --rm api alembic upgrade head
fi

echo ""
echo "4️⃣ Starting API and Worker..."
docker-compose -f nex-collector/docker-compose.yml up -d api worker

echo ""
echo "✅ NEX Context Aggregator is running!"
echo ""
echo "📊 API: http://localhost:8080"
echo "📚 Docs: http://localhost:8080/docs"
echo "🔍 Health: http://localhost:8080/healthz"
echo ""
echo "To view logs:"
echo "  docker-compose -f nex-collector/docker-compose.yml logs -f"
echo ""
echo "To stop:"
echo "  docker-compose -f nex-collector/docker-compose.yml down"

