#!/usr/bin/env python3
"""Quick test script."""
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

print("🧪 Testing NEX Context Aggregator...")
print()

# Check environment
print("1️⃣ Checking environment...")
from app.config import settings

if not settings.OPENAI_API_KEY:
    print("   ⚠️  OPENAI_API_KEY not set - some features will be disabled")
else:
    print("   ✓ OPENAI_API_KEY set")

print(f"   ✓ DATABASE_URL: {settings.DATABASE_URL[:50]}...")
print(f"   ✓ REDIS_URL: {settings.REDIS_URL}")
print(f"   ✓ DATA_DIR: {settings.DATA_DIR}")
print()

# Test database connection
print("2️⃣ Testing database connection...")
try:
    from app.db import SessionLocal
    db = SessionLocal()
    db.execute("SELECT 1")
    db.close()
    print("   ✓ Database connection successful")
except Exception as e:
    print(f"   ❌ Database connection failed: {e}")
    sys.exit(1)
print()

# Test Redis connection
print("3️⃣ Testing Redis connection...")
try:
    from redis import Redis
    redis = Redis.from_url(settings.REDIS_URL)
    redis.ping()
    print("   ✓ Redis connection successful")
except Exception as e:
    print(f"   ⚠️  Redis connection failed: {e}")
    print("   (Worker jobs will not work without Redis)")
print()

# Test imports
print("4️⃣ Testing imports...")
try:
    from app.models import ContextDoc, ContextVariant
    from app.ingest.generator import ContextGenerator
    from app.distill.sampler import ExampleSampler
    print("   ✓ All imports successful")
except Exception as e:
    print(f"   ❌ Import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
print()

print("✅ Basic tests passed!")
print()
print("Next steps:")
print("  1. Run migrations: alembic revision --autogenerate -m 'init' && alembic upgrade head")
print("  2. Run seed script: python scripts/seed_demo.py")
print("  3. Inspect data: python scripts/inspect_data.py")

