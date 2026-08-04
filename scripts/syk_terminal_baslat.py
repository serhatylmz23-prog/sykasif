"""SyKaşif Terminal Uygulaması başlatıcısı."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import uvicorn


def argumanlari_oku() -> argparse.Namespace:
    ayristirici = argparse.ArgumentParser(
        prog="syk-terminal",
        description=(
            "SyKaşif Türkçe terminal uygulamasını başlatır."
        ),
    )

    ayristirici.add_argument(
        "--ana-makine",
        default="127.0.0.1",
        help="Dinlenecek ana makine adresi.",
    )

    ayristirici.add_argument(
        "--baglanti-noktasi",
        type=int,
        default=8014,
        help="Dinlenecek bağlantı noktası.",
    )

    ayristirici.add_argument(
        "--yeniden-yukle",
        action="store_true",
        help="Geliştirme sırasında yeniden yüklemeyi açar.",
    )

    ayristirici.add_argument(
        "--dis-ag",
        action="store_true",
        help="Yerel ağ dışındaki erişime izin verir.",
    )

    ayristirici.add_argument(
        "--gercek-uygulama-islemleri",
        action="store_true",
        help="Gerçek uygulama açma ve kapatma işlemlerini açar.",
    )

    ayristirici.add_argument(
        "--gercek-sistem-islemleri",
        action="store_true",
        help="Gerçek sistem kapatma işlemlerini açar.",
    )

    return ayristirici.parse_args()


def main() -> int:
    args = argumanlari_oku()

    kok = Path(__file__).resolve().parents[1]

    if str(kok) not in sys.path:
        sys.path.insert(
            0,
            str(kok),
        )

    from syk_core.runtime_terminal import (
        CalismaKipi,
        SyKasifTerminalUygulamasi,
        TerminalUygulamasiAyarlari,
    )

    varsayilan = (
        TerminalUygulamasiAyarlari
        .varsayilan()
    )

    ayarlar = TerminalUygulamasiAyarlari(
        calisma_kipi=CalismaKipi.GELISTIRME,
        ana_makine=args.ana_makine,
        baglanti_noktasi=(
            args.baglanti_noktasi
        ),
        panel_yolu=(
            varsayilan.panel_yolu
        ),
        panel_veri_yolu=(
            varsayilan.panel_veri_yolu
        ),
        dis_ag_erisimine_izin_ver=(
            args.dis_ag
        ),
        yeniden_yukleme=(
            args.yeniden_yukle
        ),
        gunluk_seviyesi="info",
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
            varsayilan.durum_dosyasi
        ),
        yetkili_cihazlar=(
            varsayilan.yetkili_cihazlar
        ),
    )

    terminal_uygulamasi = (
        SyKasifTerminalUygulamasi(
            ayarlar=ayarlar,
            gercek_uygulama_islemlerine_izin_ver=(
                args.gercek_uygulama_islemleri
            ),
            gercek_sistem_islemlerine_izin_ver=(
                args.gercek_sistem_islemleri
            ),
        )
    )

    print(
        "SYKASIF_TERMINAL_BASLATILIYOR"
    )
    print(
        f"PANEL=http://{args.ana_makine}:"
        f"{args.baglanti_noktasi}"
        f"{ayarlar.panel_yolu}"
    )

    uvicorn.run(
        terminal_uygulamasi.uygulama,
        host=args.ana_makine,
        port=args.baglanti_noktasi,
        reload=False,
        log_level=ayarlar.gunluk_seviyesi,
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
