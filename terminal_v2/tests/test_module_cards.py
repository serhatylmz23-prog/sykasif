from fastapi.testclient import TestClient

from terminal_v2.app.main import app


client = TestClient(app)


def setup_function():
    response = client.delete(
        "/api/v2/runtime-state"
    )
    assert response.status_code == 200


def test_module_card_routes_exist():
    paths = set(
        app.openapi().get("paths", {})
    )

    assert "/api/v2/modul-kartlari" in paths
    assert (
        "/api/v2/modul-kartlari/durum"
        in paths
    )


def test_module_cards_are_turkish():
    response = client.get(
        "/api/v2/modul-kartlari"
    )

    assert response.status_code == 200

    body = response.json()

    assert body["sonuc"] == "BASARILI"
    assert body["mesaj"] == (
        "Canlı modül kartları hazır."
    )
    assert len(body["kartlar"]) >= 7


def test_active_module_card_is_marked():
    client.post(
        "/api/v2/runtime-state/aktif-modul",
        json={
            "modul_kodu": "analiz",
            "kaynak": "masaustu",
        },
    )

    body = client.get(
        "/api/v2/modul-kartlari"
    ).json()

    analiz = next(
        kart
        for kart in body["kartlar"]
        if kart["kod"] == "analiz"
    )

    assert analiz["aktif"] is True
    assert analiz["durum_metni"] == "Çalışıyor"


def test_module_status_is_shared():
    response = client.post(
        "/api/v2/modul-kartlari/durum",
        json={
            "modul_kodu": "harita",
            "durum": "TARIYOR",
            "kaynak": "tablet",
        },
    )

    assert response.status_code == 200

    harita = next(
        kart
        for kart in response.json()["kartlar"]
        if kart["kod"] == "harita"
    )

    assert harita["durum_kodu"] == "TARIYOR"
    assert harita["durum_metni"] == "Tarıyor"
    assert harita["ikon_durumu"] == "tariyor"


def test_invalid_module_status_returns_422():
    response = client.post(
        "/api/v2/modul-kartlari/durum",
        json={
            "modul_kodu": "harita",
            "durum": "GECERSIZ",
            "kaynak": "test",
        },
    )

    assert response.status_code == 422
