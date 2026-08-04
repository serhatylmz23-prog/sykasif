"""Saha cihazı yönetiminin Runtime Terminal birleşimi."""

from __future__ import annotations

from typing import Any

from syk_core.runtime_terminal import (
    SyKasifTerminalUygulamasi,
)

from .api import SahaCihazAgGecidi
from .eslestirme import (
    SahaCihazEslestirmeYoneticisi,
)
from .kesif import (
    SahaCihazKesifYoneticisi,
)
from .yonetici import (
    SahaCihazYoneticisi,
)


class SahaTerminalEntegrasyonHatasi(RuntimeError):
    """Saha cihazı ve Runtime Terminal birleşim hatası."""


class SahaTerminalKoprusu:
    """Saha cihazı ağ geçidini Runtime Terminal'e bağlar."""

    def __init__(
        self,
        terminal: SyKasifTerminalUygulamasi,
        *,
        ana_gizli_deger: str,
        kok_yol: str = "/saha-cihazlari",
        kod_gecerlilik_dakikasi: int = 10,
        azami_deneme_sayisi: int = 5,
        cevrimdisi_suresi_saniye: int = 30,
        kayit_silme_suresi_dakika: int = 60,
    ) -> None:
        if not ana_gizli_deger.strip():
            raise SahaTerminalEntegrasyonHatasi(
                "Saha terminali ana gizli değeri boş olamaz."
            )

        self.terminal = terminal

        self.yonetici = SahaCihazYoneticisi(
            eslestirme=(
                SahaCihazEslestirmeYoneticisi(
                    saat=terminal._saat,
                    kod_gecerlilik_dakikasi=(
                        kod_gecerlilik_dakikasi
                    ),
                    azami_deneme_sayisi=(
                        azami_deneme_sayisi
                    ),
                    ana_gizli_deger=(
                        ana_gizli_deger
                    ),
                )
            ),
            kesif=SahaCihazKesifYoneticisi(
                saat=terminal._saat,
                cevrimdisi_suresi_saniye=(
                    cevrimdisi_suresi_saniye
                ),
                kayit_silme_suresi_dakika=(
                    kayit_silme_suresi_dakika
                ),
            ),
        )

        self.ag_gecidi = SahaCihazAgGecidi(
            self.yonetici,
            uygulama=terminal.uygulama,
            kok_yol=kok_yol,
        )

        terminal.uygulama.state.saha_terminal_koprusu = (
            self
        )

    def zaman_asimlarini_kontrol_et(
        self,
    ) -> dict[str, Any]:
        cihazlar = (
            self.yonetici
            .zaman_asimlarini_kontrol_et()
        )

        return {
            "değişen_cihaz_sayısı": len(
                cihazlar
            ),
            "cihazlar": [
                cihaz.sozluk()
                for cihaz in cihazlar
            ],
        }

    def durum_ozeti(
        self,
    ) -> dict[str, Any]:
        return {
            "durum": "hazır",
            "runtime_terminal": (
                self.terminal.durum_ozeti()
            ),
            "saha_cihazları": (
                self.yonetici.durum_ozeti()
            ),
        }


def terminale_saha_cihazlarini_bagla(
    terminal: SyKasifTerminalUygulamasi,
    *,
    ana_gizli_deger: str,
    kok_yol: str = "/saha-cihazlari",
) -> SahaTerminalKoprusu:
    return SahaTerminalKoprusu(
        terminal,
        ana_gizli_deger=ana_gizli_deger,
        kok_yol=kok_yol,
    )
