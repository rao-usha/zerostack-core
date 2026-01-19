#!/bin/bash
# Nex Database Setup Script
# This script initializes the Nex database from scratch with all migrations and seed data

set -e  # Exit on error

echo "🚀 Nex Database Setup Script"
echo "================================"
echo ""

# Check if we're running inside Docker or locally
if [ -f /.dockerenv ]; then
    echo "✓ Running inside Docker container"
    IN_DOCKER=true
else
    echo "✓ Running locally"
    IN_DOCKER=false
fi

# Database configuration (from environment variables)
DB_HOST="${EXPLORER_DB_HOST:-localhost}"
DB_PORT="${EXPLORER_DB_PORT:-5432}"
DB_USER="${EXPLORER_DB_USER:-postgres}"
DB_PASSWORD="${EXPLORER_DB_PASSWORD:-postgres}"
DB_NAME="${EXPLORER_DB_NAME:-nex}"

echo ""
echo "📋 Database Configuration:"
echo "   Host: $DB_HOST"
echo "   Port: $DB_PORT"
echo "   User: $DB_USER"
echo "   Database: $DB_NAME"
echo ""

# Function to wait for PostgreSQL to be ready
wait_for_postgres() {
    echo "⏳ Waiting for PostgreSQL to be ready..."
    
    max_attempts=30
    attempt=0
    
    until PGPASSWORD=$DB_PASSWORD psql -h "$DB_HOST" -U "$DB_USER" -d postgres -c '\q' 2>/dev/null || [ $attempt -eq $max_attempts ]; do
        attempt=$((attempt + 1))
        echo "   Attempt $attempt/$max_attempts..."
        sleep 1
    done
    
    if [ $attempt -eq $max_attempts ]; then
        echo "❌ Failed to connect to PostgreSQL after $max_attempts attempts"
        exit 1
    fi
    
    echo "✓ PostgreSQL is ready!"
}

# Function to create database if it doesn't exist
create_database() {
    echo ""
    echo "🔨 Creating database '$DB_NAME' (if it doesn't exist)..."
    
    # Check if database exists
    DB_EXISTS=$(PGPASSWORD=$DB_PASSWORD psql -h "$DB_HOST" -U "$DB_USER" -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='$DB_NAME'")
    
    if [ "$DB_EXISTS" = "1" ]; then
        echo "✓ Database '$DB_NAME' already exists"
    else
        PGPASSWORD=$DB_PASSWORD psql -h "$DB_HOST" -U "$DB_USER" -d postgres -c "CREATE DATABASE $DB_NAME;"
        echo "✓ Database '$DB_NAME' created successfully"
    fi
}

# Function to run Alembic migrations
run_migrations() {
    echo ""
    echo "📦 Running Alembic migrations..."
    
    # Get current migration status
    echo "   Current migration status:"
    alembic current 2>&1 | sed 's/^/   /'
    
    echo ""
    echo "   Upgrading to latest version..."
    alembic upgrade head
    
    echo ""
    echo "✓ Migrations completed successfully"
    
    # Show final status
    echo "   Final migration status:"
    alembic current 2>&1 | sed 's/^/   /'
}

# Function to seed prompt recipes
seed_prompt_recipes() {
    echo ""
    echo "🌱 Seeding default prompt recipes..."
    
    python scripts/seed_prompt_recipes.py
    
    echo "✓ Prompt recipes seeded successfully"
}

# Function to display migration history
show_migration_history() {
    echo ""
    echo "📜 Migration History:"
    echo "   ===================="
    alembic history | head -20 | sed 's/^/   /'
}

# Main execution
main() {
    echo "Starting database setup process..."
    echo ""
    
    # Step 1: Wait for PostgreSQL
    wait_for_postgres
    
    # Step 2: Create database
    create_database
    
    # Step 3: Run migrations
    run_migrations
    
    # Step 4: Seed prompt recipes
    seed_prompt_recipes
    
    # Step 5: Show migration history
    show_migration_history
    
    echo ""
    echo "🎉 Database setup completed successfully!"
    echo ""
    echo "📊 Summary:"
    echo "   ✓ Database created: $DB_NAME"
    echo "   ✓ All migrations applied"
    echo "   ✓ Default prompt recipes seeded"
    echo ""
    echo "Your Nex database is ready to use! 🚀"
}

# Run main function
main









