from fastapi.testclient import TestClient

from syk_simulasyon.runtime_ui_sunucusu import (
    app,
)


def test_cevrimdisi_kuyruk_api():
    client = TestClient(app)

    response = client.post(
        "/api/syk-ui/mobile-offline/queue",
        json={
            "item_type": "evidence",
            "device_id": "PHONE-API-006C",
            "endpoint": (
                "/api/test/evidence"
            ),
            "method": "POST",
            "payload": {
                "evidence_id": (
                    "EVD-006C"
                )
            },
            "maximum_attempts": 5,
        },
    )

    assert response.status_code == 200

    assert response.json()[
        "created"
    ]


def test_eslestirme_api():
    client = TestClient(app)

    created = client.post(
        "/api/syk-ui/mobile-offline/"
        "pairings",
        json={
            "requesting_device_id": (
                "TABLET-PAIR-API-006C"
            ),
            "requesting_device_title": (
                "Saha Tableti"
            ),
            "target_role": (
                "trusted_terminal"
            ),
        },
    )

    assert created.status_code == 200

    pairing = created.json()

    confirmed = client.post(
        "/api/syk-ui/mobile-offline/"
        "pairings/confirm",
        json={
            "pairing_code": (
                pairing["pairing_code"]
            ),
            "paired_device_id": (
                "DESKTOP-PAIR-API-006C"
            ),
        },
    )

    assert confirmed.status_code == 200

    payload = confirmed.json()

    verified = client.post(
        "/api/syk-ui/mobile-offline/"
        "pairings/verify",
        json={
            "pairing_id": (
                pairing["pairing_id"]
            ),
            "pairing_token": (
                payload["pairing_token"]
            ),
        },
    )

    assert verified.status_code == 200

    assert verified.json()[
        "valid"
    ]


def test_onbellek_api():
    client = TestClient(app)

    response = client.put(
        "/api/syk-ui/mobile-offline/cache",
        json={
            "cache_key": (
                "report:RPT-006C"
            ),
            "category": "report",
            "value": {
                "report_id": (
                    "RPT-006C"
                ),
                "status": "ready",
            },
            "lifetime_seconds": 120,
        },
    )

    assert response.status_code == 200

    loaded = client.get(
        "/api/syk-ui/mobile-offline/"
        "cache/report:RPT-006C"
    )

    assert loaded.status_code == 200

    assert (
        loaded.json()[
            "value"
        ]["status"]
        == "ready"
    )