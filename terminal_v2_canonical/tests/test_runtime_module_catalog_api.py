from fastapi.testclient import TestClient

from terminal_v2.app.main import app


client = TestClient(app)


def test_module_catalog_api():
    response = client.get(
        "/api/v2/modul-katalogu"
    )

    assert response.status_code == 200

    veri = response.json()

    assert isinstance(veri, list)
    assert len(veri) > 0

    kodlar = {
        item["kod"]
        for item in veri
    }

    assert {
        "dashboard",
        "harita",
        "kanit",
        "analiz",
        "gorev",
        "rapor",
        "sensorler",
    }.issubset(kodlar)
