"""SyKaşif canlı cihaz iletişimi doğrulaması."""

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

    from syk_core.runtime_device_link import (
        TerminalCihazAnahtarlari,
        terminale_cihaz_iletisimini_bagla,
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

    terminale_cihaz_iletisimini_bagla(
        terminal,
        anahtarlar=TerminalCihazAnahtarlari(
            ana_masaustu="MASAUSTU-ANAHTARI",
            samsung_tablet="TABLET-ANAHTARI",
            iphone="IPHONE-ANAHTARI",
        ),
    )

    sunucu = CanliTerminalSunucusu(
        terminal.uygulama,
        ayarlar=CanliSunucuAyarlari(
            ana_makine="127.0.0.1",
            baglanti_noktasi=0,
            gunluk_seviyesi="warning",
        ),
    )

    with sunucu:
        durum, saglik = json_istegi(
            sunucu.ana_adres
            + "/cihaz-iletisimi/saglik"
        )

        if durum != 200:
            raise RuntimeError(
                "Cihaz iletişim sağlık yolu başarısız."
            )

        print(
            "CIHAZ_ILETISIMI_CANLI_DOGRULANDI"
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
