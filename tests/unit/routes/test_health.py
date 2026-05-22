from fastapi.testclient import TestClient

from main import app


def test_health_endpoint_reports_service_ok():
    response = TestClient(app).get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "sabipass-ai",
    }


def test_readiness_endpoint_checks_registry_and_demo_seed_data():
    response = TestClient(app).get("/ready")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ready"
    assert payload["checks"]["registry"] is True
    assert payload["checks"]["demo_seed_data"] is True
    assert payload["details"]["registry_version"] == "1.0"
