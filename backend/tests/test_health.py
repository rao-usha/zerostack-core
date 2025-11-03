"""Health endpoint tests."""
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add backend directory to path for imports
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from main import app


def test_health():
    """Test health endpoint returns expected response."""
    client = TestClient(app)
    response = client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "service" in data
    assert "database" in data
    # Status can be "healthy" or "degraded" depending on DB connection
    assert data["status"] in ["healthy", "degraded"]

