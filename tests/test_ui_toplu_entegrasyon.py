from fastapi import FastAPI
from fastapi.testclient import TestClient

from syk_simulasyon.syk_ui import install_ui


def test_ui_toplu_entegrasyon():
    app = FastAPI()
    install_ui(app)

    client = TestClient(app)

    screen = client.get("/syk-ui-screen")
    assert screen.status_code == 200
    assert "SyKaşif" in screen.text
    assert "/syk-ui/css/app.css" in screen.text
    assert "/syk-ui/js/app.js" in screen.text

    css = client.get("/syk-ui/css/app.css")
    assert css.status_code == 200
    assert ".syframe" in css.text

    javascript = client.get("/syk-ui/js/app.js")
    assert javascript.status_code == 200
    assert "loadRuntime" in javascript.text

    runtime = client.get("/api/syk-ui/runtime-state")
    assert runtime.status_code == 200
    assert runtime.json()["active_module"]["id"] == "dashboard"