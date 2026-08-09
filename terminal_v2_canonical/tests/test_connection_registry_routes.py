from fastapi.testclient import TestClient

from terminal_v2.app.main import app


client = TestClient(app)


def test_connections_endpoint():
    response = client.get(
        "/api/v2/connections",
    )

    assert response.status_code == 200

    data = response.json()

    assert "active_connections" in data
    assert "total_connections" in data
    assert "total_events" in data
    assert isinstance(data["clients"], list)


def test_status_contains_stream_metrics():
    response = client.get(
        "/api/v2/status",
    )

    assert response.status_code == 200

    connection = response.json()["connection"]

    assert connection["transport"] == "SSE"
    assert "active_streams" in connection
    assert "total_streams" in connection


def test_health_contains_connection_count():
    response = client.get("/health")

    assert response.status_code == 200
    assert "active_connections" in response.json()
