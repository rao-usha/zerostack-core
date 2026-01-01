# Nex Database Setup Script (PowerShell)
# This script initializes the Nex database from scratch with all migrations and seed data

Write-Host "🚀 Nex Database Setup Script" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# Database configuration
$DB_HOST = if ($env:EXPLORER_DB_HOST) { $env:EXPLORER_DB_HOST } else { "localhost" }
$DB_PORT = if ($env:EXPLORER_DB_PORT) { $env:EXPLORER_DB_PORT } else { "5432" }
$DB_USER = if ($env:EXPLORER_DB_USER) { $env:EXPLORER_DB_USER } else { "postgres" }
$DB_PASSWORD = if ($env:EXPLORER_DB_PASSWORD) { $env:EXPLORER_DB_PASSWORD } else { "postgres" }
$DB_NAME = if ($env:EXPLORER_DB_NAME) { $env:EXPLORER_DB_NAME } else { "nex" }

Write-Host "📋 Database Configuration:" -ForegroundColor Yellow
Write-Host "   Host: $DB_HOST"
Write-Host "   Port: $DB_PORT"
Write-Host "   User: $DB_USER"
Write-Host "   Database: $DB_NAME"
Write-Host ""

# Function to wait for PostgreSQL
function Wait-ForPostgres {
    Write-Host "⏳ Waiting for PostgreSQL to be ready..." -ForegroundColor Yellow
    
    $maxAttempts = 30
    $attempt = 0
    
    while ($attempt -lt $maxAttempts) {
        try {
            $env:PGPASSWORD = $DB_PASSWORD
            $result = & psql -h $DB_HOST -U $DB_USER -d postgres -c '\q' 2>&1
            if ($LASTEXITCODE -eq 0) {
                Write-Host "✓ PostgreSQL is ready!" -ForegroundColor Green
                return $true
            }
        } catch {
            # Connection failed, continue waiting
        }
        
        $attempt++
        Write-Host "   Attempt $attempt/$maxAttempts..."
        Start-Sleep -Seconds 1
    }
    
    Write-Host "❌ Failed to connect to PostgreSQL after $maxAttempts attempts" -ForegroundColor Red
    exit 1
}

# Function to create database
function New-NexDatabase {
    Write-Host ""
    Write-Host "🔨 Creating database '$DB_NAME' (if it doesn't exist)..." -ForegroundColor Yellow
    
    $env:PGPASSWORD = $DB_PASSWORD
    $dbExists = & psql -h $DB_HOST -U $DB_USER -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='$DB_NAME'" 2>&1
    
    if ($dbExists -eq "1") {
        Write-Host "✓ Database '$DB_NAME' already exists" -ForegroundColor Green
    } else {
        & psql -h $DB_HOST -U $DB_USER -d postgres -c "CREATE DATABASE $DB_NAME;" 2>&1 | Out-Null
        Write-Host "✓ Database '$DB_NAME' created successfully" -ForegroundColor Green
    }
}

# Function to run migrations
function Invoke-Migrations {
    Write-Host ""
    Write-Host "📦 Running Alembic migrations..." -ForegroundColor Yellow
    
    Write-Host "   Current migration status:"
    & alembic current
    
    Write-Host ""
    Write-Host "   Upgrading to latest version..."
    & alembic upgrade head
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "✓ Migrations completed successfully" -ForegroundColor Green
        
        Write-Host "   Final migration status:"
        & alembic current
    } else {
        Write-Host "❌ Migration failed" -ForegroundColor Red
        exit 1
    }
}

# Function to seed data
function Initialize-SeedData {
    Write-Host ""
    Write-Host "🌱 Seeding default prompt recipes..." -ForegroundColor Yellow
    
    & python scripts/seed_prompt_recipes.py
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Prompt recipes seeded successfully" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Warning: Seeding may have failed" -ForegroundColor Yellow
    }
}

# Function to show migration history
function Show-MigrationHistory {
    Write-Host ""
    Write-Host "📜 Migration History:" -ForegroundColor Cyan
    Write-Host "   ===================="
    & alembic history | Select-Object -First 20
}

# Main execution
try {
    Write-Host "Starting database setup process..." -ForegroundColor Cyan
    Write-Host ""
    
    # Step 1: Wait for PostgreSQL
    Wait-ForPostgres
    
    # Step 2: Create database
    New-NexDatabase
    
    # Step 3: Run migrations
    Invoke-Migrations
    
    # Step 4: Seed data
    Initialize-SeedData
    
    # Step 5: Show history
    Show-MigrationHistory
    
    Write-Host ""
    Write-Host "🎉 Database setup completed successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "📊 Summary:" -ForegroundColor Cyan
    Write-Host "   ✓ Database created: $DB_NAME" -ForegroundColor Green
    Write-Host "   ✓ All migrations applied" -ForegroundColor Green
    Write-Host "   ✓ Default prompt recipes seeded" -ForegroundColor Green
    Write-Host ""
    Write-Host "Your Nex database is ready to use! 🚀" -ForegroundColor Cyan
    
} catch {
    Write-Host ""
    Write-Host "❌ Setup failed: $_" -ForegroundColor Red
    exit 1
}









