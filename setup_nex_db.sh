#!/bin/bash
# Docker wrapper script to set up Nex database
# Run this from the project root on your host machine

echo "🐳 Setting up Nex database via Docker..."
echo ""

# Check if backend container is running
if ! docker ps | grep -q nex-backend-dev; then
    echo "⚠️  Backend container is not running. Starting services..."
    docker-compose up -d
    echo "⏳ Waiting for services to initialize..."
    sleep 5
fi

# Run the setup script inside the backend container
docker exec -it nex-backend-dev bash /app/scripts/setup_database.sh

echo ""
echo "✅ Setup complete! You can now use Nex."



