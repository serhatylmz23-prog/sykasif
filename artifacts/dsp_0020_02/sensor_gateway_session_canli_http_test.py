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


for source in (
    {
        "source_id": "dsp-0020-sonar",
        "name": "DSP-0020 Sonar",
        "kind": "sonar",
    },
    {
        "source_id": "dsp-0020-gps",
        "name": "DSP-0020 GPS",
        "kind": "gps",
    },
):
    status, _ = request(
        "POST",
        "/api/syk-ui/sensor-gateway/sources",
        {
            **source,
            "authority": "external-live",
            "health": "healthy",
            "real_device_data": True,
            "simulation_data": False,
        },
    )

    print(
        "SOURCE_CREATE_HTTP",
        source["source_id"],
        status,
    )

    if status != 201:
        raise RuntimeError(
            "Sensör kaynağı oluşturulamadı."
        )


status, session = request(
    "POST",
    "/api/syk-ui/sensor-sessions",
    {
        "name": "DSP-0020 Çoklu Sensör Oturumu",
        "source_ids": [
            "dsp-0020-sonar",
            "dsp-0020-gps",
        ],
        "research_id": "dsp-0020-research",
        "workspace_id": "dsp-0020-map",
    },
)

print("SESSION_CREATE_HTTP", status)

if status != 201:
    raise RuntimeError(
        "Çoklu sensör oturumu oluşturulamadı."
    )

session_id = str(
    session["session_id"]
)

status, _ = request(
    "POST",
    (
        "/api/syk-ui/sensor-sessions/"
        f"{session_id}/start"
    ),
)

print("SESSION_START_HTTP", status)

if status != 200:
    raise RuntimeError(
        "Sensör oturumu başlatılamadı."
    )


for source_id, payload, confidence in (
    (
        "dsp-0020-gps",
        {
            "latitude": 38.712301,
            "longitude": 38.452101,
            "accuracy_m": 0.04,
        },
        0.98,
    ),
    (
        "dsp-0020-sonar",
        {
            "depth_m": 1.47,
            "water_temperature_c": 20.0,
            "gps": {
                "latitude": 38.712302,
                "longitude": 38.452102,
            },
        },
        0.84,
    ),
):
    status, _ = request(
        "POST",
        (
            "/api/syk-ui/sensor-gateway/"
            f"sources/{source_id}/ingest"
        ),
        {
            "payload": payload,
            "research_id": "dsp-0020-research",
            "workspace_id": "dsp-0020-map",
            "confidence": confidence,
        },
    )

    print(
        "SENSOR_INGEST_HTTP",
        source_id,
        status,
    )

    if status != 201:
        raise RuntimeError(
            "Sensör verisi kabul edilemedi."
        )


status, synced = request(
    "POST",
    (
        "/api/syk-ui/sensor-sessions/"
        f"{session_id}/sync"
    ),
)

print("SESSION_SYNC_HTTP", status)

if status != 200:
    raise RuntimeError(
        "Çoklu sensör eşlemesi başarısız."
    )

if int(synced["envelope_count"]) != 2:
    raise RuntimeError(
        "Birleşik sensör paket sayısı hatalı."
    )

if len(synced["gps_track"]) != 2:
    raise RuntimeError(
        "GPS merkezli iz eksik."
    )

if (
    len(
        synced["evidence_candidate_ids"]
    )
    != 2
):
    raise RuntimeError(
        "Çapraz kanıt adayları eksik."
    )

status, stopped = request(
    "POST",
    (
        "/api/syk-ui/sensor-sessions/"
        f"{session_id}/stop"
    ),
)

print("SESSION_STOP_HTTP", status)

if status != 200:
    raise RuntimeError(
        "Sensör oturumu durdurulamadı."
    )

if stopped["state"] != "stopped":
    raise RuntimeError(
        "Sensör oturumu durmadı."
    )

print(
    "SENSOR_GATEWAY_SESSION_CANLI_HTTP_OK"
)