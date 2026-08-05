from __future__ import annotations

import json
import urllib.error
import urllib.request

from syk_core.external_devices.nmea_model import (
    calculate_checksum,
)


BASE_URL = "http://127.0.0.1:8013"


def sentence(payload: str) -> str:
    return (
        f"${payload}*"
        f"{calculate_checksum(payload)}"
    )


def request(
    method: str,
    path: str,
    payload: dict[str, object] | None = None,
) -> tuple[int, dict[str, object]]:
    data = None
    headers: dict[str, str] = {}

    if payload is not None:
        data = json.dumps(
            payload,
            ensure_ascii=False,
        ).encode("utf-8")

        headers["Content-Type"] = (
            "application/json; charset=utf-8"
        )

    req = urllib.request.Request(
        BASE_URL + path,
        data=data,
        headers=headers,
        method=method,
    )

    try:
        with urllib.request.urlopen(
            req,
            timeout=10,
        ) as response:
            return (
                response.status,
                json.loads(
                    response.read().decode("utf-8")
                ),
            )
    except urllib.error.HTTPError as error:
        return (
            error.code,
            json.loads(
                error.read().decode("utf-8")
            ),
        )


status, connection = request(
    "POST",
    "/api/syk-ui/real-device-connections",
    {
        "manufacturer": "Garmin",
        "model": "DSP-0019-06 NMEA Runtime",
        "serial_number": "DSP-0019-06-001",
        "device_id": "dsp-0019-06-garmin",
        "transport": "tcp",
        "host": "127.0.0.1",
        "port": 10110,
    },
)

print("CONNECTION_CREATE_HTTP", status)

if status != 201:
    raise RuntimeError(
        "Gerçek bağlantı profili oluşturulamadı."
    )

connection_id = str(
    connection["connection_id"]
)

status, _ = request(
    "POST",
    (
        "/api/syk-ui/real-device-connections/"
        f"{connection_id}/connect"
    ),
)

print("CONNECTION_CONNECT_HTTP", status)

if status != 200:
    raise RuntimeError(
        "Gerçek bağlantı açılamadı."
    )

status, heartbeat = request(
    "POST",
    (
        "/api/syk-ui/real-device-connections/"
        f"{connection_id}/heartbeat"
    ),
)

print("CONNECTION_HEARTBEAT_HTTP", status)

if status != 200:
    raise RuntimeError(
        "Heartbeat başarısız."
    )

for payload in (
    "SDDPT,1.38,0.00",
    "YXMTW,20.2,C",
):
    status, connection = request(
        "POST",
        (
            "/api/syk-ui/real-device-connections/"
            f"{connection_id}/nmea"
        ),
        {
            "sentence": sentence(payload),
        },
    )

    print("NMEA_INGEST_HTTP", status)

    if status != 200:
        raise RuntimeError(
            f"NMEA kabulü başarısız: {payload}"
        )

snapshot = connection["connection_snapshot"]

if snapshot["depth_m"] != 1.38:
    raise RuntimeError(
        "Gerçek derinlik Runtime kaydı hatalı."
    )

if snapshot["water_temperature_c"] != 20.2:
    raise RuntimeError(
        "Gerçek sıcaklık Runtime kaydı hatalı."
    )

if snapshot["real_device_data"] is not True:
    raise RuntimeError(
        "Gerçek veri yetkisi kayboldu."
    )

status, manifest = request(
    "GET",
    (
        "/api/syk-ui/real-device-connections/"
        f"{connection_id}/manifest"
    ),
)

print("CONNECTION_MANIFEST_HTTP", status)

if status != 200:
    raise RuntimeError(
        "Bağlantı manifesti üretilemedi."
    )

if manifest["simulation_data"] is not False:
    raise RuntimeError(
        "Gerçek ve simülasyon veri ayrımı hatalı."
    )

if len(manifest["digest_sha256"]) != 64:
    raise RuntimeError(
        "Manifest SHA-256 kaydı hatalı."
    )

status, _ = request(
    "POST",
    (
        "/api/syk-ui/real-device-connections/"
        f"{connection_id}/disconnect"
    ),
)

print("CONNECTION_DISCONNECT_HTTP", status)

if status != 200:
    raise RuntimeError(
        "Gerçek bağlantı kapatılamadı."
    )

print(
    "REAL_DEVICE_CONNECTION_CANLI_HTTP_OK"
)