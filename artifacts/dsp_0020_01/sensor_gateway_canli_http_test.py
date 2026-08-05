from __future__ import annotations

import json
import urllib.error
import urllib.request


BASE_URL = "http://127.0.0.1:8013"


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
                    response.read().decode(
                        "utf-8"
                    )
                ),
            )
    except urllib.error.HTTPError as error:
        return (
            error.code,
            json.loads(
                error.read().decode("utf-8")
            ),
        )


status, source = request(
    "POST",
    "/api/syk-ui/sensor-gateway/sources",
    {
        "source_id": "dsp-0020-garmin-sonar",
        "name": "DSP-0020 Garmin Sonar",
        "kind": "sonar",
        "authority": "external-live",
        "health": "healthy",
        "real_device_data": True,
        "simulation_data": False,
        "metadata": {
            "profile": "shallow-coast-0-2m",
        },
    },
)

print("SOURCE_CREATE_HTTP", status)

if status != 201:
    raise RuntimeError(
        "Sensör kaynağı oluşturulamadı."
    )

status, envelope = request(
    "POST",
    (
        "/api/syk-ui/sensor-gateway/"
        "sources/dsp-0020-garmin-sonar/ingest"
    ),
    {
        "payload": {
            "depth_m": 1.51,
            "water_temperature_c": 20.0,
            "fish_target_count": 1,
        },
        "research_id": "dsp-0020-research",
        "workspace_id": "dsp-0020-map",
        "confidence": 0.82,
    },
)

print("SENSOR_INGEST_HTTP", status)

if status != 201:
    raise RuntimeError(
        "Sensör verisi alınamadı."
    )

if envelope["real_device_data"] is not True:
    raise RuntimeError(
        "Gerçek cihaz veri işareti kayboldu."
    )

if envelope["simulation_data"] is not False:
    raise RuntimeError(
        "Simülasyon izolasyonu bozuldu."
    )

status, snapshot = request(
    "GET",
    "/api/syk-ui/sensor-gateway",
)

print("SENSOR_GATEWAY_HTTP", status)

if status != 200:
    raise RuntimeError(
        "Sensör geçidi özeti alınamadı."
    )

if snapshot["source_count"] != 1:
    raise RuntimeError(
        "Sensör kaynak sayısı hatalı."
    )

if snapshot["envelope_count"] != 1:
    raise RuntimeError(
        "Sensör paket sayısı hatalı."
    )

if len(snapshot["manifest_sha256"]) != 64:
    raise RuntimeError(
        "Sensör geçidi manifest SHA kaydı hatalı."
    )

print(
    "SENSOR_GATEWAY_CANLI_HTTP_OK"
)