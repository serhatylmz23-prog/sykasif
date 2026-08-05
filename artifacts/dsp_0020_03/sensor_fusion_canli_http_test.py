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


sources = (
    {
        "source_id": "fusion-sonar",
        "name": "Fusion Sonar",
        "kind": "sonar",
    },
    {
        "source_id": "fusion-gps",
        "name": "Fusion GPS",
        "kind": "gps",
    },
    {
        "source_id": "fusion-water",
        "name": "Fusion Water",
        "kind": "water-temperature",
    },
)

for source in sources:
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
            "Birleştirme kaynağı oluşturulamadı."
        )


records = (
    (
        "fusion-sonar",
        {
            "depth_m": 1.46,
            "water_temperature_c": 19.9,
            "gps": {
                "latitude": 38.712301,
                "longitude": 38.452101,
            },
        },
        0.84,
    ),
    (
        "fusion-gps",
        {
            "latitude": 38.712302,
            "longitude": 38.452102,
            "accuracy_m": 0.04,
        },
        0.98,
    ),
    (
        "fusion-water",
        {
            "water_temperature_c": 20.3,
            "latitude": 38.712303,
            "longitude": 38.452103,
        },
        0.90,
    ),
)

for source_id, payload, confidence in records:
    status, _ = request(
        "POST",
        (
            "/api/syk-ui/sensor-gateway/"
            f"sources/{source_id}/ingest"
        ),
        {
            "payload": payload,
            "research_id": "fusion-research",
            "workspace_id": "fusion-map",
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
            "Birleştirme verisi kaydedilemedi."
        )


status, result = request(
    "POST",
    "/api/syk-ui/sensor-fusion/run",
    {
        "research_id": "fusion-research",
        "workspace_id": "fusion-map",
        "time_tolerance_seconds": 10,
        "location_tolerance_m": 20,
        "minimum_source_count": 2,
        "minimum_confidence": 0.5,
        "source_weights": {
            "fusion-sonar": 2.0,
            "fusion-gps": 3.0,
            "fusion-water": 1.0,
        },
    },
)

print("SENSOR_FUSION_HTTP", status)

if status != 201:
    raise RuntimeError(
        "Sensör birleştirme çalıştırılamadı."
    )

if int(result["count"]) != 1:
    raise RuntimeError(
        "Birleşim grubu oluşturulamadı."
    )

group = result["groups"][0]

if len(group["source_ids"]) != 3:
    raise RuntimeError(
        "Birleşim kaynak sayısı hatalı."
    )

if group["real_device_data"] is not True:
    raise RuntimeError(
        "Gerçek veri işareti kayboldu."
    )

if group["simulation_data"] is not False:
    raise RuntimeError(
        "Simülasyon izolasyonu bozuldu."
    )

if (
    group["map_layer_packet"]
    ["layer_key"]
    != "sensor-fusion"
):
    raise RuntimeError(
        "Harita katman paketi hatalı."
    )

if len(group["evidence_group_id"]) < 20:
    raise RuntimeError(
        "Kanıt grubu kimliği eksik."
    )

print(
    "SENSOR_FUSION_CANLI_HTTP_OK"
)