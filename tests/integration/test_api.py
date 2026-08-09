from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_root_endpoint():
    response = client.get("/")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "online"
    assert data["service"] == "Atlas AI Financial Assistant"


def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "healthy"


def test_ready_endpoint():
    response = client.get("/ready")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] in {
        "ready",
        "not_ready",
    }

    assert data["database"] in {
        "connected",
        "unavailable",
    }