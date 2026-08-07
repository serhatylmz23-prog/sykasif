from fastapi.testclient import TestClient

from terminal_v2.app.main import app


client = TestClient(app)


def test_pwa_module_detail_client_is_served():
    response = client.get(
        "/pwa/module_detail.js"
    )

    assert response.status_code == 200
    assert (
        "/api/v2/modul-katalogu"
        in response.text
    )
    assert (
        "window.SyKasifModuleDetail"
        in response.text
    )


def test_pwa_loads_module_detail_client():
    response = client.get("/pwa/")

    assert response.status_code == 200
    assert (
        "./module_detail.js"
        in response.text
    )


def test_module_detail_client_fetches_active_module():
    response = client.get(
        "/pwa/module_detail.js"
    )

    text = response.text

    assert "modulDetayiniGetir" in text
    assert "aktifModulDetayiniYukle" in text
    assert (
        "sykasif:aktif-modul-guncellendi"
        in text
    )
    assert "encodeURIComponent" in text


def test_module_detail_client_updates_panel():
    response = client.get(
        "/pwa/module_detail.js"
    )

    text = response.text

    assert '"modulBasligi"' in text
    assert '"modulAciklamasi"' in text
    assert '"islemAlani"' in text
    assert "modul.islemler" in text
    assert "modul-islem-butonu" in text


def test_module_detail_client_dispatches_ready_event():
    response = client.get(
        "/pwa/module_detail.js"
    )

    assert (
        "sykasif:modul-detayi-hazir"
        in response.text
    )
    assert "CustomEvent(" in response.text
