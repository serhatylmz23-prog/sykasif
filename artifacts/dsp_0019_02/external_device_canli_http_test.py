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


status, registered = request(
    "POST",
    "/api/syk-ui/external-devices/garmin/mock",
    {
        "latitude": 38.7123,
        "longitude": 38.4521,
        "minimum_depth_m": 0.4,
        "maximum_depth_m": 2.0,
        "seed": 42,
    },
)

print("DEVICE_REGISTER_HTTP", status)

if status != 201:
    raise RuntimeError(
        f"Cihaz kaydedilemedi: {status}"
    )

device_id = str(
    registered["profile"]["identity"]["device_id"]
)

status, connected = request(
    "POST",
    (
        "/api/syk-ui/external-devices/"
        f"{device_id}/connect"
    ),
)

print("DEVICE_CONNECT_HTTP", status)

if status != 200:
    raise RuntimeError(
        f"Cihaz bağlanamadı: {status}"
    )

status, record = request(
    "POST",
    (
        "/api/syk-ui/external-devices/"
        f"{device_id}/frames"
    ),
    {
        "research_id": "canli-research-001",
        "workspace_id": "canli-map-001",
    },
)

print("SONAR_FRAME_HTTP", status)

if status != 201:
    raise RuntimeError(
        f"Sonar karesi okunamadı: {status}"
    )

depth_m = float(
    record["frame"]["depth_m"]
)

print("SONAR_DEPTH_M", depth_m)

if not 0.4 <= depth_m <= 2.0:
    raise RuntimeError(
        f"Derinlik sınır dışı: {depth_m}"
    )

if (
    record["frame"]["metadata"]
    ["priority_profile"]
    != "shallow-coast-0-2m"
):
    raise RuntimeError(
        "Sığ kıyı çalışma profili hatalı."
    )

if (
    record["evidence_candidate"]
    ["evidence_status"]
    != "candidate-unverified"
):
    raise RuntimeError(
        "Kanıt adayı durumu hatalı."
    )

status, records = request(
    "GET",
    (
        "/api/syk-ui/external-devices/"
        "records/list"
        "?research_id=canli-research-001"
    ),
)

print("SONAR_RECORD_LIST_HTTP", status)

if status != 200:
    raise RuntimeError(
        "Sonar kayıtları listelenemedi."
    )

if int(records["count"]) != 1:
    raise RuntimeError(
        "Canlı sonar kayıt sayısı hatalı."
    )

status, disconnected = request(
    "POST",
    (
        "/api/syk-ui/external-devices/"
        f"{device_id}/disconnect"
    ),
)

print("DEVICE_DISCONNECT_HTTP", status)

if status != 200:
    raise RuntimeError(
        "Cihaz bağlantısı kapatılamadı."
    )

print(
    "EXTERNAL_DEVICE_CANLI_HTTP_OK"
)