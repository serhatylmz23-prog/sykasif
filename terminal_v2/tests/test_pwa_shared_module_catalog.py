from fastapi.testclient import TestClient

from terminal_v2.app.main import app


client = TestClient(app)


def test_pwa_shared_catalog_script_is_served():
    response = client.get(
        "/pwa/module_catalog.js"
    )

    assert response.status_code == 200
    assert (
        "/api/v2/modul-katalogu"
        in response.text
    )
    assert (
        "window.SyKasifModuleCatalog"
        in response.text
    )


def test_pwa_loads_catalog_before_main_script():
    response = client.get("/pwa/")

    assert response.status_code == 200

    catalog_index = response.text.index(
        "./module_catalog.js"
    )
    pwa_index = response.text.index(
        "./pwa.js"
    )

    assert catalog_index < pwa_index


def test_pwa_catalog_api_returns_shared_modules():
    response = client.get(
        "/api/v2/modul-katalogu"
    )

    assert response.status_code == 200

    modules = response.json()

    codes = {
        module["kod"]
        for module in modules
    }

    assert {
        "dashboard",
        "harita",
        "kanit",
        "analiz",
        "gorev",
        "rapor",
        "sensorler",
    }.issubset(codes)


def test_pwa_catalog_has_live_events():
    response = client.get(
        "/pwa/module_catalog.js"
    )

    assert (
        "sykasif:modul-katalogu-hazir"
        in response.text
    )
    assert (
        "sykasif:modul-katalogu-hata"
        in response.text
    )
