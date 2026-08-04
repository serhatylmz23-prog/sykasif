"""SyKaşif birleşik çalıştırılabilir prototip çekirdeği."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from syk_core.runtime_device_link import (
    TerminalCihazAnahtarlari,
    TerminalCihazIletisimKoprusu,
    terminale_cihaz_iletisimini_bagla,
)
from syk_core.runtime_field_link import (
    SahaTerminalKoprusu,
    terminale_saha_cihazlarini_bagla,
)
from syk_core.runtime_terminal import (
    CanliSunucuAyarlari,
    CanliTerminalSunucusu,
    SyKasifTerminalUygulamasi,
    TerminalUygulamasiAyarlari,
)


class PrototipHatasi(RuntimeError):
    """SyKaşif birleşik prototip hatası."""


class PrototipDurumu(str, Enum):
    HAZIRLANIYOR = "hazırlanıyor"
    HAZIR = "hazır"
    CALISIYOR = "çalışıyor"
    DURDURULDU = "durduruldu"
    HATA = "hata"


@dataclass(slots=True, frozen=True)
class PrototipGuvenlikAyarlari:
    ana_masaustu_anahtari: str
    samsung_tablet_anahtari: str
    iphone_anahtari: str
    saha_ana_gizli_degeri: str

    def __post_init__(self) -> None:
        degerler = {
            "Ana masaüstü anahtarı": (
                self.ana_masaustu_anahtari
            ),
            "Samsung tablet anahtarı": (
                self.samsung_tablet_anahtari
            ),
            "iPhone anahtarı": (
                self.iphone_anahtari
            ),
            "Saha ana gizli değeri": (
                self.saha_ana_gizli_degeri
            ),
        }

        for ad, deger in degerler.items():
            if not deger.strip():
                raise ValueError(
                    f"{ad} boş olamaz."
                )


@dataclass(slots=True, frozen=True)
class PrototipAyarlari:
    terminal: TerminalUygulamasiAyarlari
    guvenlik: PrototipGuvenlikAyarlari
    canli_sunucu: CanliSunucuAyarlari | None = None

    @classmethod
    def varsayilan(
        cls,
        *,
        guvenlik: PrototipGuvenlikAyarlari,
    ) -> "PrototipAyarlari":
        return cls(
            terminal=(
                TerminalUygulamasiAyarlari
                .varsayilan()
            ),
            guvenlik=guvenlik,
            canli_sunucu=CanliSunucuAyarlari(
                ana_makine="127.0.0.1",
                baglanti_noktasi=0,
                gunluk_seviyesi="warning",
                erisim_gunlugu=False,
            ),
        )


class SyKasifBirlesikPrototip:
    """Terminal, cihaz iletişimi ve saha bağlantısını birleştirir."""

    def __init__(
        self,
        *,
        ayarlar: PrototipAyarlari,
    ) -> None:
        self.ayarlar = ayarlar
        self.durum = (
            PrototipDurumu.HAZIRLANIYOR
        )
        self.son_hata: str | None = None

        try:
            self.terminal = (
                SyKasifTerminalUygulamasi(
                    ayarlar=ayarlar.terminal
                )
            )

            self.cihaz_iletisim_koprusu: (
                TerminalCihazIletisimKoprusu
            ) = terminale_cihaz_iletisimini_bagla(
                self.terminal,
                anahtarlar=(
                    TerminalCihazAnahtarlari(
                        ana_masaustu=(
                            ayarlar
                            .guvenlik
                            .ana_masaustu_anahtari
                        ),
                        samsung_tablet=(
                            ayarlar
                            .guvenlik
                            .samsung_tablet_anahtari
                        ),
                        iphone=(
                            ayarlar
                            .guvenlik
                            .iphone_anahtari
                        ),
                    )
                ),
            )

            self.saha_terminal_koprusu: (
                SahaTerminalKoprusu
            ) = terminale_saha_cihazlarini_bagla(
                self.terminal,
                ana_gizli_deger=(
                    ayarlar
                    .guvenlik
                    .saha_ana_gizli_degeri
                ),
            )

            self.canli_sunucu: (
                CanliTerminalSunucusu | None
            ) = None

            if ayarlar.canli_sunucu is not None:
                self.canli_sunucu = (
                    CanliTerminalSunucusu(
                        self.terminal.uygulama,
                        ayarlar=(
                            ayarlar.canli_sunucu
                        ),
                    )
                )

            self.terminal.uygulama.state.birlesik_prototip = (
                self
            )

            self.durum = PrototipDurumu.HAZIR

        except Exception as hata:
            self.durum = PrototipDurumu.HATA
            self.son_hata = str(hata)
            raise

    @property
    def calisiyor_mu(self) -> bool:
        return (
            self.durum
            is PrototipDurumu.CALISIYOR
        )

    @property
    def ana_adres(self) -> str | None:
        if self.canli_sunucu is None:
            return None

        if not self.canli_sunucu.calisiyor_mu:
            return None

        return self.canli_sunucu.ana_adres

    def baslat(self) -> str:
        if self.canli_sunucu is None:
            raise PrototipHatasi(
                "Canlı sunucu ayarları bulunmuyor."
            )

        if self.calisiyor_mu:
            return self.canli_sunucu.ana_adres

        try:
            self.canli_sunucu.baslat()
            self.durum = (
                PrototipDurumu.CALISIYOR
            )
            self.son_hata = None

            return self.canli_sunucu.ana_adres

        except Exception as hata:
            self.durum = PrototipDurumu.HATA
            self.son_hata = str(hata)
            raise PrototipHatasi(
                "Birleşik prototip başlatılamadı."
            ) from hata

    def durdur(self) -> None:
        try:
            if (
                self.canli_sunucu is not None
                and self.canli_sunucu.calisiyor_mu
            ):
                self.canli_sunucu.durdur()

            self.terminal.guvenli_durdur()
            self.durum = (
                PrototipDurumu.DURDURULDU
            )
            self.son_hata = None

        except Exception as hata:
            self.durum = PrototipDurumu.HATA
            self.son_hata = str(hata)
            raise PrototipHatasi(
                "Birleşik prototip güvenli durdurulamadı."
            ) from hata

    def zaman_asimlarini_kontrol_et(
        self,
    ) -> dict[str, Any]:
        saha = (
            self.saha_terminal_koprusu
            .zaman_asimlarini_kontrol_et()
        )

        cihaz_oturumlari = (
            self.cihaz_iletisim_koprusu
            .yonetici
            .zaman_asimlarini_kontrol_et()
        )

        return {
            "saha_cihazları": saha,
            "cihaz_oturumları": {
                "değişen_oturum_sayısı": len(
                    cihaz_oturumlari
                ),
                "oturumlar": [
                    oturum.sozluk()
                    for oturum
                    in cihaz_oturumlari
                ],
            },
        }

    def durum_ozeti(
        self,
    ) -> dict[str, Any]:
        return {
            "sistem": "SyKaşif",
            "bileşen": "birleşik_prototip",
            "durum": self.durum.value,
            "çalışıyor": self.calisiyor_mu,
            "ana_adres": self.ana_adres,
            "son_hata": self.son_hata,
            "runtime_terminal": (
                self.terminal.durum_ozeti()
            ),
            "cihaz_iletişimi": (
                self.cihaz_iletisim_koprusu
                .durum_ozeti()
            ),
            "saha_terminali": (
                self.saha_terminal_koprusu
                .durum_ozeti()
            ),
            "gerçek_işlem": (
                self.terminal
                .uygulama_isletmeni
                .gercek_isleme_izin_ver
            ),
        }

    def __enter__(
        self,
    ) -> "SyKasifBirlesikPrototip":
        self.baslat()
        return self

    def __exit__(
        self,
        exc_type,
        exc_value,
        traceback,
    ) -> None:
        self.durdur()


def birlesik_prototip_olustur(
    *,
    ayarlar: PrototipAyarlari,
) -> SyKasifBirlesikPrototip:
    return SyKasifBirlesikPrototip(
        ayarlar=ayarlar
    )
