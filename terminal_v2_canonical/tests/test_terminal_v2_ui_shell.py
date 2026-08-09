from fastapi.testclient import TestClient

from terminal_v2.app.main import app


client = TestClient(app)


def test_terminal_v2_index_is_html():
    response = client.get("/")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "SyKaşif Terminal V2" in response.text
    assert 'id="terminal-shell"' in response.text
    assert 'id="module-grid"' in response.text


def test_terminal_v2_status_endpoint():
    response = client.get("/api/v2/status")

    assert response.status_code == 200

    data = response.json()

    assert data["terminal"]["version"] == "2.0.0"
    assert data["runtime"]["port"] == 8013
    assert data["runtime"]["status"] == "ONLINE"
    assert "dashboard" in data["modules"]
    assert "notifications" in data["modules"]


def test_terminal_v2_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["terminal"] == "v2"
    assert data["port"] == 8013


def test_terminal_v2_static_assets():
    css_response = client.get("/static/css/main.css")
    js_response = client.get("/static/js/main.js")

    assert css_response.status_code == 200
    assert js_response.status_code == 200

    assert ".terminal-shell" in css_response.text
    assert "fetchStatus" in js_response.text
