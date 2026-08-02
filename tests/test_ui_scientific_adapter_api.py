from fastapi import FastAPI
from fastapi.testclient import TestClient

from syk_simulasyon.syk_ui import install_ui


def test_bilimsel_adapter_api():
    app = FastAPI()
    install_ui(app)

    client = TestClient(app)

    inventory = client.get(
        "/api/syk-ui/scientific-adapters"
    )

    assert inventory.status_code == 200
    assert len(inventory.json()) == 1
    assert inventory.json()[0]["id"] == "simulated"

    ingest = client.post(
        (
            "/api/syk-ui/scientific-adapters/"
            "simulated/modules/magnetometer/ingest"
        ),
        json={
            "live_value": 49125,
            "confidence": 95.8,
            "status": "verified",
            "source": "mag_test_device",
            "metadata": {
                "connection": "usb",
            },
        },
    )

    assert ingest.status_code == 200

    payload = ingest.json()

    assert payload["state"]["live_value"] == 49125
    assert payload["state"]["confidence"] == 95.8
    assert payload["state"]["status"] == "verified"
    assert payload["state"]["source"] == "mag_test_device"
    assert payload["adapter"]["id"] == "simulated"

    runtime = client.get(
        "/api/syk-ui/scientific-modules/magnetometer"
    )

    assert runtime.status_code == 200
    assert runtime.json()["state"]["live_value"] == 49125


def test_bilimsel_adapter_api_bilinmeyen_kayit():
    app = FastAPI()
    install_ui(app)

    client = TestClient(app)

    response = client.post(
        (
            "/api/syk-ui/scientific-adapters/"
            "unknown/modules/gpr/ingest"
        ),
        json={
            "live_value": 1,
        },
    )

    assert response.status_code == 404