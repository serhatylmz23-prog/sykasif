import json

import pytest

from syk_simulasyon.syk_ui_runtime.scientific_transport import (
    BleScientificTransport,
    ScientificTransportError,
)


class FakeBleBackend:
    def __init__(
        self,
        payload: bytes,
    ) -> None:
        self.payload = payload

    async def discover(
        self,
        timeout: float,
    ):
        assert timeout == 4.0

        return [
            {
                "address": "AA:BB:CC:DD:EE:FF",
                "name": "SYK PROBE BLE",
                "rssi": -48,
                "service_uuids": [
                    "12345678-1234-5678-1234-56789abcdef0"
                ],
            }
        ]

    async def read_characteristic(
        self,
        address: str,
        characteristic_uuid: str,
        timeout: float,
    ) -> bytes:
        assert address == "AA:BB:CC:DD:EE:FF"
        assert (
            characteristic_uuid
            == "87654321-4321-6789-4321-0fedcba98765"
        )
        assert timeout == 5.0

        return self.payload


@pytest.mark.anyio
async def test_ble_cihaz_kesfi():
    transport = BleScientificTransport(
        backend=FakeBleBackend(b"{}")
    )

    devices = await transport.discover(
        timeout=4.0
    )

    assert len(devices) == 1
    assert devices[0].id == (
        "ble:AA:BB:CC:DD:EE:FF"
    )
    assert devices[0].title == "SYK PROBE BLE"
    assert devices[0].transport == "ble"
    assert (
        devices[0].address
        == "AA:BB:CC:DD:EE:FF"
    )
    assert devices[0].metadata["rssi"] == -48


@pytest.mark.anyio
async def test_ble_json_paketi_okuma():
    payload = json.dumps(
        {
            "module_id": "thermal",
            "live_value": 27.85,
            "confidence": 95.3,
            "status": "verified",
            "source": "thermal_ble_device",
            "metadata": {
                "sensor": "TH-BLE-01",
            },
        }
    ).encode("utf-8")

    transport = BleScientificTransport(
        backend=FakeBleBackend(payload)
    )

    packet = await transport.read_packet(
        address="AA:BB:CC:DD:EE:FF",
        characteristic_uuid=(
            "87654321-4321-6789-4321-0fedcba98765"
        ),
        timeout=5.0,
    )

    assert packet.module_id == "thermal"
    assert packet.live_value == 27.85
    assert packet.confidence == 95.3
    assert packet.status == "verified"
    assert packet.source == "thermal_ble_device"
    assert packet.metadata["sensor"] == "TH-BLE-01"
    assert packet.metadata["transport"] == "ble"


@pytest.mark.anyio
@pytest.mark.parametrize(
    "payload",
    [
        b"",
        b"gecersiz-json",
        b'{"live_value": 1}',
        b'{"module_id": "gpr"}',
    ],
)
async def test_ble_paket_hatalari(
    payload: bytes,
):
    transport = BleScientificTransport(
        backend=FakeBleBackend(payload)
    )

    with pytest.raises(
        ScientificTransportError
    ):
        await transport.read_packet(
            address="AA:BB:CC:DD:EE:FF",
            characteristic_uuid=(
                "87654321-4321-6789-4321-0fedcba98765"
            ),
            timeout=5.0,
        )