from __future__ import annotations

import pytest

from syk_core.external_devices.connection_model import (
    DeviceDataAuthority,
    DeviceEndpoint,
    DeviceProtocolProfile,
    DeviceTransportType,
    RawDataAvailability,
)
from syk_core.external_devices.device_model import (
    DeviceConnectionState,
    DeviceIdentity,
)
from syk_core.external_devices.device_discovery import (
    device_discovery_service,
)
from syk_core.external_devices.garmin_real_adapter import (
    GarminRealAdapter,
)
from syk_core.external_devices.nmea_model import (
    NmeaParseError,
    calculate_checksum,
    parse_nmea_sentence,
)


def sentence(payload: str) -> str:
    return (
        f"${payload}*"
        f"{calculate_checksum(payload)}"
    )


def create_adapter() -> GarminRealAdapter:
    return GarminRealAdapter(
        identity=DeviceIdentity(
            manufacturer="Garmin",
            model="External NMEA Device",
            serial_number="GARMIN-REAL-CONTRACT-001",
            device_id="garmin-real-contract-001",
        ),
        endpoint=DeviceEndpoint(
            transport=DeviceTransportType.TCP,
            host="127.0.0.1",
            port=10110,
            timeout_seconds=2.0,
        ),
    )


def test_real_garmin_contract_full_flow() -> None:
    adapter = create_adapter()

    assert (
        adapter.connection_state
        == DeviceConnectionState.DISCONNECTED
    )

    adapter.connect()

    adapter.ingest_many(
        (
            sentence("SDDPT,1.42,0.00"),
            sentence("YXMTW,19.8,C"),
        )
    )

    snapshot = adapter.connection_snapshot()

    assert snapshot.connected is True
    assert snapshot.depth_m == 1.42
    assert snapshot.water_temperature_c == 19.8
    assert snapshot.sentence_count == 2
    assert snapshot.real_device_data is True
    assert (
        snapshot.vendor_raw_sonar_available
        is False
    )

    assert (
        snapshot.protocol["authority"]
        == "external-live"
    )

    assert (
        snapshot.protocol[
            "raw_data_availability"
        ]
        == "partial"
    )

    adapter.disconnect()

    assert (
        adapter.connection_state
        == DeviceConnectionState.DISCONNECTED
    )


def test_invalid_nmea_degrades_health() -> None:
    adapter = create_adapter()
    adapter.connect()

    with pytest.raises(
        NmeaParseError,
        match="checksum",
    ):
        adapter.ingest_nmea(
            "$SDDPT,1.42,0.00*00"
        )

    snapshot = adapter.connection_snapshot()

    assert snapshot.rejected_sentence_count == 1
    assert adapter.health.value == "warning"


def test_network_endpoint_requires_host_and_port() -> None:
    with pytest.raises(
        ValueError,
        match="host ve port",
    ):
        DeviceEndpoint(
            transport=DeviceTransportType.TCP,
        )


def test_vendor_raw_data_is_not_assumed() -> None:
    profile = DeviceProtocolProfile(
        protocol_name="NMEA 0183",
        protocol_version="4.x",
        authority=DeviceDataAuthority.EXTERNAL_LIVE,
        raw_data_availability=(
            RawDataAvailability.PARTIAL
        ),
        supports_depth=True,
        supports_water_temperature=True,
        supports_position=True,
        supports_targets=False,
        supports_bottom_profile=False,
        supports_vendor_raw_sonar=False,
    )

    assert profile.supports_vendor_raw_sonar is False
    assert profile.supports_targets is False


def test_discovery_never_claims_real_device() -> None:
    candidates = (
        device_discovery_service.discover(
            include_mock_candidates=True
        )
    )

    assert len(candidates) == 1
    assert candidates[0].verified is False
    assert (
        candidates[0].metadata["real_device"]
        is False
    )


def test_nmea_parser() -> None:
    payload = "SDDPT,1.84,0.00"
    parsed = parse_nmea_sentence(
        sentence(payload)
    )

    assert parsed.talker == "SD"
    assert parsed.sentence_type == "DPT"
    assert parsed.fields[0] == "1.84"