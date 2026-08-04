"""Cihazlar arası iletişimin Runtime Terminal ile birleşimi."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from syk_core.runtime_terminal import (
    SyKasifTerminalUygulamasi,
)

from .api import CihazIletisimAgGecidi
from .cihaz_yonetici import (
    CihazKomutu,
    YetkiliCihazKaydi,
    YetkiliCihazYoneticisi,
)
from .guvenlik import (
    CihazYetkisi,
    IslemYetkisi,
)


class TerminalCihazEntegrasyonHatasi(RuntimeError):
    """Runtime Terminal cihaz iletişim entegrasyonu hatası."""


@dataclass(slots=True, frozen=True)
class TerminalCihazAnahtarlari:
    ana_masaustu: str
    samsung_tablet: str
    iphone: str

    def __post_init__(self) -> None:
        if not self.ana_masaustu.strip():
            raise ValueError(
                "Ana masaüstü anahtarı boş olamaz."
            )

        if not self.samsung_tablet.strip():
            raise ValueError(
                "Samsung tablet anahtarı boş olamaz."
            )

        if not self.iphone.strip():
            raise ValueError(
                "iPhone anahtarı boş olamaz."
            )


class TerminalCihazIletisimKoprusu:
    """Runtime Terminal ile yetkili cihaz ağ geçidini birleştirir."""

    def __init__(
        self,
        terminal: SyKasifTerminalUygulamasi,
        *,
        anahtarlar: TerminalCihazAnahtarlari,
        kok_yol: str = "/cihaz-iletisimi",
    ) -> None:
        self.terminal = terminal
        self.anahtarlar = anahtarlar

        self.yonetici = YetkiliCihazYoneticisi(
            saat=terminal._saat
        )

        self._cihazlari_kaydet()
        self._isleyicileri_kaydet()

        self.ag_gecidi = CihazIletisimAgGecidi(
            self.yonetici,
            uygulama=terminal.uygulama,
            kok_yol=kok_yol,
        )

        terminal.uygulama.state.cihaz_iletisim_koprusu = (
            self
        )

    def _cihazlari_kaydet(
        self,
    ) -> None:
        ayarlar = {
            cihaz.cihaz_kimligi: cihaz
            for cihaz in (
                self.terminal
                .ayarlar
                .yetkili_cihazlar
            )
        }

        zorunlu_cihazlar = {
            "ANA-MASAUSTU",
            "SAMSUNG-TABLET",
            "IPHONE-8-PLUS",
        }

        eksikler = (
            zorunlu_cihazlar
            - set(ayarlar)
        )

        if eksikler:
            raise TerminalCihazEntegrasyonHatasi(
                "Terminal ayarlarında zorunlu cihazlar eksik: "
                + ", ".join(
                    sorted(eksikler)
                )
            )

        self.yonetici.cihaz_kaydet(
            YetkiliCihazKaydi(
                cihaz_kimligi="ANA-MASAUSTU",
                cihaz_parmak_izi=(
                    ayarlar[
                        "ANA-MASAUSTU"
                    ].cihaz_parmak_izi
                ),
                yetki=CihazYetkisi.KURUCU_KAAN,
                gizli_anahtar=(
                    self.anahtarlar
                    .ana_masaustu
                ),
                aciklama=(
                    ayarlar[
                        "ANA-MASAUSTU"
                    ].aciklama
                ),
            )
        )

        self.yonetici.cihaz_kaydet(
            YetkiliCihazKaydi(
                cihaz_kimligi="SAMSUNG-TABLET",
                cihaz_parmak_izi=(
                    ayarlar[
                        "SAMSUNG-TABLET"
                    ].cihaz_parmak_izi
                ),
                yetki=CihazYetkisi.BILGE_KAAN,
                gizli_anahtar=(
                    self.anahtarlar
                    .samsung_tablet
                ),
                aciklama=(
                    ayarlar[
                        "SAMSUNG-TABLET"
                    ].aciklama
                ),
            )
        )

        self.yonetici.cihaz_kaydet(
            YetkiliCihazKaydi(
                cihaz_kimligi="IPHONE-8-PLUS",
                cihaz_parmak_izi=(
                    ayarlar[
                        "IPHONE-8-PLUS"
                    ].cihaz_parmak_izi
                ),
                yetki=CihazYetkisi.ISLETMEN,
                gizli_anahtar=(
                    self.anahtarlar
                    .iphone
                ),
                aciklama=(
                    ayarlar[
                        "IPHONE-8-PLUS"
                    ].aciklama
                ),
            )
        )

    def _isleyicileri_kaydet(
        self,
    ) -> None:
        self.yonetici.isleyici_kaydet(
            IslemYetkisi.DURUM_OKU,
            self._durum_oku,
        )

        self.yonetici.isleyici_kaydet(
            IslemYetkisi.UYGULAMA_AC,
            self._uygulama_ac,
        )

        self.yonetici.isleyici_kaydet(
            IslemYetkisi.UYGULAMA_KAPAT,
            self._uygulama_kapat,
        )

        self.yonetici.isleyici_kaydet(
            IslemYetkisi.SISTEMI_DURDUR,
            self._sistemi_durdur,
        )

    def _durum_oku(
        self,
        komut: CihazKomutu,
    ) -> dict[str, Any]:
        return {
            "durum": "hazır",
            "hedef_cihaz_kimliği": (
                komut.hedef_cihaz_kimligi
            ),
            "runtime_terminal": (
                self.terminal.durum_ozeti()
            ),
        }

    def _uygulama_ac(
        self,
        komut: CihazKomutu,
    ) -> dict[str, Any]:
        uygulama_kimligi = str(
            komut.icerik.get(
                "uygulama_kimliği",
                self.terminal
                .ayarlar
                .sykasif_uygulama_kimligi,
            )
        )

        tanim = (
            self.terminal
            .cihaz_araci
            .uygulama_getir(
                uygulama_kimligi
            )
        )

        islem_kimligi = (
            self.terminal
            .uygulama_isletmeni
            .baslat(
                tanim
            )
        )

        return {
            "uygulama_kimliği": (
                uygulama_kimligi
            ),
            "durum": "açıldı",
            "işlem_kimliği": (
                islem_kimligi
            ),
            "gerçek_işlem": (
                self.terminal
                .uygulama_isletmeni
                .gercek_isleme_izin_ver
            ),
        }

    def _uygulama_kapat(
        self,
        komut: CihazKomutu,
    ) -> dict[str, Any]:
        uygulama_kimligi = str(
            komut.icerik.get(
                "uygulama_kimliği",
                self.terminal
                .ayarlar
                .sykasif_uygulama_kimligi,
            )
        )

        tanim = (
            self.terminal
            .cihaz_araci
            .uygulama_getir(
                uygulama_kimligi
            )
        )

        durum = (
            self.terminal
            .cihaz_araci
            .uygulama_durumu_getir(
                uygulama_kimligi
            )
        )

        basarili = (
            self.terminal
            .uygulama_isletmeni
            .kapat(
                tanim,
                durum,
            )
        )

        return {
            "uygulama_kimliği": (
                uygulama_kimligi
            ),
            "durum": (
                "kapatıldı"
                if basarili
                else "kapatılamadı"
            ),
            "başarılı": bool(
                basarili
            ),
            "gerçek_işlem": (
                self.terminal
                .uygulama_isletmeni
                .gercek_isleme_izin_ver
            ),
        }

    def _sistemi_durdur(
        self,
        komut: CihazKomutu,
    ) -> dict[str, Any]:
        self.terminal.guvenli_durdur()

        return {
            "durum": "güvenli_durduruldu",
            "gerekçe": komut.gerekce,
            "insan_onayı": (
                komut.insan_onayi
            ),
        }

    def durum_ozeti(
        self,
    ) -> dict[str, Any]:
        return {
            "durum": "hazır",
            "terminal": (
                self.terminal.durum_ozeti()
            ),
            "cihaz_iletişimi": (
                self.yonetici.durum_ozeti()
            ),
        }


def terminale_cihaz_iletisimini_bagla(
    terminal: SyKasifTerminalUygulamasi,
    *,
    anahtarlar: TerminalCihazAnahtarlari,
    kok_yol: str = "/cihaz-iletisimi",
) -> TerminalCihazIletisimKoprusu:
    return TerminalCihazIletisimKoprusu(
        terminal,
        anahtarlar=anahtarlar,
        kok_yol=kok_yol,
    )
