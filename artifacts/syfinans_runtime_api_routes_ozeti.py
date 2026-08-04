from __future__ import annotations

from pathlib import Path
import json


rapor_yolu = Path(
    "artifacts/"
    "SYFINANS_RUNTIME_API_ROUTES_INCELEME.json"
)

rapor = json.loads(
    rapor_yolu.read_text(
        encoding="utf-8"
    )
)


def yaz(
    baslik: str,
    kayitlar,
) -> None:
    print()
    print(
        f"=== {baslik} ==="
    )

    if not kayitlar:
        print(
            "BULUNAMADI"
        )
        return

    for kayit in kayitlar:
        print(
            json.dumps(
                kayit,
                ensure_ascii=False,
                sort_keys=True,
            )
        )


print(
    "HEDEF",
    rapor.get(
        "hedef",
        "-",
    ),
)

print(
    "HEDEF_SHA256",
    rapor.get(
        "hedef_sha256",
        "-",
    ),
)

print(
    "RAPOR_SHA256",
    rapor.get(
        "rapor_sha256",
        "-",
    ),
)

yaz(
    "ROUTER NESNELERI",
    rapor.get(
        "router_nesneleri",
        [],
    ),
)

yaz(
    "FASTAPI NESNELERI",
    rapor.get(
        "uygulama_nesneleri",
        [],
    ),
)

yaz(
    "HTTP YOLLARI",
    rapor.get(
        "http_yollari",
        [],
    ),
)

yaz(
    "INCLUDE ROUTER CAGRILARI",
    rapor.get(
        "include_router_cagrilari",
        [],
    ),
)

yaz(
    "MOUNT CAGRILARI",
    rapor.get(
        "mount_cagrilari",
        [],
    ),
)

fonksiyonlar = rapor.get(
    "fonksiyonlar",
    [],
)

ilgili_fonksiyonlar = [
    kayit
    for kayit in fonksiyonlar
    if any(
        ifade in str(
            kayit.get(
                "ad",
                "",
            )
        ).casefold()
        for ifade in (
            "router",
            "route",
            "api",
            "app",
            "runtime",
            "screen",
            "health",
            "snapshot",
        )
    )
]

yaz(
    "ILGILI FONKSIYONLAR",
    ilgili_fonksiyonlar,
)

print()
print(
    "SYFINANS_RUNTIME_API_ROUTES_OZETI_OK"
)
