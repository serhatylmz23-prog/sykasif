from __future__ import annotations

import pytest

from syk_core.external_devices import (
    DeviceConnectionState,
    DeviceRegistry,
    GarminAdapter,
    GarminMockConfiguration,
    SonarTargetType,
)


def test_garmin_mock_adapter_full_flow() -> None:
    adapter = GarminAdapter(
        GarminMockConfiguration(
            latitude=38.7123,
            longitude=38.4521,
            minimum_depth_m=0.4,
            maximum_depth_m=2.0,
            seed=42,
        )
    )

    assert (
        adapter.connection_state
        == DeviceConnectionState.DISCONNECTED
    )

    adapter.connect()

    assert (
        adapter.connection_state
        == DeviceConnectionState.CONNECTED
    )

    first = adapter.read_frame()
    second = adapter.read_frame()

    assert 0.4 <= first.depth_m <= 2.0
    assert 0.4 <= second.depth_m <= 2.0

    assert (
        first.metadata["priority_profile"]
        == "shallow-coast-0-2m"
    )

    assert first.metadata["real_device_data"] is False
    assert first.raw_data_available is False
    assert first.gps_fix is not None

    assert len(second.targets) == 1
    assert (
        second.targets[0].target_type
        == SonarTargetType.FISH
    )

    assert (
        second.targets[0]
        .metadata["species_identified"]
        is False
    )

    adapter.disconnect()

    assert (
        adapter.connection_state
        == DeviceConnectionState.DISCONNECTED
    )


def test_garmin_adapter_requires_connection() -> None:
    adapter = GarminAdapter()

    with pytest.raises(
        RuntimeError,
        match="bağlı değil",
    ):
        adapter.read_frame()


def test_device_registry_flow() -> None:
    registry = DeviceRegistry()
    adapter = GarminAdapter()

    registry.register(adapter)

    device_id = (
        adapter.profile.identity.device_id
    )

    assert registry.get(device_id) is adapter
    assert registry.status_snapshot()["count"] == 1

    with pytest.raises(
        ValueError,
        match="zaten kayıtlı",
    ):
        registry.register(adapter)

    removed = registry.unregister(device_id)

    assert removed is adapter
    assert registry.get(device_id) is None


def test_invalid_mock_depth_profile() -> None:
    with pytest.raises(
        ValueError,
        match="Azami derinlik",
    ):
        GarminMockConfiguration(
            minimum_depth_m=2.0,
            maximum_depth_m=1.0,
        )