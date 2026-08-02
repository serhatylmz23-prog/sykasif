from fastapi import FastAPI
from fastapi.testclient import TestClient

from syk_simulasyon.syk_ui import install_ui
from syk_simulasyon.syk_ui_runtime import api_routes


class FakeHub:
    def inventory(self):
        return [
            {
                "id": "serial:COM7",
                "title": "SYK PROBE V2",
                "transport": "serial",
                "address": "COM7",
                "connected": False,
                "state": "discovered",
                "module_id": "gpr",
                "battery": 82.0,
                "signal_quality": 91.0,
                "firmware": "1.0.0",
                "last_packet_at": None,
                "metadata": {},
            }
        ]

    def transports(self):
        return [
            {
                "id": "serial",
                "title": "Seri",
                "discovery_supported": True,
                "read_supported": True,
            }
        ]

    async def refresh(
        self,
        *,
        ble_timeout: float,
    ):
        return {
            "devices": self.inventory(),
            "transports": self.transports(),
            "errors": {
                "serial": None,
                "ble": None,
                "tcp": None,
            },
        }

    def get(self, device_id: str):
        return self.inventory()[0]

    def set_connection(
        self,
        device_id: str,
        *,
        connected: bool,
    ):
        device = self.inventory()[0]
        device["connected"] = connected
        return device

    def update_telemetry(self, device_id: str, **kwargs):
        device = self.inventory()[0]
        device.update(kwargs)
        return device

    def register_manual(self, **kwargs):
        return {
            "id": kwargs["device_id"],
            "title": kwargs["title"],
            "transport": kwargs["transport"],
            "address": kwargs["address"],
        }


def test_device_hub_api(monkeypatch):
    monkeypatch.setattr(
        api_routes,
        "scientific_device_hub",
        FakeHub(),
    )

    app = FastAPI()
    install_ui(app)

    client = TestClient(app)

    inventory = client.get(
        "/api/syk-ui/device-hub"
    )

    assert inventory.status_code == 200
    assert len(inventory.json()["devices"]) == 1

    refresh = client.post(
        "/api/syk-ui/device-hub/refresh",
        json={"timeout": 4.0},
    )

    assert refresh.status_code == 200

    connection = client.patch(
        (
            "/api/syk-ui/device-hub/"
            "serial:COM7/connection"
        ),
        json={"connected": True},
    )

    assert connection.status_code == 200
    assert connection.json()["connected"] is True