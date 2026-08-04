from __future__ import annotations

from pathlib import Path
import json


rapor_yolu = Path(
    "artifacts/"
    "SYFINANS_PROTOTIP_KAPANIS_"
    "MIMARI_INCELEME.json"
)

rapor = json.loads(
    rapor_yolu.read_text(
        encoding="utf-8"
    )
)

runtime_adaylari = rapor.get(
    "runtime_adaylari",
    [],
)

tarayici_testleri = rapor.get(
    "tarayici_testleri",
    [],
)

bulgular = rapor.get(
    "bulgular",
    {},
)

http_yollari = bulgular.get(
    "http_yollari",
    [],
)

statik_yollar = bulgular.get(
    "statik_yollar",
    [],
)

finans_referanslari = bulgular.get(
    "finans_referanslari",
    [],
)


print(
    "RAPOR_SHA256",
    rapor.get(
        "rapor_sha256",
        "-",
    ),
)

print()
print(
    "=== EN GUCLU RUNTIME ADAYLARI ==="
)

for sira, kayit in enumerate(
    runtime_adaylari[:12],
    start=1,
):
    print(
        f"{sira:02d}",
        "PUAN",
        kayit.get(
            "puan",
            0,
        ),
        "DOSYA",
        kayit.get(
            "dosya",
            "-",
        ),
        "ISARETLER",
        ",".join(
            kayit.get(
                "isaretler",
                [],
            )
        ),
    )


print()
print(
    "=== MEVCUT HTTP YOLLARI ==="
)

for kayit in http_yollari[:50]:
    print(
        kayit.get(
            "dosya",
            "-",
        ),
        "SATIR",
        kayit.get(
            "satir",
            0,
        ),
        "YOL",
        kayit.get(
            "deger",
            "-",
        ),
    )


print()
print(
    "=== TARAYICI TESTLERI ==="
)

for kayit in tarayici_testleri[:30]:
    print(
        kayit.get(
            "dosya",
            "-",
        ),
        "ISARETLER",
        ",".join(
            kayit.get(
                "isaretler",
                [],
            )
        ),
    )


print()
print(
    "=== STATIK ARAYUZ YOLLARI ==="
)

for kayit in statik_yollar[:40]:
    print(
        kayit.get(
            "dosya",
            "-",
        ),
        "SATIR",
        kayit.get(
            "satir",
            0,
        ),
        "DEGER",
        kayit.get(
            "deger",
            "-",
        ),
    )


print()
print(
    "=== MEVCUT FINANS REFERANSLARI ==="
)

for kayit in finans_referanslari[:40]:
    print(
        kayit.get(
            "dosya",
            "-",
        ),
        "SATIR",
        kayit.get(
            "satir",
            0,
        ),
        "DEGER",
        kayit.get(
            "deger",
            "-",
        ),
    )


aday_dosya = (
    runtime_adaylari[0].get(
        "dosya"
    )
    if runtime_adaylari
    else None
)

if not aday_dosya:
    raise RuntimeError(
        "Uygun runtime giriş noktası bulunamadı."
    )

aday_yolu = Path(
    aday_dosya
)

if not aday_yolu.is_file():
    raise FileNotFoundError(
        aday_yolu
    )

print()
print(
    "SECILEN_RUNTIME_ADAYI",
    aday_yolu.as_posix(),
)

print(
    "RUNTIME_HEDEF_SECIMI_OK"
)
