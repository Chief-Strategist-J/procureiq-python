import sys
import os
import pytest
from fastapi.testclient import TestClient

# Add src to python path
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))

from src.api.main import app
from src.infra.database import get_db

client = TestClient(app)

# Mock DB Session
class MockSession:
    def execute(self, query, params=None):
        class MockResult:
            def fetchall(self):
                # Return a mock resource row: (id, name, user_id, service_crew_id, resource_type, is_active)
                return [
                    (1, "Test Python Resource", 100, None, "technician", True)
                ]
        return MockResult()

def override_get_db():
    try:
        yield MockSession()
    finally:
        pass

# Register the override
app.dependency_overrides[get_db] = override_get_db

def test_get_candidates_endpoint():
    response = client.get("/api/v1/fieldservice/appointments/42/candidates")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["status"] == "success"
    assert json_data["code"] == 200
    
    candidates = json_data["data"]
    assert len(candidates) == 1
    assert candidates[0]["id"] == 1
    assert candidates[0]["name"] == "Test Python Resource"
    assert candidates[0]["resource_type"] == "technician"
    assert candidates[0]["is_active"] is True
