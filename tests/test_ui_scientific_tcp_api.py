from fastapi import FastAPI
from fastapi.testclient import TestClient

from syk_simulasyon.syk_ui import install_ui
from syk_simulasyon.syk_ui_runtime import api_routes
from syk_simulasyon.syk_ui_runtime.scientific_transport import (
    ScientificTransportPacket,
)


class FakeTcpTransport:
    def read_packet(
        self,
        *,
        host: str,
        port: int,
        timeout: float,
    ):
        return ScientificTransportPacket(
            module_id="spectral",
            live_value=755.2,
            confidence=94.1,
            status="verified",
            source="spectral_tcp_device",
            metadata={
                "host": host,
                "port": port,
            },
        )


def test_tcp_cihaz_api(monkeypatch):
    monkeypatch.setattr(
        api_routes,
        "tcp_transport",
        FakeTcpTransport(),
    )

    app = FastAPI()
    install_ui(app)

    client = TestClient(app)

    response = client.post(
        "/api/syk-ui/scientific-devices/tcp/read",
        json={
            "host": "192.168.1.50",
            "port": 9100,
            "timeout": 3.0,
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["state"]["live_value"] == 755.2
    assert payload["state"]["confidence"] == 94.1
    assert payload["state"]["status"] == "verified"
    assert (
        payload["state"]["source"]
        == "spectral_tcp_device"
    )