from __future__ import annotations

from pathlib import Path
import ast


ROOT = Path(".")
SRC = ROOT / "src"
TESTS = ROOT / "tests"

arananlar = {
    "niyet": [
        SRC / "syk_jarmin" / "runtime" / "intent_engine.py",
        SRC / "syk_jarmin" / "intent_engine.py",
    ],
    "ana_sayfa": [
        SRC / "syk_simulasyon" / "syk_ui_runtime"
        / "static" / "index.html",
    ],
    "mobil_sensor": [
        SRC / "syk_simulasyon" / "syk_ui_runtime"
        / "static" / "js" / "mobile_sensor_runtime.js",
        SRC / "syk_simulasyon" / "syk_ui_runtime"
        / "static" / "js" / "mobile_sensors.js",
    ],
    "dagitim": [
        ROOT / "pyproject.toml",
        TESTS / "test_pyproject_dagitim_sozlesmesi.py",
    ],
}

bulunanlar: dict[str, list[Path]] = {}

for baslik, adaylar in arananlar.items():
    bulunanlar[baslik] = [
        yol
        for yol in adaylar
        if yol.is_file()
    ]


print()
print("=== BULUNAN DOSYALAR ===")

for baslik, yollar in bulunanlar.items():
    print()
    print(baslik.upper())

    if not yollar:
        print("BULUNAMADI")
        continue

    for yol in yollar:
        print(yol.as_posix())


def yazdir(
    yol: Path,
    baslangic: int = 1,
    bitis: int | None = None,
) -> None:
    metin = yol.read_text(
        encoding="utf-8",
    )

    satirlar = metin.splitlines()

    if bitis is None:
        bitis = len(satirlar)

    print()
    print("=" * 78)
    print(yol.as_posix())
    print("=" * 78)

    for numara in range(
        max(1, baslangic),
        min(len(satirlar), bitis) + 1,
    ):
        print(
            f"{numara:04d}: "
            f"{satirlar[numara - 1]}"
        )


# Niyet çözümleyicinin tamamı
for yol in bulunanlar["niyet"]:
    yazdir(yol)


# Dağıtım sözleşmesi
for yol in bulunanlar["dagitim"]:
    yazdir(yol)


# Ana sayfadaki mobil, GPS ve script satırları
for yol in bulunanlar["ana_sayfa"]:
    metin = yol.read_text(
        encoding="utf-8",
    )

    satirlar = metin.splitlines()

    eslesen = [
        numara
        for numara, satir in enumerate(
            satirlar,
            start=1,
        )
        if any(
            ifade.casefold()
            in satir.casefold()
            for ifade in (
                "GPS",
                "mobile",
                "sensor",
                "<script",
            )
        )
    ]

    print()
    print("=" * 78)
    print(yol.as_posix())
    print("=" * 78)

    for numara in eslesen:
        baslangic = max(
            1,
            numara - 3,
        )

        bitis = min(
            len(satirlar),
            numara + 3,
        )

        for satir_numarasi in range(
            baslangic,
            bitis + 1,
        ):
            print(
                f"{satir_numarasi:04d}: "
                f"{satirlar[satir_numarasi - 1]}"
            )

        print("---")


# Mobil sensör dosyasının tamamı
for yol in bulunanlar["mobil_sensor"]:
    yazdir(yol)


# static/js altında sensör benzeri tüm dosyalar
js_dizini = (
    SRC
    / "syk_simulasyon"
    / "syk_ui_runtime"
    / "static"
    / "js"
)

print()
print("=== MOBİL / SENSÖR JAVASCRIPT DOSYALARI ===")

if js_dizini.is_dir():
    for yol in sorted(
        js_dizini.glob("*.js")
    ):
        ad = yol.name.casefold()

        if any(
            ifade in ad
            for ifade in (
                "mobile",
                "sensor",
                "device",
                "control",
            )
        ):
            print(yol.as_posix())


# syk_jarmin kullanan importları çıkar
print()
print("=== SYK_JARMIN İÇE AKTARIMLARI ===")

for yol in sorted(
    ROOT.rglob("*.py")
):
    if any(
        parca in {
            ".venv",
            "__pycache__",
            "artifacts",
        }
        for parca in yol.parts
    ):
        continue

    try:
        metin = yol.read_text(
            encoding="utf-8",
        )
    except UnicodeDecodeError:
        continue

    if (
        "syk_jarmin"
        in metin
    ):
        print(yol.as_posix())


print()
print("KALAN_DORT_BASLIK_INCELEME_OK")
