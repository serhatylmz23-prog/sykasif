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
            body = response.read().decode("utf-8")

            return (
                response.status,
                json.loads(body),
            )

    except urllib.error.HTTPError as error:
        body = error.read().decode("utf-8")

        return (
            error.code,
            json.loads(body),
        )


status, created = request(
    "POST",
    "/api/syk-ui/projects",
    {
        "name": "DSP-0014 R1 Canlı Proje",
        "research_area": "Birleşik runtime doğrulaması",
        "description": "Route sırası canlı testi",
    },
)

print(
    "PROJECT_CREATE_HTTP",
    status,
)

if status != 201:
    raise RuntimeError(
        f"Proje oluşturulamadı: {status} {created}"
    )

project_id = str(
    created["project_id"]
)

status, listed = request(
    "GET",
    "/api/syk-ui/projects",
)

print(
    "PROJECT_LIST_HTTP",
    status,
)

if status != 200:
    raise RuntimeError(
        f"Proje listelenemedi: {status}"
    )

if int(listed["count"]) < 1:
    raise RuntimeError(
        "Proje listesi boş."
    )

status, activated = request(
    "PATCH",
    f"/api/syk-ui/projects/{project_id}/activate",
)

print(
    "PROJECT_ACTIVATE_HTTP",
    status,
)

if status != 200:
    raise RuntimeError(
        f"Proje aktifleştirilemedi: {status}"
    )

if activated["active"] is not True:
    raise RuntimeError(
        "Proje aktif duruma geçmedi."
    )

status, archived = request(
    "PATCH",
    f"/api/syk-ui/projects/{project_id}/archive",
)

print(
    "PROJECT_ARCHIVE_HTTP",
    status,
)

if status != 200:
    raise RuntimeError(
        f"Proje arşivlenemedi: {status}"
    )

if archived["status"] != "archived":
    raise RuntimeError(
        "Proje arşiv durumuna geçmedi."
    )

print(
    "PROJECT_RUNTIME_CANLI_HTTP_OK"
)