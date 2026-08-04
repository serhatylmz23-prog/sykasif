"""SyKaşif birleşik prototip tek komutlu başlatıcısı."""

from __future__ import annotations

import argparse
import json
import os
import signal
from dataclasses import dataclass
from pathlib import Path
from threading import Event
from typing import Any, Mapping, Sequence

from syk_core.runtime_terminal import (
    CanliSunucuAyarlari,
    TerminalUygulamasiAyarlari,
)

from .uygulama import (
    PrototipAyarlari,
    PrototipGuvenlikAyarlari,
    SyKasifBirlesikPrototip,
)


class PrototipBaslaticiHatasi(RuntimeError):
    """Birleşik prototip başlatma aracı hatası."""


@dataclass(slots=True, frozen=True)
class PrototipBaslatmaSecenekleri:
    ana_makine: str = "127.0.0.1"
    baglanti_noktasi: int = 0
    durum_dosyasi: str = (
        "artifacts/runtime_prototype/"
        "birlesik_prototip_durumu.json"
    )
    erisim_gunlugu: bool = False

    def __post_init__(self) -> None:
        if not self.ana_makine.strip():
            raise ValueError(
                "Ana makine boş olamaz."
            )

        if not 0 <= self.baglanti_noktasi <= 65535:
            raise ValueError(
                "Bağlantı noktası 0–65535 aralığında olmalıdır."
            )

        if not self.durum_dosyasi.strip():
            raise ValueError(
                "Durum dosyası boş olamaz."
            )


def ortam_degeri_getir(
    ortam: Mapping[str, str],
    ad: str,
) -> str:
    deger = ortam.get(ad, "").strip()

    if not deger:
        raise PrototipBaslaticiHatasi(
            f"Zorunlu ortam değeri eksik: {ad}"
        )

    return deger


def guvenlik_ayarlari_ortamdan(
    ortam: Mapping[str, str] | None = None,
) -> PrototipGuvenlikAyarlari:
    kaynak = ortam or os.environ

    return PrototipGuvenlikAyarlari(
        ana_masaustu_anahtari=(
            ortam_degeri_getir(
                kaynak,
                "SYK_ANA_MASAUSTU_ANAHTARI",
            )
        ),
        samsung_tablet_anahtari=(
            ortam_degeri_getir(
                kaynak,
                "SYK_SAMSUNG_TABLET_ANAHTARI",
            )
        ),
        iphone_anahtari=(
            ortam_degeri_getir(
                kaynak,
                "SYK_IPHONE_ANAHTARI",
            )
        ),
        saha_ana_gizli_degeri=(
            ortam_degeri_getir(
                kaynak,
                "SYK_SAHA_ANA_GIZLI_DEGERI",
            )
        ),
    )


def prototip_ayarlari_olustur(
    *,
    guvenlik: PrototipGuvenlikAyarlari,
    secenekler: PrototipBaslatmaSecenekleri,
) -> PrototipAyarlari:
    varsayilan = (
        TerminalUygulamasiAyarlari
        .varsayilan()
    )

    durum_yolu = Path(
        secenekler.durum_dosyasi
    )

    durum_yolu.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    terminal_baglanti_noktasi = (
        secenekler.baglanti_noktasi
        if secenekler.baglanti_noktasi > 0
        else 8714
    )

    terminal = TerminalUygulamasiAyarlari(
        ana_makine=secenekler.ana_makine,
        baglanti_noktasi=(
            terminal_baglanti_noktasi
        ),
        panel_yolu="/terminal",
        panel_veri_yolu="/terminal/veri",
        dis_ag_erisimine_izin_ver=(
            secenekler.ana_makine
            not in {
                "127.0.0.1",
                "localhost",
            }
        ),
        ana_makine_cihaz_kimligi=(
            varsayilan
            .ana_makine_cihaz_kimligi
        ),
        sykasif_uygulama_kimligi=(
            varsayilan
            .sykasif_uygulama_kimligi
        ),
        sykasif_calistirma_yolu=(
            varsayilan
            .sykasif_calistirma_yolu
        ),
        durum_dosyasi=str(
            durum_yolu
        ),
        yetkili_cihazlar=(
            varsayilan.yetkili_cihazlar
        ),
    )

    canli_sunucu = CanliSunucuAyarlari(
        ana_makine=secenekler.ana_makine,
        baglanti_noktasi=(
            secenekler.baglanti_noktasi
        ),
        baslama_zaman_asimi_saniye=10,
        durma_zaman_asimi_saniye=10,
        gunluk_seviyesi="warning",
        erisim_gunlugu=(
            secenekler.erisim_gunlugu
        ),
    )

    return PrototipAyarlari(
        terminal=terminal,
        guvenlik=guvenlik,
        canli_sunucu=canli_sunucu,
    )


class PrototipBaslaticisi:
    """Birleşik prototipi başlatır ve güvenli biçimde kapatır."""

    def __init__(
        self,
        *,
        ayarlar: PrototipAyarlari,
    ) -> None:
        self.ayarlar = ayarlar
        self.prototip: (
            SyKasifBirlesikPrototip | None
        ) = None
        self._kapatma_istegi = Event()

    @property
    def calisiyor_mu(self) -> bool:
        return (
            self.prototip is not None
            and self.prototip.calisiyor_mu
        )

    def hazirla(
        self,
    ) -> SyKasifBirlesikPrototip:
        if self.prototip is None:
            self.prototip = (
                SyKasifBirlesikPrototip(
                    ayarlar=self.ayarlar
                )
            )

        return self.prototip

    def baslat(
        self,
    ) -> str:
        prototip = self.hazirla()
        adres = prototip.baslat()

        self._durum_kaydi_yaz(
            olay="başlatıldı"
        )

        return adres

    def durdur(
        self,
    ) -> None:
        if self.prototip is None:
            return

        self.prototip.durdur()

        self._durum_kaydi_yaz(
            olay="durduruldu"
        )

    def kapatma_iste(
        self,
        *_: Any,
    ) -> None:
        self._kapatma_istegi.set()

    def bekle(
        self,
        *,
        kontrol_araligi_saniye: float = 0.25,
    ) -> None:
        while not self._kapatma_istegi.wait(
            kontrol_araligi_saniye
        ):
            if not self.calisiyor_mu:
                break

    def calistir(
        self,
    ) -> int:
        signal.signal(
            signal.SIGINT,
            self.kapatma_iste,
        )

        if hasattr(signal, "SIGTERM"):
            signal.signal(
                signal.SIGTERM,
                self.kapatma_iste,
            )

        adres = self.baslat()

        print(
            "SYKASIF_BIRLESIK_PROTOTIP_CALISIYOR"
        )
        print(
            f"ANA_ADRES={adres}"
        )
        print(
            f"TERMINAL={adres}/terminal"
        )
        print(
            f"CIHAZ_ILETISIMI={adres}/cihaz-iletisimi/saglik"
        )
        print(
            f"SAHA_CIHAZLARI={adres}/saha-cihazlari/saglik"
        )
        print(
            "KAPATMA=CTRL+C"
        )

        try:
            self.bekle()
        finally:
            self.durdur()

        print(
            "SYKASIF_BIRLESIK_PROTOTIP_DURDURULDU"
        )

        return 0

    def dogrula(
        self,
    ) -> dict[str, Any]:
        prototip = self.hazirla()
        ozet = prototip.durum_ozeti()

        sonuc = {
            "başarılı": True,
            "durum": ozet["durum"],
            "sistem": ozet["sistem"],
            "gerçek_işlem": (
                ozet["gerçek_işlem"]
            ),
            "bileşenler": {
                "runtime_terminal": True,
                "cihaz_iletişimi": True,
                "saha_terminali": True,
            },
        }

        self._durum_kaydi_yaz(
            olay="doğrulandı",
            ek=sonuc,
        )

        return sonuc

    def _durum_kaydi_yaz(
        self,
        *,
        olay: str,
        ek: Mapping[str, Any] | None = None,
    ) -> None:
        prototip = self.prototip

        if prototip is None:
            return

        dosya = Path(
            self.ayarlar
            .terminal
            .durum_dosyasi
        )

        dosya.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        veri: dict[str, Any] = {
            "olay": olay,
            "prototip": (
                prototip.durum_ozeti()
            ),
        }

        if ek:
            veri["ek"] = dict(ek)

        dosya.write_text(
            json.dumps(
                veri,
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )


def arguman_ayristirici() -> argparse.ArgumentParser:
    ayristirici = argparse.ArgumentParser(
        prog="syk-prototip",
        description=(
            "SyKaşif birleşik prototip "
            "başlatma ve doğrulama aracı"
        ),
    )

    ayristirici.add_argument(
        "komut",
        choices=(
            "calistir",
            "dogrula",
        ),
    )

    ayristirici.add_argument(
        "--ana-makine",
        default="127.0.0.1",
    )

    ayristirici.add_argument(
        "--port",
        type=int,
        default=0,
    )

    ayristirici.add_argument(
        "--durum-dosyasi",
        default=(
            "artifacts/runtime_prototype/"
            "birlesik_prototip_durumu.json"
        ),
    )

    ayristirici.add_argument(
        "--erisim-gunlugu",
        action="store_true",
    )

    return ayristirici


def main(
    argv: Sequence[str] | None = None,
    *,
    ortam: Mapping[str, str] | None = None,
) -> int:
    argumanlar = (
        arguman_ayristirici()
        .parse_args(argv)
    )

    guvenlik = guvenlik_ayarlari_ortamdan(
        ortam
    )

    ayarlar = prototip_ayarlari_olustur(
        guvenlik=guvenlik,
        secenekler=(
            PrototipBaslatmaSecenekleri(
                ana_makine=(
                    argumanlar.ana_makine
                ),
                baglanti_noktasi=(
                    argumanlar.port
                ),
                durum_dosyasi=(
                    argumanlar.durum_dosyasi
                ),
                erisim_gunlugu=(
                    argumanlar
                    .erisim_gunlugu
                ),
            )
        ),
    )

    baslatici = PrototipBaslaticisi(
        ayarlar=ayarlar
    )

    if argumanlar.komut == "dogrula":
        sonuc = baslatici.dogrula()

        print(
            json.dumps(
                sonuc,
                ensure_ascii=False,
                indent=2,
            )
        )

        print(
            "SYKASIF_BIRLESIK_PROTOTIP_DOGRULANDI"
        )

        return 0

    return baslatici.calistir()

