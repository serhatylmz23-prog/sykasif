from __future__ import annotations

import ast
from pathlib import Path

from fastapi.testclient import TestClient

from syk_simulasyon.runtime_fastapi_sunucusu import (
    uygulama_olustur,
)


KAYNAK = Path(
    "src/syk_simulasyon/runtime_fastapi_sunucusu.py"
)

ISARET = (
    "# SYK_UI_SCREEN_UYUMLULUK_YOLU"
)

TERCIH_SIRASI = (
    "/syk-ui",
    "/ui",
    "/runtime-ui",
    "/ui/runtime",
    "/dashboard",
    "/panel",
)


def html_hedefini_bul() -> str:
    uygulama = uygulama_olustur()

    mevcut_yollar = {
        getattr(route, "path", None)
        for route in uygulama.router.routes
    }

    if "/syk-ui-screen" in mevcut_yollar:
        return "/syk-ui-screen"

    adaylar: list[str] = []

    for tercih in TERCIH_SIRASI:
        if tercih in mevcut_yollar:
            adaylar.append(tercih)

    for yol in sorted(
        yol
        for yol in mevcut_yollar
        if isinstance(yol, str)
    ):
        kucuk = yol.lower()

        if yol.startswith("/api/"):
            continue

        if yol == "/syk-ui-screen":
            continue

        if any(
            kelime in kucuk
            for kelime in (
                "ui",
                "screen",
                "panel",
                "dashboard",
                "runtime",
            )
        ):
            if yol not in adaylar:
                adaylar.append(yol)

    with TestClient(
        uygulama,
        follow_redirects=True,
    ) as istemci:
        for yol in adaylar:
            try:
                yanit = istemci.get(yol)
            except Exception:
                continue

            icerik_turu = yanit.headers.get(
                "content-type",
                "",
            ).lower()

            if (
                yanit.status_code == 200
                and "text/html" in icerik_turu
            ):
                print(
                    f"GERCEK_UI_HEDEFI={yol}"
                )
                return yol

    raise RuntimeError(
        "HTTP 200 ve text/html döndüren gerçek UI yolu bulunamadı. "
        f"ADAYLAR={adaylar}"
    )


def onar(
    hedef: str,
) -> None:
    kaynak = KAYNAK.read_text(
        encoding="utf-8-sig"
    )

    if ISARET in kaynak:
        print(
            "SYK_UI_SCREEN_UYUMLULUK_YOLU_ZATEN_VAR"
        )
        return

    agac = ast.parse(
        kaynak,
        filename=str(KAYNAK),
    )

    uygulama_fonksiyonu = next(
        (
            node
            for node in agac.body
            if isinstance(
                node,
                (
                    ast.FunctionDef,
                    ast.AsyncFunctionDef,
                ),
            )
            and node.name == "uygulama_olustur"
        ),
        None,
    )

    if uygulama_fonksiyonu is None:
        raise RuntimeError(
            "uygulama_olustur fonksiyonu bulunamadı."
        )

    return_dugumleri = [
        node
        for node in uygulama_fonksiyonu.body
        if isinstance(node, ast.Return)
    ]

    if not return_dugumleri:
        raise RuntimeError(
            "uygulama_olustur içinde üst seviye return bulunamadı."
        )

    return_satiri = return_dugumleri[-1].lineno

    satirlar = kaynak.splitlines()

    blok = [
        "    # SYK_UI_SCREEN_UYUMLULUK_YOLU",
        "    if not any(",
        '        getattr(route, "path", None) == "/syk-ui-screen"',
        "        for route in uygulama.router.routes",
        "    ):",
        "        from fastapi.responses import RedirectResponse",
        "",
        "        @uygulama.get(",
        '            "/syk-ui-screen",',
        "            include_in_schema=False,",
        "        )",
        "        async def syk_ui_screen_uyumluluk_yolu():",
        "            return RedirectResponse(",
        f'                url="{hedef}",',
        "                status_code=307,",
        "            )",
        "",
    ]

    yeni_satirlar = (
        satirlar[: return_satiri - 1]
        + blok
        + satirlar[return_satiri - 1 :]
    )

    yeni_kaynak = "\n".join(
        yeni_satirlar
    ) + "\n"

    ast.parse(
        yeni_kaynak,
        filename=str(KAYNAK),
    )

    KAYNAK.write_text(
        yeni_kaynak,
        encoding="utf-8",
    )

    print(
        "SYK_UI_SCREEN_UYUMLULUK_YOLU_EKLENDI"
    )
    print(
        f"SYK_UI_SCREEN_HEDEFI={hedef}"
    )


def main() -> int:
    hedef = html_hedefini_bul()

    if hedef == "/syk-ui-screen":
        print(
            "SYK_UI_SCREEN_ZATEN_CALISIYOR"
        )
        return 0

    onar(hedef)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
