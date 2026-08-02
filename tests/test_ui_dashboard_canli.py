from fastapi import FastAPI
from fastapi.testclient import TestClient

from syk_simulasyon.syk_ui import install_ui


def test_ui_dashboard_ve_canli_websocket():
    app = FastAPI()
    install_ui(app)

    client = TestClient(app)

    screen = client.get("/syk-ui-screen")
    assert screen.status_code == 200
    assert 'id="right-panel"' not in screen.text
    assert 'class="right-panel"' in screen.text
    assert 'id="event-stream"' in screen.text
    assert 'id="map-stage"' in screen.text

    runtime = client.get("/api/syk-ui/runtime-state")
    assert runtime.status_code == 200

    payload = runtime.json()

    assert payload["active_module"]["id"] == "dashboard"
    assert len(payload["modules"]) == 27

    with client.websocket_connect("/api/syk-ui/live") as socket:
        live = socket.receive_json()

    assert live["connection"] == "live"
    assert live["active_module"]["id"] == "dashboard"
    assert len(live["modules"]) == 27

    javascript = client.get("/syk-ui/js/app.js")
    assert javascript.status_code == 200
    assert "connectLiveRuntime" in javascript.text
    assert "/api/syk-ui/live" in javascript.text