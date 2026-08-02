import json

import pytest

from syk_simulasyon.syk_ui_runtime.scientific_transport import (
    ScientificTransportError,
    SerialScientificTransport,
)


class FakeSerialBackend:
    def __init__(self, line: str) -> None:
        self.line = line

    def ports(self):
        return [
            {
                "device": "COM7",
                "description": "SYK PROBE V2",
                "manufacturer": "SyKaşif",
                "vid": 1234,
                "pid": 5678,
            }
        ]

    def read_line(
        self,
        port: str,
        baud_rate: int,
        timeout: float,
    ) -> str:
        assert port == "COM7"
        assert baud_rate == 115200
        assert timeout == 2.0

        return self.line


def test_seri_cihaz_kesfi():
    backend = FakeSerialBackend("{}")
    transport = SerialScientificTransport(
        backend=backend
    )

    devices = transport.discover()

    assert len(devices) == 1
    assert devices[0].id == "serial:COM7"
    assert devices[0].title == "SYK PROBE V2"
    assert devices[0].transport == "serial"
    assert devices[0].address == "COM7"
    assert devices[0].metadata["vid"] == 1234
    assert devices[0].metadata["pid"] == 5678


def test_seri_json_paketi_okuma():
    line = json.dumps(
        {
            "module_id": "magnetometer",
            "live_value": 49120,
            "confidence": 94.8,
            "status": "verified",
            "source": "syk_probe_v2",
            "metadata": {
                "sensor": "MAG-01",
            },
        }
    )

    transport = SerialScientificTransport(
        backend=FakeSerialBackend(line)
    )

    packet = transport.read_packet(
        port="COM7",
        baud_rate=115200,
        timeout=2.0,
    )

    assert packet.module_id == "magnetometer"
    assert packet.live_value == 49120
    assert packet.confidence == 94.8
    assert packet.status == "verified"
    assert packet.source == "syk_probe_v2"
    assert packet.metadata["port"] == "COM7"
    assert packet.metadata["sensor"] == "MAG-01"


@pytest.mark.parametrize(
    "line",
    [
        "",
        "geçersiz-json",
        '{"live_value": 12}',
        '{"module_id": "gpr"}',
    ],
)
def test_seri_paket_hatalari(line: str):
    transport = SerialScientificTransport(
        backend=FakeSerialBackend(line)
    )

    with pytest.raises(
        ScientificTransportError
    ):
        transport.read_packet(
            port="COM7"
        )