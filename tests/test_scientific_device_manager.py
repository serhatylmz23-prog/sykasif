import json

import pytest

from syk_simulasyon.syk_ui_runtime.scientific_adapter import (
    ScientificAdapterRegistry,
)
from syk_simulasyon.syk_ui_runtime.scientific_device_manager import (
    ScientificDeviceManager,
)
from syk_simulasyon.syk_ui_runtime.scientific_runtime import (
    ScientificRuntime,
)
from syk_simulasyon.syk_ui_runtime.scientific_transport import (
    BleScientificTransport,
    SerialScientificTransport,
    TcpScientificTransport,
)


class FakeSerialBackend:
    def ports(self):
        return [
            {
                "device": "COM7",
                "description": "SYK PROBE V2",
            }
        ]

    def read_line(
        self,
        port: str,
        baud_rate: int,
        timeout: float,
    ) -> str:
        return json.dumps(
            {
                "module_id": "gpr",
                "live_value": 54.2,
                "confidence": 95.1,
                "status": "verified",
                "source": "serial_manager_test",
            }
        )


class FakeTcpBackend:
    def receive(
        self,
        host: str,
        port: int,
        timeout: float,
    ) -> str:
        return json.dumps(
            {
                "module_id": "lidar",
                "live_value": "1.55M",
                "confidence": 96.0,
                "status": "verified",
                "source": "tcp_manager_test",
            }
        )


class FakeBleBackend:
    async def discover(
        self,
        timeout: float,
    ):
        return [
            {
                "address": "AA:BB:CC:DD:EE:FF",
                "name": "SYK PROBE BLE",
                "rssi": -40,
            }
        ]

    async def read_characteristic(
        self,
        address: str,
        characteristic_uuid: str,
        timeout: float,
    ) -> bytes:
        return json.dumps(
            {
                "module_id": "thermal",
                "live_value": 28.7,
                "confidence": 94.4,
                "status": "verified",
                "source": "ble_manager_test",
            }
        ).encode("utf-8")


def create_manager():
    runtime = ScientificRuntime()
    adapters = ScientificAdapterRegistry(runtime)

    manager = ScientificDeviceManager(
        adapters=adapters,
        serial_transport=SerialScientificTransport(
            backend=FakeSerialBackend()
        ),
        tcp_transport=TcpScientificTransport(
            backend=FakeTcpBackend()
        ),
        ble_transport=BleScientificTransport(
            backend=FakeBleBackend()
        ),
    )

    return runtime, manager


def test_bilimsel_cihaz_yonetici_tasimlari():
    _, manager = create_manager()

    transports = manager.transports()

    assert len(transports) == 3

    assert {
        item["id"]
        for item in transports
    } == {
        "serial",
        "tcp",
        "ble",
    }


@pytest.mark.anyio
async def test_bilimsel_cihaz_toplu_kesif():
    _, manager = create_manager()

    result = await manager.discover_all(
        ble_timeout=4.0
    )

    assert len(result["devices"]["serial"]) == 1
    assert len(result["devices"]["ble"]) == 1
    assert result["devices"]["tcp"] == []

    assert (
        result["devices"]["serial"][0]["address"]
        == "COM7"
    )

    assert (
        result["devices"]["ble"][0]["address"]
        == "AA:BB:CC:DD:EE:FF"
    )


def test_bilimsel_cihaz_seri_ve_tcp_okuma():
    runtime, manager = create_manager()

    serial_result = manager.read_serial(
        port="COM7"
    )

    assert (
        serial_result["state"]["live_value"]
        == 54.2
    )

    assert (
        runtime.get("gpr")["state"]["source"]
        == "serial_manager_test"
    )

    tcp_result = manager.read_tcp(
        host="192.168.1.50",
        port=9100,
    )

    assert (
        tcp_result["state"]["live_value"]
        == "1.55M"
    )

    assert (
        runtime.get("lidar")["state"]["source"]
        == "tcp_manager_test"
    )


@pytest.mark.anyio
async def test_bilimsel_cihaz_ble_okuma():
    runtime, manager = create_manager()

    result = await manager.read_ble(
        address="AA:BB:CC:DD:EE:FF",
        characteristic_uuid=(
            "87654321-4321-6789-4321-0fedcba98765"
        ),
    )

    assert result["state"]["live_value"] == 28.7

    assert (
        runtime.get("thermal")["state"]["source"]
        == "ble_manager_test"
    )