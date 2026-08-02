import json

import pytest

from syk_simulasyon.syk_ui_runtime.scientific_transport import (
    ScientificTransportError,
    TcpScientificTransport,
)


class FakeTcpBackend:
    def __init__(self, response: str) -> None:
        self.response = response

    def receive(
        self,
        host: str,
        port: int,
        timeout: float,
    ) -> str:
        assert host == "192.168.1.50"
        assert port == 9100
        assert timeout == 3.0

        return self.response


def test_tcp_json_paketi_okuma():
    response = json.dumps(
        {
            "module_id": "lidar",
            "live_value": "1.42M",
            "confidence": 95.4,
            "status": "verified",
            "source": "lidar_tcp_device",
            "metadata": {
                "device_id": "LDR-01",
            },
        }
    )

    transport = TcpScientificTransport(
        backend=FakeTcpBackend(response)
    )

    packet = transport.read_packet(
        host="192.168.1.50",
        port=9100,
        timeout=3.0,
    )

    assert packet.module_id == "lidar"
    assert packet.live_value == "1.42M"
    assert packet.confidence == 95.4
    assert packet.status == "verified"
    assert packet.source == "lidar_tcp_device"
    assert packet.metadata["host"] == "192.168.1.50"
    assert packet.metadata["port"] == 9100
    assert packet.metadata["device_id"] == "LDR-01"


@pytest.mark.parametrize(
    ("host", "port", "response"),
    [
        ("", 9100, "{}"),
        ("192.168.1.50", 0, "{}"),
        ("192.168.1.50", 70000, "{}"),
        ("192.168.1.50", 9100, ""),
        ("192.168.1.50", 9100, "geçersiz-json"),
        ("192.168.1.50", 9100, '{"live_value": 1}'),
    ],
)
def test_tcp_paket_hatalari(
    host: str,
    port: int,
    response: str,
):
    transport = TcpScientificTransport(
        backend=FakeTcpBackend(response)
    )

    with pytest.raises(ScientificTransportError):
        transport.read_packet(
            host=host,
            port=port,
            timeout=3.0,
        )