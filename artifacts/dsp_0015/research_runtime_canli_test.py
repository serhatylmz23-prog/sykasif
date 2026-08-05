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
        "name": "DSP-0015 Canlı Proje",
        "research_area": "Araştırma Masası",
        "description": "Birleşik canlı test",
    },
)

print("PROJECT_CREATE_HTTP", status)

if status != 201:
    raise RuntimeError(
        f"Proje oluşturulamadı: {status}"
    )

status, research = request(
    "POST",
    "/api/syk-ui/research",
    {
        "project_id": project["project_id"],
        "title": "Canlı Araştırma",
        "research_type": "map-sonar",
        "notes": "DSP-0015 doğrulaması",
    },
)

print("RESEARCH_CREATE_HTTP", status)

if status != 201:
    raise RuntimeError(
        f"Araştırma oluşturulamadı: {status}"
    )

research_id = str(
    research["research_id"]
)

operations = (
    (
        f"/api/syk-ui/research/{research_id}/start",
        None,
        "RESEARCH_START_HTTP",
    ),
    (
        f"/api/syk-ui/research/{research_id}/media",
        {"value": "media-canli-001"},
        "RESEARCH_MEDIA_HTTP",
    ),
    (
        f"/api/syk-ui/research/{research_id}/evidence",
        {"value": "evidence-canli-001"},
        "RESEARCH_EVIDENCE_HTTP",
    ),
    (
        f"/api/syk-ui/research/{research_id}/map-layer",
        {"value": "topography"},
        "RESEARCH_MAP_HTTP",
    ),
    (
        f"/api/syk-ui/research/{research_id}/complete",
        None,
        "RESEARCH_COMPLETE_HTTP",
    ),
)

for path, payload, label in operations:
    status, result = request(
        "PATCH",
        path,
        payload,
    )

    print(label, status)

    if status != 200:
        raise RuntimeError(
            f"{label} başarısız: {status}"
        )

status, listed = request(
    "GET",
    (
        "/api/syk-ui/research"
        f"?project_id={project['project_id']}"
    ),
)

print("RESEARCH_LIST_HTTP", status)

if status != 200:
    raise RuntimeError(
        f"Araştırmalar listelenemedi: {status}"
    )

if int(listed["count"]) != 1:
    raise RuntimeError(
        "Araştırma listesi beklenen sayıda değil."
    )

print(
    "RESEARCH_RUNTIME_CANLI_HTTP_OK"
)