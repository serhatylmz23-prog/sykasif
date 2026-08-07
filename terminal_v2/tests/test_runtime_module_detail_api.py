from fastapi.testclient import TestClient

from terminal_v2.app.main import app


client = TestClient(app)


def test_module_detail_api_returns_requested_module():
    response = client.get(
        "/api/v2/modul-katalogu/harita"
    )

    assert response.status_code == 200

    veri = response.json()

    assert veri["kod"] == "harita"
    assert veri["baslik"] == "Canl\u0131 Harita"
    assert veri["islemler"]


def test_module_detail_api_returns_dashboard_fallback():
    response = client.get(
        "/api/v2/modul-katalogu/bilinmeyen"
    )

    assert response.status_code == 200

    veri = response.json()

    assert veri["kod"] == "dashboard"


def test_module_detail_api_has_turkish_content():
    response = client.get(
        "/api/v2/modul-katalogu/rapor"
    )

    veri = response.json()

    assert veri["ad"] == "Rapor"
    assert "M\u00fch\u00fcrl\u00fc" in veri["aciklama"]
    assert (
        "Yeni rapor olu\u015ftur"
        in veri["islemler"]
    )
