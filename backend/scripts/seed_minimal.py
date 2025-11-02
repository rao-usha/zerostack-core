"""Seed database with minimal test data."""
import uuid
import sys
from pathlib import Path

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine
from backend.core.config import settings
from backend.db.meta import METADATA
from backend.db import models


def seed():
    """Seed database with minimal test data."""
    engine = create_engine(settings.database_url)
    
    # Create all tables if they don't exist
    METADATA.create_all(engine)
    
    with engine.begin() as conn:
        # Create a demo org
        demo_org_id = uuid.uuid4()
        conn.execute(
            models.orgs.insert().values(
                id=demo_org_id,
                name="Demo Org"
            )
        )
        
        # Create a demo user
        demo_user_id = uuid.uuid4()
        conn.execute(
            models.users.insert().values(
                id=demo_user_id,
                org_id=demo_org_id,
                email="demo@nex.ai",
                role="admin"
            )
        )
        
        print(f"✓ Created demo org: {demo_org_id} (Demo Org)")
        print(f"✓ Created demo user: {demo_user_id} (demo@nex.ai)")
        print("✓ Database seeded successfully!")


if __name__ == "__main__":
    seed()

