from fastapi.testclient import TestClient

from terminal_v2.app.main import app


client = TestClient(app)


def setup_function():
    response = client.delete(
        "/api/v2/runtime-state"
    )
    assert response.status_code == 200


def kart(body, kod):
    return next(
        item
        for item in body["kartlar"]
        if item["kod"] == kod
    )


def test_active_module_route_exists():
    paths = set(
        app.openapi().get("paths", {})
    )

    assert (
        "/api/v2/modul-kartlari/aktif"
        in paths
    )


def test_harita_becomes_active():
    response = client.post(
        "/api/v2/modul-kartlari/aktif",
        json={
            "modul_kodu": "harita",
            "kaynak": "windows_masaustu",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["aktif_modul"] == "harita"
    assert kart(body, "harita")["aktif"] is True
    assert (
        kart(body, "harita")["durum_kodu"]
        == "CALISIYOR"
    )


def test_previous_module_returns_to_waiting():
    client.post(
        "/api/v2/modul-kartlari/aktif",
        json={
            "modul_kodu": "harita",
            "kaynak": "windows_masaustu",
        },
    )

    response = client.post(
        "/api/v2/modul-kartlari/aktif",
        json={
            "modul_kodu": "analiz",
            "kaynak": "windows_masaustu",
        },
    )

    body = response.json()

    assert kart(body, "analiz")["aktif"] is True
    assert (
        kart(body, "analiz")["durum_kodu"]
        == "CALISIYOR"
    )
    assert kart(body, "harita")["aktif"] is False
    assert (
        kart(body, "harita")["durum_kodu"]
        == "BEKLIYOR"
    )


def test_active_module_response_is_turkish():
    response = client.post(
        "/api/v2/modul-kartlari/aktif",
        json={
            "modul_kodu": "rapor",
            "kaynak": "windows_masaustu",
        },
    )

    body = response.json()

    assert body["sonuc"] == "BASARILI"
    assert body["mesaj"] == (
        "Canlı modül kartları hazır."
    )
