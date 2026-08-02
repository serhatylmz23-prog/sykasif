from fastapi import FastAPI
from fastapi.testclient import TestClient

from syk_simulasyon.syk_ui import install_ui
from syk_simulasyon.syk_ui_runtime import api_routes


class FakeDeviceManager:
    def transports(self):
        return [
            {
                "id": "serial",
                "title": "Seri",
                "discovery_supported": True,
                "read_supported": True,
            },
            {
                "id": "tcp",
                "title": "TCP",
                "discovery_supported": False,
                "read_supported": True,
            },
            {
                "id": "ble",
                "title": "BLE",
                "discovery_supported": True,
                "read_supported": True,
            },
        ]

    async def discover_all(
        self,
        *,
        ble_timeout: float,
    ):
        return {
            "transports": self.transports(),
            "devices": {
                "serial": [
                    {
                        "id": "serial:COM7",
                        "address": "COM7",
                    }
                ],
                "ble": [
                    {
                        "id": "ble:AA",
                        "address": "AA",
                    }
                ],
                "tcp": [],
            },
            "errors": {
                "serial": None,
                "ble": None,
                "tcp": None,
            },
        }


def test_bilimsel_cihaz_yonetici_api(monkeypatch):
    monkeypatch.setattr(
        api_routes,
        "scientific_device_manager",
        FakeDeviceManager(),
    )

    app = FastAPI()
    install_ui(app)

    client = TestClient(app)

    transports = client.get(
        "/api/syk-ui/scientific-devices/transports"
    )

    assert transports.status_code == 200
    assert len(transports.json()) == 3

    discovery = client.post(
        "/api/syk-ui/scientific-devices/discover",
        json={
            "timeout": 4.0,
        },
    )

    assert discovery.status_code == 200

    payload = discovery.json()

    assert len(payload["devices"]["serial"]) == 1
    assert len(payload["devices"]["ble"]) == 1
    assert payload["devices"]["tcp"] == []