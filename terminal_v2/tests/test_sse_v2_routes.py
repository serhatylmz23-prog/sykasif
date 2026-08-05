from fastapi.testclient import TestClient

from terminal_v2.app.main import app


client = TestClient(app)


def test_sse_snapshot_endpoint():
    response = client.get(
        "/api/v2/events/snapshot",
    )

    assert response.status_code == 200

    data = response.json()

    assert data["terminal"] == "v2"
    assert data["runtime"] == "ONLINE"
    assert data["transport"] == "SSE"
    assert data["port"] == 8013


def test_status_reports_sse_transport():
    response = client.get(
        "/api/v2/status",
    )

    assert response.status_code == 200

    data = response.json()

    assert data["connection"]["transport"] == "SSE"
    assert data["connection"]["stream"] == "ONLINE"
