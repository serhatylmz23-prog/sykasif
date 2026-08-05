from __future__ import annotations

from syk_core.external_devices import (
    GarminAdapter,
    device_registry,
)


adapter = GarminAdapter()

device_registry.reset()
device_registry.register(adapter)

device_id = adapter.profile.identity.device_id
device_count = device_registry.status_snapshot()["count"]

print(
    "DEVICE_ID",
    device_id,
)

print(
    "DEVICE_COUNT",
    device_count,
)

if device_id != "garmin-sonar-mock-001":
    raise RuntimeError(
        f"Beklenmeyen cihaz kimliği: {device_id}"
    )

if device_count != 1:
    raise RuntimeError(
        f"Beklenmeyen cihaz sayısı: {device_count}"
    )

adapter.connect()
frame = adapter.read_frame()

print(
    "FRAME_DEPTH_M",
    frame.depth_m,
)

print(
    "FRAME_SOURCE_MODE",
    frame.source_mode,
)

if not 0.0 <= frame.depth_m <= 2.0:
    raise RuntimeError(
        f"Sığ kıyı derinliği sınır dışı: {frame.depth_m}"
    )

if frame.source_mode != "mock":
    raise RuntimeError(
        f"Kaynak türü hatalı: {frame.source_mode}"
    )

adapter.disconnect()

print(
    "EXTERNAL_DEVICE_IMPORT_OK"
)