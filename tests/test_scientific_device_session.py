import pytest

from syk_simulasyon.syk_ui_runtime.scientific_device_session import (
    ScientificDeviceSessionManager,
)


class FakeHub:
    def __init__(self):
        self.devices = {
            "serial:COM7": {
                "id": "serial:COM7",
                "connected": True,
                "module_id": "gpr",
            },
            "ble:AA": {
                "id": "ble:AA",
                "connected": False,
                "module_id": "thermal",
            },
        }

    def get(self, device_id: str):
        if device_id not in self.devices:
            raise KeyError(device_id)

        return dict(self.devices[device_id])


def test_cihaz_kayit_oturumu():
    manager = ScientificDeviceSessionManager(
        FakeHub()
    )

    started = manager.start(
        device_id="serial:COM7",
        metadata={
            "operator": "Bilge Kaan",
        },
    )

    assert started["state"] == "recording"
    assert started["device_id"] == "serial:COM7"
    assert started["module_id"] == "gpr"
    assert started["sample_count"] == 0
    assert started["started_at"]

    active = manager.active_for_device(
        "serial:COM7"
    )

    assert active["id"] == started["id"]

    sampled = manager.append_sample(
        started["id"],
        count=25,
    )

    assert sampled["sample_count"] == 25

    stopped = manager.stop(started["id"])

    assert stopped["state"] == "stopped"
    assert stopped["stopped_at"]
    assert (
        manager.active_for_device("serial:COM7")
        is None
    )


def test_cihaz_kayit_oturumu_hatalari():
    manager = ScientificDeviceSessionManager(
        FakeHub()
    )

    with pytest.raises(ValueError):
        manager.start(
            device_id="ble:AA"
        )

    started = manager.start(
        device_id="serial:COM7"
    )

    with pytest.raises(ValueError):
        manager.start(
            device_id="serial:COM7"
        )

    manager.stop(started["id"])

    with pytest.raises(ValueError):
        manager.append_sample(
            started["id"]
        )

    with pytest.raises(KeyError):
        manager.get("unknown")