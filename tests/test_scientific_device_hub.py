import pytest

from syk_simulasyon.syk_ui_runtime.scientific_device_hub import (
    ScientificDeviceHub,
)


class FakeManager:
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
                        "title": "SYK PROBE V2",
                        "address": "COM7",
                        "connected": False,
                        "metadata": {
                            "manufacturer": "SyKaşif",
                        },
                    }
                ],
                "ble": [
                    {
                        "id": "ble:AA",
                        "title": "SYK THERMAL",
                        "address": "AA",
                        "connected": False,
                        "metadata": {
                            "rssi": -42,
                        },
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


@pytest.mark.anyio
async def test_device_hub_kesif_ve_envanter():
    hub = ScientificDeviceHub(FakeManager())

    refreshed = await hub.refresh(
        ble_timeout=4.0
    )

    assert len(refreshed["devices"]) == 2
    assert len(refreshed["transports"]) == 3
    assert hub.exists("serial:COM7")
    assert hub.exists("ble:AA")

    probe = hub.get("serial:COM7")

    assert probe["title"] == "SYK PROBE V2"
    assert probe["transport"] == "serial"
    assert probe["address"] == "COM7"


def test_device_hub_baglanti_ve_telemetri():
    hub = ScientificDeviceHub(FakeManager())

    created = hub.register_manual(
        device_id="tcp:gpr-01",
        title="SYK GPR",
        transport="tcp",
        address="192.168.1.50:9100",
        module_id="gpr",
    )

    assert created["connected"] is False

    connected = hub.set_connection(
        "tcp:gpr-01",
        connected=True,
    )

    assert connected["connected"] is True
    assert connected["state"] == "connected"

    updated = hub.update_telemetry(
        "tcp:gpr-01",
        battery=88.4,
        signal_quality=93.1,
        firmware="1.4.2",
    )

    assert updated["battery"] == 88.4
    assert updated["signal_quality"] == 93.1
    assert updated["firmware"] == "1.4.2"
    assert updated["last_packet_at"]


def test_device_hub_hatalari():
    hub = ScientificDeviceHub(FakeManager())

    with pytest.raises(KeyError):
        hub.get("unknown")

    with pytest.raises(ValueError):
        hub.register_manual(
            device_id="bad",
            title="Bad",
            transport="infrared",
            address="X",
        )