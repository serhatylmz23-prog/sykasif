from fastapi import FastAPI
from fastapi.testclient import TestClient

from syk_simulasyon.syk_ui import install_ui


def test_device_hub_tarayıcı_dosyalari():
    app = FastAPI()
    install_ui(app)

    client = TestClient(app)

    screen = client.get("/syk-ui-screen")

    assert screen.status_code == 200
    assert "/syk-ui/css/device_hub.css" in screen.text
    assert "/syk-ui/js/device_hub.js" in screen.text

    css = client.get(
        "/syk-ui/css/device_hub.css"
    )

    assert css.status_code == 200
    assert ".device-hub" in css.text
    assert ".device-card" in css.text

    javascript = client.get(
        "/syk-ui/js/device_hub.js"
    )

    assert javascript.status_code == 200
    assert "SyKDeviceHub" in javascript.text
    assert "Cihazları Tara" in javascript.text
    assert "/api/syk-ui/device-hub" in javascript.text

    module_views = client.get(
        "/syk-ui/js/module_views.js"
    )

    assert module_views.status_code == 200
    assert "SyKDeviceHub" in module_views.text