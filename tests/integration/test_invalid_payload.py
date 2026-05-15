import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_invalid_payload_rejection():
    """
    Guarantees that empty or structurally malformed data objects
    are cleanly blocked by our contract layer with a 422 error.
    """
    # Sending a completely blank payload to test boundary defenses
    response = client.post("/api/v1/neural/chat", json={})
    assert response.status_code == 422
