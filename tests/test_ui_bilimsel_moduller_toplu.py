from fastapi import FastAPI
from fastapi.testclient import TestClient

from syk_simulasyon.syk_ui import install_ui


SCIENTIFIC_MODULES = {
    "geology",
    "frequency",
    "lidar",
    "astronomy",
    "chemistry",
    "spectral",
    "thermal",
    "magnetometer",
    "gravimeter",
    "ert",
    "gpr",
    "seismic",
    "hydro",
    "botany",
    "soil",
    "water",
}


def test_bilimsel_modul_ekranlari_toplu_kodlandi():
    app = FastAPI()
    install_ui(app)

    client = TestClient(app)

    screen = client.get("/syk-ui-screen")
    assert screen.status_code == 200
    assert "/syk-ui/css/scientific_views.css" in screen.text
    assert "/syk-ui/js/scientific_views.js" in screen.text

    css = client.get("/syk-ui/css/scientific_views.css")
    assert css.status_code == 200
    assert ".scientific-screen" in css.text
    assert ".scientific-scan" in css.text
    assert ".scientific-metrics" in css.text

    javascript = client.get("/syk-ui/js/scientific_views.js")
    assert javascript.status_code == 200

    for module_id in SCIENTIFIC_MODULES:
        assert f"{module_id}:" in javascript.text

    assert "Bu ekran gerçek saha sonucu değildir." in javascript.text
    assert "SyKScientificViews" in javascript.text

    module_views = client.get("/syk-ui/js/module_views.js")
    assert module_views.status_code == 200
    assert "SyKScientificViews" in module_views.text