"""SyKaşif canlı terminal doğrulama aracı."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from urllib.request import urlopen


def argumanlari_oku() -> argparse.Namespace:
    ayristirici = argparse.ArgumentParser(
        prog="syk-terminal-canli-dogrula",
        description=(
            "SyKaşif terminalini gerçek ağ yuvasında "
            "başlatır ve canlı yolları doğrular."
        ),
    )

    ayristirici.add_argument(
        "--ana-makine",
        default="127.0.0.1",
    )

    ayristirici.add_argument(
        "--baglanti-noktasi",
        type=int,
        default=0,
    )

    ayristirici.add_argument(
        "--beklet",
        action="store_true",
        help=(
            "Doğrulama sonrasında sunucuyu "
            "kullanıcı kapatana kadar açık tutar."
        ),
    )

    return ayristirici.parse_args()


def json_getir(
    adres: str,
) -> dict:
    with urlopen(
        adres,
        timeout=5.0,
    ) as yanit:
        return json.loads(
            yanit.read().decode(
                "utf-8"
            )
        )


def main() -> int:
    args = argumanlari_oku()

    kok = Path(__file__).resolve().parents[1]
    kaynak = kok / "src"

    if str(kaynak) not in sys.path:
        sys.path.insert(
            0,
            str(kaynak),
        )

    from syk_core.runtime_terminal import (
        CalismaKipi,
        CanliSunucuAyarlari,
        CanliTerminalSunucusu,
        SyKasifTerminalUygulamasi,
        TerminalUygulamasiAyarlari,
    )

    varsayilan = (
        TerminalUygulamasiAyarlari
        .varsayilan()
    )

    ayarlar = TerminalUygulamasiAyarlari(
        calisma_kipi=(
            CalismaKipi.LABORATUVAR
        ),
        ana_makine=args.ana_makine,
        baglanti_noktasi=(
            args.baglanti_noktasi
            if args.baglanti_noktasi > 0
            else 8014
        ),
        panel_yolu=(
            varsayilan.panel_yolu
        ),
        panel_veri_yolu=(
            varsayilan.panel_veri_yolu
        ),
        dis_ag_erisimine_izin_ver=False,
        ana_makine_cihaz_kimligi=(
            varsayilan
            .ana_makine_cihaz_kimligi
        ),
        sykasif_uygulama_kimligi=(
            varsayilan
            .sykasif_uygulama_kimligi
        ),
        sykasif_calistirma_yolu=str(
            kok
        ),
        durum_dosyasi=(
            "artifacts/syk_core_parca_006/"
            "canli_terminal_durumu.json"
        ),
        yetkili_cihazlar=(
            varsayilan.yetkili_cihazlar
        ),
    )

    sistem = SyKasifTerminalUygulamasi(
        ayarlar=ayarlar
    )

    sunucu = CanliTerminalSunucusu(
        sistem.uygulama,
        ayarlar=CanliSunucuAyarlari(
            ana_makine=args.ana_makine,
            baglanti_noktasi=(
                args.baglanti_noktasi
            ),
            gunluk_seviyesi="warning",
            erisim_gunlugu=False,
        ),
    )

    try:
        sunucu.baslat()

        saglik = json_getir(
            sunucu.ana_adres
            + "/saglik"
        )

        panel = json_getir(
            sunucu.ana_adres
            + "/terminal/veri"
        )

        if saglik.get(
            "durum"
        ) != "sağlıklı":
            raise RuntimeError(
                "Canlı sağlık doğrulaması başarısız."
            )

        if not panel.get(
            "başarılı"
        ):
            raise RuntimeError(
                "Canlı terminal paneli doğrulanamadı."
            )

        print(
            "CANLI_TERMINAL_DOGRULANDI"
        )
        print(
            f"ANA_ADRES={sunucu.ana_adres}"
        )
        print(
            f"PANEL={sunucu.ana_adres}/terminal"
        )
        print(
            f"SAGLIK={saglik['durum']}"
        )
        print(
            "CIHAZ_SAYISI="
            f"{panel['panel']['toplam_cihaz_sayısı']}"
        )

        if args.beklet:
            print(
                "SUNUCU_ACIK_TUTULUYOR"
            )
            print(
                "DURDURMAK_ICIN_CTRL_C"
            )

            while True:
                input()

        return 0

    except KeyboardInterrupt:
        print(
            "CANLI_TERMINAL_KULLANICI_TARAFINDAN_DURDURULDU"
        )
        return 0

    finally:
        sunucu.durdur()


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
