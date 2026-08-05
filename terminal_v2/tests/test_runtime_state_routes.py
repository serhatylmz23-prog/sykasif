from fastapi.testclient import TestClient

from terminal_v2.app.main import app


client = TestClient(app)


def setup_function():
    response = client.delete(
        "/api/v2/runtime-state"
    )

    assert response.status_code == 200


def test_runtime_state_routes_exist():
    paths = set(
        app.openapi().get("paths", {})
    )

    required = {
        "/api/v2/runtime-state",
        "/api/v2/runtime-state/sistem",
        "/api/v2/runtime-state/cihaz",
        "/api/v2/runtime-state/aktif-modul",
    }

    assert required.issubset(paths)


def test_runtime_state_snapshot_is_turkish():
    response = client.get(
        "/api/v2/runtime-state"
    )

    assert response.status_code == 200

    body = response.json()

    assert body["sonuc"] == "BASARILI"
    assert "mesaj" in body
    assert body["revision"] == 0


def test_tablet_connection_is_shared():
    response = client.post(
        "/api/v2/runtime-state/cihaz",
        json={
            "cihaz_turu": "tablet",
            "bagli": True,
            "kaynak": "tablet",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["sonuc"] == "BASARILI"
    assert body["revision"] == 1
    assert (
        body["durum"]["cihazlar"]["tablet"]["bagli"]
        is True
    )
    assert (
        body["yayin"]["type"]
        == "runtime_durumu_guncellendi"
    )


def test_phone_connection_is_shared():
    response = client.post(
        "/api/v2/runtime-state/cihaz",
        json={
            "cihaz_turu": "telefon",
            "bagli": True,
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert (
        body["durum"]["cihazlar"]["telefon"]["durum"]
        == "CALISIYOR"
    )


def test_active_module_is_shared():
    response = client.post(
        "/api/v2/runtime-state/aktif-modul",
        json={
            "modul_kodu": "analiz",
            "kaynak": "masaustu",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert (
        body["durum"]["aktif_modul"]
        == "analiz"
    )


def test_invalid_status_returns_422():
    response = client.post(
        "/api/v2/runtime-state/sistem",
        json={
            "durum": "GECERSIZ",
            "mesaj": "Geçersiz durum.",
            "kaynak": "test",
        },
    )

    assert response.status_code == 422
