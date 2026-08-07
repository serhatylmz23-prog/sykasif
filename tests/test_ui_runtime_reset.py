from fastapi.testclient import TestClient

from syk_simulasyon.syk_ui_runtime.application import app


def test_ui_runtime_screen_200():
    client = TestClient(app)
    response = client.get("/syk-ui-screen")

    assert response.status_code == 200
    assert "SyKaşif Terminal V2" in response.text


def test_ui_runtime_health():
    client = TestClient(app)
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
