import json

from syk_simulasyon.syk_ui_runtime.scientific_adapter import (
    ScientificAdapterRegistry,
    ingest_transport_packet,
)
from syk_simulasyon.syk_ui_runtime.scientific_runtime import (
    ScientificRuntime,
)
from syk_simulasyon.syk_ui_runtime.scientific_transport import (
    SerialScientificTransport,
)


class FakeSerialBackend:
    def ports(self):
        return []

    def read_line(
        self,
        port: str,
        baud_rate: int,
        timeout: float,
    ) -> str:
        return json.dumps(
            {
                "module_id": "gpr",
                "live_value": 52.4,
                "confidence": 96.1,
                "status": "verified",
                "source": "gpr_serial_device",
                "metadata": {
                    "antenna": "400MHz",
                },
            }
        )


def test_seri_paket_runtime_aktarimi():
    runtime = ScientificRuntime()
    registry = ScientificAdapterRegistry(runtime)

    transport = SerialScientificTransport(
        backend=FakeSerialBackend()
    )

    packet = transport.read_packet(
        port="COM9"
    )

    result = ingest_transport_packet(
        registry,
        packet,
    )

    assert result["state"]["live_value"] == 52.4
    assert result["state"]["confidence"] == 96.1
    assert result["state"]["status"] == "verified"
    assert (
        result["state"]["source"]
        == "gpr_serial_device"
    )

    assert (
        result["adapter"]["metadata"]["port"]
        == "COM9"
    )