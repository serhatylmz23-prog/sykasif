from fastapi.testclient import TestClient

from terminal_v2.app.main import app


client = TestClient(app)


def test_runtime_metrics_route():
    response = client.get(
        "/api/v2/events/metrics",
    )

    assert response.status_code == 200

    data = response.json()

    assert data["type"] == "metrics"
    assert data["runtime"] == "ONLINE"
    assert data["stream"] == "ONLINE"
    assert "active_connections" in data


def test_live_runtime_asset():
    response = client.get(
        "/static/js/live_runtime.js",
    )

    assert response.status_code == 200
    assert "terminal.metrics" in response.text
    assert "EventSource" in response.text


def test_live_runtime_script_is_loaded():
    response = client.get("/")

    assert response.status_code == 200

    assert (
        "/static/js/live_runtime.js"
        in response.text
    )
