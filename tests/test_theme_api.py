from fastapi.testclient import TestClient

from syk_simulasyon.runtime_ui_sunucusu import app


def test_tema_api():
    client = TestClient(app)

    themes = client.get(
        "/api/syk-ui/themes"
    )

    assert themes.status_code == 200

    selected = client.put(
        "/api/syk-ui/themes/current",
        json={
            "theme_id": "silver",
        },
    )

    assert selected.status_code == 200

    assert selected.json()["active"][
        "id"
    ] == "silver"


def test_otomatik_tema_api():
    client = TestClient(app)

    response = client.post(
        "/api/syk-ui/themes/automatic",
        json={
            "hour": 12,
            "weather": "storm",
            "device": "desktop",
        },
    )

    assert response.status_code == 200

    assert response.json()["active"][
        "id"
    ] == "dark"