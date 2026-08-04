"""SyKaşif canlı saha cihazı doğrulaması."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from urllib.request import Request, urlopen


def json_istegi(
    adres: str,
    *,
    yontem: str = "GET",
    veri: dict | None = None,
) -> tuple[int, dict]:
    ham = None
    basliklar = {
        "Accept": "application/json",
    }

    if veri is not None:
        ham = json.dumps(
            veri,
            ensure_ascii=False,
        ).encode("utf-8")

        basliklar["Content-Type"] = (
            "application/json; charset=utf-8"
        )

    istek = Request(
        adres,
        data=ham,
        headers=basliklar,
        method=yontem,
    )

    with urlopen(
        istek,
        timeout=5.0,
    ) as yanit:
        return (
            int(yanit.status),
            json.loads(
                yanit.read().decode("utf-8")
            ),
        )


def main() -> int:
    kok = Path(__file__).resolve().parents[1]
    kaynak = kok / "src"

    if str(kaynak) not in sys.path:
        sys.path.insert(
            0,
            str(kaynak),
        )

    from syk_core.runtime_field_link import (
        terminale_saha_cihazlarini_bagla,
    )
    from syk_core.runtime_terminal import (
        CanliSunucuAyarlari,
        CanliTerminalSunucusu,
        SyKasifTerminalUygulamasi,
        TerminalUygulamasiAyarlari,
    )

    terminal = SyKasifTerminalUygulamasi(
        ayarlar=(
            TerminalUygulamasiAyarlari
            .varsayilan()
        )
    )

    terminale_saha_cihazlarini_bagla(
        terminal,
        ana_gizli_deger=(
            "SPR-008-CANLI-DOGRULAMA-GIZLI"
        ),
    )

    sunucu = CanliTerminalSunucusu(
        terminal.uygulama,
        ayarlar=CanliSunucuAyarlari(
            ana_makine="127.0.0.1",
            baglanti_noktasi=0,
            gunluk_seviyesi="warning",
            erisim_gunlugu=False,
        ),
    )

    with sunucu:
        durum, saglik = json_istegi(
            sunucu.ana_adres
            + "/saha-cihazlari/saglik"
        )

        if durum != 200:
            raise RuntimeError(
                "Canlı saha cihazı sağlık yolu başarısız."
            )

        print(
            "SAHA_CIHAZI_CANLI_DOGRULANDI"
        )
        print(
            f"ANA_ADRES={sunucu.ana_adres}"
        )
        print(
            f"DURUM={saglik['durum']}"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
