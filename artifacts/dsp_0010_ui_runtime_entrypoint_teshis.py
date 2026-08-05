from __future__ import annotations

import ast
from pathlib import Path
from typing import Any


ROOTS = (
    Path("src"),
    Path("tests"),
    Path("scripts"),
)

TERMS = (
    "8013",
    "syk-ui-screen",
    "SYK_UI_TEST_URL",
    "uvicorn",
    "subprocess.Popen",
    "subprocess.run",
    "pytest.fixture",
    "pytest_configure",
    "pytest_sessionstart",
    "base_url",
)

SUFFIXES = {
    ".py",
    ".ps1",
    ".toml",
    ".ini",
    ".yaml",
    ".yml",
    ".json",
}

rapor: list[str] = []


def yaz(*parcalar: Any) -> None:
    metin = " ".join(
        str(parca)
        for parca in parcalar
    )

    print(metin)
    rapor.append(metin)


def dosyalari_bul() -> list[Path]:
    sonuc: list[Path] = []

    for root in ROOTS:
        if not root.exists():
            continue

        for path in root.rglob("*"):
            if not path.is_file():
                continue

            if (
                path.suffix.lower() in SUFFIXES
                or path.name == "pyproject.toml"
            ):
                sonuc.append(path)

    pyproject = Path("pyproject.toml")

    if pyproject.is_file():
        sonuc.append(pyproject)

    return sorted(
        set(sonuc)
    )


def metin_oku(path: Path) -> str:
    for encoding in (
        "utf-8-sig",
        "utf-8",
        "cp1254",
    ):
        try:
            return path.read_text(
                encoding=encoding
            )
        except UnicodeDecodeError:
            continue

    return path.read_text(
        encoding="utf-8",
        errors="replace",
    )


dosyalar = dosyalari_bul()

yaz("=" * 78)
yaz("DSP-0010 UI RUNTIME ENTRYPOINT TESHISI")
yaz("=" * 78)
yaz("INCELENEN_DOSYA_SAYISI", len(dosyalar))

eslesmeler: list[
    tuple[Path, int, str]
] = []

for path in dosyalar:
    text = metin_oku(path)

    for number, line in enumerate(
        text.splitlines(),
        start=1,
    ):
        if any(
            term.casefold() in line.casefold()
            for term in TERMS
        ):
            eslesmeler.append(
                (
                    path,
                    number,
                    line.strip(),
                )
            )

yaz()
yaz("=== ANAHTAR ESLESMELER ===")

for path, number, line in eslesmeler:
    yaz(
        f"{path}:{number}:{line}"
    )

yaz()
yaz("=== PYTHON FASTAPI / UVICORN ADAYLARI ===")

for path in dosyalar:
    if path.suffix.lower() != ".py":
        continue

    text = metin_oku(path)

    try:
        tree = ast.parse(
            text,
            filename=str(path),
        )
    except SyntaxError as error:
        yaz(
            "AST_HATASI",
            path,
            error.lineno,
            error.msg,
        )
        continue

    aday = False
    detaylar: list[str] = []

    for node in ast.walk(tree):
        if isinstance(
            node,
            ast.Call,
        ):
            if isinstance(
                node.func,
                ast.Name,
            ) and node.func.id == "FastAPI":
                aday = True
                detaylar.append(
                    f"FastAPI SATIR {node.lineno}"
                )

            if isinstance(
                node.func,
                ast.Attribute,
            ) and node.func.attr in {
                "run",
                "Popen",
                "include_router",
                "mount",
            }:
                kaynak = ast.unparse(
                    node
                )

                if any(
                    token in kaynak
                    for token in (
                        "uvicorn",
                        "subprocess",
                        "include_router",
                        ".mount(",
                    )
                ):
                    aday = True
                    detaylar.append(
                        f"{node.func.attr} SATIR "
                        f"{node.lineno}: {kaynak}"
                    )

        if isinstance(
            node,
            ast.FunctionDef,
        ) and node.name in {
            "uygulama_olustur",
            "app_olustur",
            "create_app",
            "server",
            "sunucu",
            "live_server",
        }:
            aday = True
            detaylar.append(
                f"FONKSIYON {node.name} "
                f"SATIR {node.lineno}"
            )

    if aday:
        yaz()
        yaz("DOSYA", path)

        for detay in detaylar:
            yaz(" ", detay)

yaz()
yaz("=== TEST FIXTURE DOSYALARI ===")

for path in dosyalar:
    if (
        path.name == "conftest.py"
        or "fixture" in path.name.casefold()
        or "playwright" in path.name.casefold()
        or "sunucu" in path.name.casefold()
        or "server" in path.name.casefold()
    ):
        yaz(path)

yaz()
yaz("=== UI TEST HEDEFLERI ===")

for path in sorted(
    Path("tests").glob(
        "test_ui_*tarayici.py"
    )
):
    text = metin_oku(path)

    hedef_satirlari = [
        (
            number,
            line.strip(),
        )
        for number, line in enumerate(
            text.splitlines(),
            start=1,
        )
        if (
            "SYK_UI_TEST_URL" in line
            or "8013" in line
            or "syk-ui-screen" in line
        )
    ]

    yaz()
    yaz("TEST", path)

    for number, line in hedef_satirlari:
        yaz(
            f"  {number}: {line}"
        )

yaz()
yaz("=== ONCELIKLI ENTRYPOINT ADAYLARI ===")

adaylar = (
    Path(
        "src/syk_simulasyon/"
        "runtime_ui_sunucusu.py"
    ),
    Path(
        "src/syk_simulasyon/"
        "runtime_fastapi_sunucusu.py"
    ),
    Path(
        "src/syk_simulasyon/"
        "syk_ui.py"
    ),
)

for aday in adaylar:
    if not aday.is_file():
        yaz(
            "YOK",
            aday,
        )
        continue

    text = metin_oku(aday)

    yaz()
    yaz("ADAY", aday)
    yaz(
        "SYK_UI_SCREEN",
        "/syk-ui-screen" in text,
    )
    yaz(
        "UVICORN",
        "uvicorn" in text.casefold(),
    )
    yaz(
        "FASTAPI",
        "FastAPI(" in text,
    )
    yaz(
        "UYGULAMA_OLUSTUR",
        "uygulama_olustur" in text,
    )

Path(
    "artifacts/"
    "SYK_DSP_0010_UI_RUNTIME_ENTRYPOINT.txt"
).write_text(
    "\n".join(rapor) + "\n",
    encoding="utf-8",
)

yaz()
yaz(
    "SYK_DSP_0010_UI_RUNTIME_ENTRYPOINT_OK"
)