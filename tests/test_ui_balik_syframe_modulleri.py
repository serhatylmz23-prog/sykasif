from fastapi import FastAPI
from fastapi.testclient import TestClient

from syk_simulasyon.syk_ui import install_ui


def test_balik_rehberi_ve_syframe_modulleri():
    app = FastAPI()
    install_ui(app)

    client = TestClient(app)

    ekran = client.get("/syk-ui-screen")
    assert ekran.status_code == 200
    assert 'id="module-view"' in ekran.text
    assert "/syk-ui/css/module_views.css" in ekran.text
    assert "/syk-ui/js/module_views.js" in ekran.text

    css = client.get("/syk-ui/css/module_views.css")
    assert css.status_code == 200
    assert ".fish-grid" in css.text
    assert ".syframe-demo" in css.text

    javascript = client.get("/syk-ui/js/module_views.js")
    assert javascript.status_code == 200
    assert "TATLI SU BALIK REHBERİ" in javascript.text
    assert "SyFrame™" in javascript.text
    assert "fishView" in javascript.text
    assert "syframeView" in javascript.text
    assert javascript.text.count('["') >= 18

    app_js = client.get("/syk-ui/js/app.js")
    assert app_js.status_code == 200
    assert "SyKModuleViews" in app_js.text