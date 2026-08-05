from fastapi.testclient import TestClient

from terminal_v2.app.main import app


client = TestClient(app)


def test_cleanup_connections_route():
    response = client.post(
        "/api/v2/connections/cleanup",
    )

    assert response.status_code == 200

    data = response.json()

    assert "removed_count" in data
    assert "removed_client_ids" in data
    assert "active_connections" in data


def test_health_reports_device_connections():
    response = client.get("/health")

    assert response.status_code == 200

    data = response.json()

    assert "active_tablet" in data
    assert "active_desktop" in data


def test_status_reports_device_metrics():
    response = client.get(
        "/api/v2/status",
    )

    assert response.status_code == 200

    connection = response.json()["connection"]

    assert "active_tablets" in connection
    assert "active_desktops" in connection
    assert connection["transport"] == "SSE"
