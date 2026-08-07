from fastapi.testclient import TestClient

from terminal_v2.app.main import app


client = TestClient(app)


def test_pwa_has_live_module_card_area():
    response = client.get("/pwa/")

    assert response.status_code == 200
    assert 'id="modulKartlari"' in response.text
    assert 'id="canliModullerBasligi"' in response.text


def test_pwa_builds_cards_from_shared_catalog():
    response = client.get(
        "/pwa/pwa.js"
    )

    assert response.status_code == 200
    assert "modulKartlariniOlustur" in response.text
    assert "durum.moduller" in response.text
    assert "data-modul-kodu" in response.text


def test_pwa_marks_active_module_card():
    response = client.get(
        "/pwa/pwa.js"
    )

    assert "aktifModulKodunuGetir" in response.text
    assert 'classList.toggle(' in response.text
    assert '"aktif"' in response.text
    assert '"?al???yor"' in response.text
    assert '"Bekliyor"' in response.text


def test_pwa_live_cards_dispatch_binding_event():
    response = client.get(
        "/pwa/pwa.js"
    )

    assert (
        "sykasif:modul-kartlari-yenilendi"
        in response.text
    )
    assert "CustomEvent(" in response.text


def test_pwa_live_cards_are_responsive():
    response = client.get(
        "/pwa/pwa.css"
    )

    assert ".modul-kartlari" in response.text
    assert ".modul-karti.aktif" in response.text
    assert "@media (max-width: 640px)" in response.text
