from fastapi.testclient import TestClient

from syk_simulasyon.runtime_ui_sunucusu import (
    app,
)


def test_kasif_ikon_api():
    client = TestClient(app)

    response = client.get(
        "/api/syk-ui/kasif-icons"
    )

    assert response.status_code == 200

    payload = response.json()

    assert (
        payload["icon_count"]
        == 27
    )


def test_kasif_asistan_profili_api():
    client = TestClient(app)

    response = client.get(
        "/api/syk-ui/kasif-icons/"
        "assistant"
    )

    assert response.status_code == 200

    payload = response.json()

    assert (
        payload["display_name"]
        == "Kaşif"
    )

    rules = payload[
        "icon"
    ]["visual_rules"]

    assert not rules[
        "face_visible"
    ]

    assert not rules[
        "headphones"
    ]


def test_tek_ikon_api():
    client = TestClient(app)

    response = client.get(
        "/api/syk-ui/kasif-icons/"
        "lidar"
    )

    assert response.status_code == 200

    assert (
        response.json()[
            "title"
        ]
        == "Lidar"
    )


def test_ikon_arama_api():
    client = TestClient(app)

    response = client.get(
        "/api/syk-ui/kasif-icons/"
        "search",
        params={
            "q": "kanıt",
        },
    )

    assert response.status_code == 200

    ids = {
        icon["icon_id"]
        for icon
        in response.json()[
            "icons"
        ]
    }

    assert "evidence" in ids