from fastapi.testclient import TestClient

from syk_simulasyon.runtime_ui_sunucusu import app


def test_ui_mevcut_fastapi_sunucusuna_baglanir():
    client = TestClient(app)

    ekran = client.get("/syk-ui-screen")
    assert ekran.status_code == 200
    assert "SyKaşif" in ekran.text

    durum = client.get("/api/syk-ui/runtime-state")
    assert durum.status_code == 200
    assert durum.json()["active_module"]["id"] == "dashboard"

    css = client.get("/syk-ui/css/app.css")
    assert css.status_code == 200

    javascript = client.get("/syk-ui/js/app.js")
    assert javascript.status_code == 200


def test_ui_rotalari_ardisik_cagrilarda_kararlidir():
    client = TestClient(app)

    ilk_ekran = client.get("/syk-ui-screen")
    ikinci_ekran = client.get("/syk-ui-screen")

    assert ilk_ekran.status_code == 200
    assert ikinci_ekran.status_code == 200
    assert ilk_ekran.text == ikinci_ekran.text

    ilk_durum = client.get("/api/syk-ui/runtime-state")
    ikinci_durum = client.get("/api/syk-ui/runtime-state")

    assert ilk_durum.status_code == 200
    assert ikinci_durum.status_code == 200
    assert ilk_durum.json() == ikinci_durum.json()