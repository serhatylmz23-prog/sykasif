from __future__ import annotations

from syk_core.external_devices.connection_model import (
    DeviceEndpoint,
    DeviceTransportType,
)
from syk_core.external_devices.device_model import (
    DeviceIdentity,
)
from syk_core.external_devices.garmin_real_adapter import (
    GarminRealAdapter,
)
from syk_core.external_devices.nmea_model import (
    calculate_checksum,
)


def sentence(payload: str) -> str:
    return (
        f"${payload}*"
        f"{calculate_checksum(payload)}"
    )


adapter = GarminRealAdapter(
    identity=DeviceIdentity(
        manufacturer="Garmin",
        model="Contract Verification Device",
        serial_number="VERIFY-001",
        device_id="garmin-contract-verify-001",
    ),
    endpoint=DeviceEndpoint(
        transport=DeviceTransportType.TCP,
        host="127.0.0.1",
        port=10110,
    ),
)

adapter.connect()

adapter.ingest_many(
    (
        sentence("SDDPT,1.36,0.00"),
        sentence("YXMTW,20.1,C"),
    )
)

snapshot = adapter.connection_snapshot()

print(
    "REAL_DEVICE_DATA",
    snapshot.real_device_data,
)

print(
    "DEPTH_M",
    snapshot.depth_m,
)

print(
    "WATER_TEMPERATURE_C",
    snapshot.water_temperature_c,
)

print(
    "RAW_VENDOR_SONAR",
    snapshot.vendor_raw_sonar_available,
)

if snapshot.depth_m != 1.36:
    raise RuntimeError(
        "Derinlik sÃ¶zleÅŸmesi doÄŸrulanamadÄ±."
    )

if snapshot.water_temperature_c != 20.1:
    raise RuntimeError(
        "Su sÄ±caklÄ±ÄŸÄ± sÃ¶zleÅŸmesi doÄŸrulanamadÄ±."
    )

if snapshot.vendor_raw_sonar_available:
    raise RuntimeError(
        "Desteklenmeyen ham sonar verisi "
        "yanlÄ±ÅŸlÄ±kla etkin gÃ¶sterildi."
    )

adapter.disconnect()

print(
    "GARMIN_REAL_CONNECTION_CONTRACT_OK"
)