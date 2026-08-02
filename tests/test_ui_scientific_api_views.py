from fastapi import FastAPI
from fastapi.testclient import TestClient

from syk_simulasyon.syk_ui import install_ui


def test_bilimsel_api_tabanli_tarayıcı_dosyaları():
    app = FastAPI()
    install_ui(app)

    client = TestClient(app)

    screen = client.get("/syk-ui-screen")
    assert screen.status_code == 200

    assert (
        "/syk-ui/js/scientific_api_views.js"
        in screen.text
    )

    javascript = client.get(
        "/syk-ui/js/scientific_api_views.js"
    )

    assert javascript.status_code == 200
    assert "SyKScientificApiViews" in javascript.text
    assert "scientific-modules" in javascript.text
    assert "new WebSocket" in javascript.text
    assert "CANLI RUNTIME BAĞLANTISI" in javascript.text

    module_views = client.get(
        "/syk-ui/js/module_views.js"
    )

    assert module_views.status_code == 200
    assert "SyKScientificApiViews" in module_views.text