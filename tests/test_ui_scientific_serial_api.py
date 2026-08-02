from fastapi import FastAPI
from fastapi.testclient import TestClient

from syk_simulasyon.syk_ui import install_ui
from syk_simulasyon.syk_ui_runtime import api_routes


class FakeSerialTransport:
    def inventory(self):
        return [
            {
                "id": "serial:COM7",
                "title": "SYK PROBE V2",
                "transport": "serial",
                "address": "COM7",
                "connected": False,
                "metadata": {},
            }
        ]

    def read_packet(
        self,
        *,
        port: str,
        baud_rate: int,
        timeout: float,
    ):
        from syk_simulasyon.syk_ui_runtime.scientific_transport import (
            ScientificTransportPacket,
        )

        return ScientificTransportPacket(
            module_id="thermal",
            live_value=28.4,
            confidence=93.2,
            status="verified",
            source="thermal_serial_device",
            metadata={
                "port": port,
                "baud_rate": baud_rate,
            },
        )


def test_seri_cihaz_api(monkeypatch):
    monkeypatch.setattr(
        api_routes,
        "serial_transport",
        FakeSerialTransport(),
    )

    app = FastAPI()
    install_ui(app)

    client = TestClient(app)

    devices = client.get(
        "/api/syk-ui/scientific-devices/serial"
    )

    assert devices.status_code == 200
    assert len(devices.json()) == 1
    assert devices.json()[0]["address"] == "COM7"

    reading = client.post(
        "/api/syk-ui/scientific-devices/serial/read",
        json={
            "port": "COM7",
            "baud_rate": 115200,
            "timeout": 2.0,
        },
    )

    assert reading.status_code == 200

    payload = reading.json()

    assert payload["state"]["live_value"] == 28.4
    assert payload["state"]["confidence"] == 93.2
    assert payload["state"]["status"] == "verified"
    assert (
        payload["state"]["source"]
        == "thermal_serial_device"
    )