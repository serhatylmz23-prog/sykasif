from fastapi import FastAPI
from fastapi.testclient import TestClient

from syk_simulasyon.syk_ui import install_ui
from syk_simulasyon.syk_ui_runtime import api_routes
from syk_simulasyon.syk_ui_runtime.scientific_transport import (
    ScientificTransportPacket,
)


class FakeBleTransport:
    async def inventory(
        self,
        *,
        timeout: float,
    ):
        return [
            {
                "id": "ble:AA:BB:CC:DD:EE:FF",
                "title": "SYK PROBE BLE",
                "transport": "ble",
                "address": "AA:BB:CC:DD:EE:FF",
                "connected": False,
                "metadata": {
                    "rssi": -42,
                },
            }
        ]

    async def read_packet(
        self,
        *,
        address: str,
        characteristic_uuid: str,
        timeout: float,
    ):
        return ScientificTransportPacket(
            module_id="magnetometer",
            live_value=48990,
            confidence=94.7,
            status="verified",
            source="magnetometer_ble_device",
            metadata={
                "address": address,
                "characteristic_uuid": (
                    characteristic_uuid
                ),
            },
        )


def test_ble_cihaz_api(monkeypatch):
    monkeypatch.setattr(
        api_routes,
        "ble_transport",
        FakeBleTransport(),
    )

    app = FastAPI()
    install_ui(app)

    client = TestClient(app)

    devices = client.post(
        "/api/syk-ui/scientific-devices/ble/discover",
        json={
            "timeout": 4.0,
        },
    )

    assert devices.status_code == 200
    assert len(devices.json()) == 1
    assert (
        devices.json()[0]["address"]
        == "AA:BB:CC:DD:EE:FF"
    )

    reading = client.post(
        "/api/syk-ui/scientific-devices/ble/read",
        json={
            "address": "AA:BB:CC:DD:EE:FF",
            "characteristic_uuid": (
                "87654321-4321-6789-4321-0fedcba98765"
            ),
            "timeout": 5.0,
        },
    )

    assert reading.status_code == 200

    payload = reading.json()

    assert payload["state"]["live_value"] == 48990
    assert payload["state"]["confidence"] == 94.7
    assert payload["state"]["status"] == "verified"
    assert (
        payload["state"]["source"]
        == "magnetometer_ble_device"
    )