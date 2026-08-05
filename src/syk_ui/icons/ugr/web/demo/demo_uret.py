"""UGR dinamik ikon örnek sayfa üreticisi."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from syk_ui.icons.ugr.runtime import (
    IkonCalismaDurumu,
    IkonGorunumModu,
    UgrDinamikIkonServisi,
)
from syk_ui.icons.ugr.web import (
    UgrIkonWebRenderServisi,
)


def demo_uret(
    manifest: Path,
    cikti: Path,
    limit: int = 30,
) -> None:
    """Canlı ikon ön izleme sayfası üretir."""

    servis = UgrDinamikIkonServisi()
    servis.manifest_yukle(manifest)

    kayitlar = list(
        servis.kayit_defteri.tumu()
    )[:limit]

    durumlar = list(
        IkonCalismaDurumu
    )

    gorunumler = list(
        IkonGorunumModu
    )

    for indeks, kayit in enumerate(
        kayitlar
    ):
        servis.durum_degistir(
            kayit.ikon_kimligi,
            yeni_durum=(
                durumlar[
                    indeks
                    % len(durumlar)
                ]
            ),
            neden=(
                "UGR web runtime ön izleme."
            ),
            zorla=True,
        )

        servis.gorunum_modu_degistir(
            kayit.ikon_kimligi,
            gorunumler[
                indeks
                % len(gorunumler)
            ],
        )

    render = UgrIkonWebRenderServisi(
        servis
    )

    grid = render.grid_html_uret(
        kayitlar,
        baslik=(
            "SyKaşif UGR Dinamik İkon Runtime"
        ),
    )

    html = f"""<!doctype html>
<html lang="tr">
<head>
    <meta charset="utf-8">
    <meta
        name="viewport"
        content="width=device-width, initial-scale=1"
    >
    <title>SyKaşif UGR Dinamik İkonlar</title>
    <link
        rel="stylesheet"
        href="../static/css/ugr_dynamic_icons.css"
    >
    <style>
        html {{
            min-height: 100%;
            background: #07101a;
        }}

        body {{
            margin: 0;
            min-height: 100vh;
            padding: 32px;
            background:
                radial-gradient(
                    circle at 50% 0%,
                    rgba(45, 111, 146, 0.16),
                    transparent 50%
                ),
                linear-gradient(
                    180deg,
                    #0b1825,
                    #050a10
                );
            font-family:
                Inter,
                "Segoe UI",
                Arial,
                sans-serif;
        }}
    </style>
</head>
<body>
    {grid}
    <script
        src="../static/js/ugr_dynamic_icons.js"
    ></script>
</body>
</html>
"""

    cikti.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    cikti.write_text(
        html,
        encoding="utf-8",
    )


def parser_uret() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--manifest",
        required=True,
    )

    parser.add_argument(
        "--cikti",
        required=True,
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=30,
    )

    return parser


def main(
    argv: Sequence[str] | None = None,
) -> int:
    args = parser_uret().parse_args(
        argv
    )

    demo_uret(
        manifest=Path(args.manifest),
        cikti=Path(args.cikti),
        limit=args.limit,
    )

    print(
        "UGR_DYNAMIC_ICON_DEMO_CREATED"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
