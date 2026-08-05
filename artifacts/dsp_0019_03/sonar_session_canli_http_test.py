from __future__ import annotations

import json
import urllib.error
import urllib.parse
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
        body = error.read().decode("utf-8")

        return (
            error.code,
            json.loads(body),
        )


status, device = request(
    "POST",
    "/api/syk-ui/external-devices/garmin/mock",
    {
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
    device["profile"]["identity"]["device_id"]
)

status, _ = request(
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

status, session = request(
    "POST",
    "/api/syk-ui/sonar-sessions",
    {
        "device_id": device_id,
        "name": "DSP-0019-03 Canlı Kıyı Oturumu",
        "research_id": "canli-research-001",
        "workspace_id": "canli-map-001",
        "maximum_priority_depth_m": 2.0,
    },
)

print("SESSION_CREATE_HTTP", status)

if status != 201:
    raise RuntimeError(
        f"Oturum oluşturulamadı: {status}"
    )

session_id = str(
    session["session_id"]
)

status, started = request(
    "POST",
    (
        "/api/syk-ui/sonar-sessions/"
        f"{session_id}/start"
    ),
)

print("SESSION_START_HTTP", status)

if status != 200:
    raise RuntimeError(
        f"Oturum başlatılamadı: {status}"
    )

status, captured = request(
    "POST",
    (
        "/api/syk-ui/sonar-sessions/"
        f"{session_id}/capture"
    ),
    {
        "frame_count": 6,
    },
)

print("SESSION_CAPTURE_HTTP", status)

if status != 200:
    raise RuntimeError(
        f"Sonar kareleri alınamadı: {status}"
    )

print(
    "SESSION_FRAME_COUNT",
    captured["frame_count"],
)

print(
    "SESSION_FISH_TARGET_COUNT",
    captured["summary"]["fish_target_count"],
)

if int(captured["frame_count"]) != 6:
    raise RuntimeError(
        "Canlı oturum kare sayısı hatalı."
    )

if len(captured["gps_track"]) != 6:
    raise RuntimeError(
        "GPS izi beklenen sayıda değil."
    )

if (
    len(
        captured["evidence_candidate_ids"]
    )
    != 6
):
    raise RuntimeError(
        "Kanıt adayı zinciri eksik."
    )

if (
    captured["map_layer_state"]
    ["layer_key"]
    != "garmin-sonar-live"
):
    raise RuntimeError(
        "Canlı sonar harita katmanı hatalı."
    )

if (
    captured["map_layer_state"]
    ["within_priority_depth"]
    is not True
):
    raise RuntimeError(
        "0–2 m çalışma profili dışına çıkıldı."
    )

status, stopped = request(
    "POST",
    (
        "/api/syk-ui/sonar-sessions/"
        f"{session_id}/stop"
    ),
)

print("SESSION_STOP_HTTP", status)

if status != 200:
    raise RuntimeError(
        f"Oturum durdurulamadı: {status}"
    )

if stopped["state"] != "stopped":
    raise RuntimeError(
        "Sonar oturumu durmadı."
    )

query = urllib.parse.urlencode(
    {
        "research_id": "canli-research-001",
    }
)

status, sessions = request(
    "GET",
    (
        "/api/syk-ui/sonar-sessions"
        f"?{query}"
    ),
)

print("SESSION_LIST_HTTP", status)

if status != 200:
    raise RuntimeError(
        "Sonar oturumları listelenemedi."
    )

if int(sessions["count"]) != 1:
    raise RuntimeError(
        "Canlı sonar oturumu listede bulunamadı."
    )

print(
    "SONAR_SESSION_CANLI_HTTP_OK"
)