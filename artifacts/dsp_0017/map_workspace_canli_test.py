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


status, project = request(
    "POST",
    "/api/syk-ui/projects",
    {
        "name": "DSP-0017 Harita Projesi",
        "research_area": "Harita, AR ve sonar",
    },
)

print("PROJECT_HTTP", status)

if status != 201:
    raise RuntimeError(
        f"Proje oluşturulamadı: {status}"
    )

status, research = request(
    "POST",
    "/api/syk-ui/research",
    {
        "project_id": project["project_id"],
        "title": "Kıyı Şeridi Harita Çalışması",
        "research_type": "map-sonar",
    },
)

print("RESEARCH_HTTP", status)

if status != 201:
    raise RuntimeError(
        f"Araştırma oluşturulamadı: {status}"
    )

status, workspace = request(
    "POST",
    "/api/syk-ui/map-workspaces",
    {
        "research_id": research["research_id"],
        "name": "Keban Kıyı Çalışma Alanı",
        "latitude": 38.7123,
        "longitude": 38.4521,
        "zoom": 18,
    },
)

print("MAP_WORKSPACE_HTTP", status)

if status != 201:
    raise RuntimeError(
        f"Harita alanı oluşturulamadı: {status}"
    )

workspace_id = str(
    workspace["workspace_id"]
)

operations = (
    (
        "PATCH",
        f"/api/syk-ui/map-workspaces/{workspace_id}/activate",
        None,
        200,
        "MAP_ACTIVATE_HTTP",
    ),
    (
        "PATCH",
        f"/api/syk-ui/map-workspaces/{workspace_id}/ar",
        {"enabled": True},
        200,
        "MAP_AR_HTTP",
    ),
    (
        "POST",
        f"/api/syk-ui/map-workspaces/{workspace_id}/pins",
        {
            "name": "Kıyı Tarama Noktası",
            "latitude": 38.7124,
            "longitude": 38.4522,
            "accuracy_m": 1.5,
        },
        201,
        "MAP_PIN_HTTP",
    ),
    (
        "POST",
        f"/api/syk-ui/map-workspaces/{workspace_id}/layers",
        {
            "key": "garmin-sonar",
            "name": "Garmin Sonar",
            "layer_type": "sonar",
            "opacity": 0.82,
            "ar_enabled": True,
            "source": "external-device-adapter",
            "metadata": {
                "priority_depth_m": 2.0,
                "mode": "shallow-coast-support",
            },
        },
        201,
        "MAP_SONAR_LAYER_HTTP",
    ),
    (
        "POST",
        (
            f"/api/syk-ui/map-workspaces/"
            f"{workspace_id}/measurements"
        ),
        {
            "measurement_type": "distance",
            "value": 14.8,
            "unit": "m",
            "start": {
                "latitude": 38.7123,
                "longitude": 38.4521,
            },
            "end": {
                "latitude": 38.7124,
                "longitude": 38.4522,
            },
        },
        201,
        "MAP_MEASUREMENT_HTTP",
    ),
)

for method, path, payload, expected, label in operations:
    status, result = request(
        method,
        path,
        payload,
    )

    print(label, status)

    if status != expected:
        raise RuntimeError(
            f"{label} başarısız: {status} {result}"
        )

status, final_state = request(
    "GET",
    f"/api/syk-ui/map-workspaces/{workspace_id}",
)

print("MAP_FINAL_HTTP", status)

if status != 200:
    raise RuntimeError(
        "Harita çalışma alanı okunamadı."
    )

if final_state["ar_enabled"] is not True:
    raise RuntimeError(
        "AR durumu etkinleşmedi."
    )

if len(final_state["pins"]) != 1:
    raise RuntimeError(
        "Konum pini kaydedilmedi."
    )

if len(final_state["measurements"]) != 1:
    raise RuntimeError(
        "Ölçüm kaydedilmedi."
    )

if not any(
    layer["key"] == "garmin-sonar"
    for layer in final_state["layers"]
):
    raise RuntimeError(
        "Garmin sonar katmanı kaydedilmedi."
    )

print(
    "MAP_WORKSPACE_CANLI_HTTP_OK"
)