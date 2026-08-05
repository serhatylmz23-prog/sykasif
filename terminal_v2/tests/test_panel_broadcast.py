from fastapi.testclient import TestClient

from terminal_v2.app.main import app


client = TestClient(app)


def test_panel_broadcast_routes_exist():
    paths = set(
        app.openapi().get("paths", {})
    )

    required = {
        "/api/v2/panel/events",
        "/api/v2/panel/broadcast",
        "/api/v2/panel/broadcast/status",
    }

    assert required.issubset(paths)


def test_panel_broadcast_status_is_turkish():
    response = client.get(
        "/api/v2/panel/broadcast/status"
    )

    assert response.status_code == 200

    body = response.json()

    assert body["durum"] == "AKTIF"
    assert "mesaj" in body
    assert "bagli_istemci_sayisi" in body


def test_panel_event_can_be_broadcast():
    client.delete(
        "/api/v2/panel/state"
    )

    response = client.post(
        "/api/v2/panel/broadcast",
        json={
            "olay_turu": "YENI_KANIT",
            "kaynak": "tablet",
            "veri": {
                "kanit_kodu": "KANIT-001",
            },
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["sonuc"] == "YAYINLANDI"
    assert body["revision"] == 1
    assert (
        body["event"]["type"]
        == "panel_guncellendi"
    )


def test_panel_sse_route_is_registered():
    paths = set(
        app.openapi().get("paths", {})
    )

    assert "/api/v2/panel/events" in paths
