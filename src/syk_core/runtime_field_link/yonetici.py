"""SyKaşif saha eşleştirme ve keşif birleşik yönetimi."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .eslestirme import (
    EslestirmeIstegi,
    SahaCihazAdayi,
    SahaCihazEslestirmeYoneticisi,
)
from .kesif import (
    KesfedilenCihaz,
    SahaCihazKesifYoneticisi,
)


class SahaCihazYonetimHatasi(RuntimeError):
    """Birleşik saha cihazı yönetim hatası."""


@dataclass(slots=True, frozen=True)
class SahaCihazBaglantiBilgisi:
    cihaz_kimligi: str
    cihaz_parmak_izi: str
    ag_adresi: str
    hizmet_noktasi: int

    def __post_init__(self) -> None:
        if not self.cihaz_kimligi.strip():
            raise ValueError(
                "Cihaz kimliği boş olamaz."
            )

        if not self.cihaz_parmak_izi.strip():
            raise ValueError(
                "Cihaz parmak izi boş olamaz."
            )

        if not self.ag_adresi.strip():
            raise ValueError(
                "Ağ adresi boş olamaz."
            )

        if not 1 <= self.hizmet_noktasi <= 65535:
            raise ValueError(
                "Hizmet noktası geçersiz."
            )


class SahaCihazYoneticisi:
    """Eşleştirme, keşif ve yeniden bağlantıyı tek noktadan yönetir."""

    def __init__(
        self,
        *,
        eslestirme: SahaCihazEslestirmeYoneticisi,
        kesif: SahaCihazKesifYoneticisi,
    ) -> None:
        self.eslestirme = eslestirme
        self.kesif = kesif

    def eslestirme_baslat(
        self,
        cihaz: SahaCihazAdayi,
    ) -> tuple[EslestirmeIstegi, str]:
        return (
            self.eslestirme
            .eslestirme_istegi_olustur(
                cihaz
            )
        )

    def eslestirmeyi_onayla(
        self,
        istek_kimligi: str,
        *,
        onaylayan: str,
    ) -> EslestirmeIstegi:
        return self.eslestirme.istegi_onayla(
            istek_kimligi,
            onaylayan=onaylayan,
        )

    def eslestirmeyi_tamamla(
        self,
        istek_kimligi: str,
        *,
        kod: str,
        baglanti: SahaCihazBaglantiBilgisi,
    ) -> tuple[EslestirmeIstegi, KesfedilenCihaz]:
        istek = (
            self.eslestirme
            .eslestirmeyi_tamamla(
                istek_kimligi,
                kod=kod,
                cihaz_parmak_izi=(
                    baglanti
                    .cihaz_parmak_izi
                ),
            )
        )

        if (
            istek.cihaz.cihaz_kimligi
            != baglanti.cihaz_kimligi
        ):
            raise SahaCihazYonetimHatasi(
                "Eşleştirme isteği ile bağlantı cihazı uyuşmuyor."
            )

        if not istek.oturum_anahtari:
            raise SahaCihazYonetimHatasi(
                "Eşleştirme oturum anahtarı üretmedi."
            )

        kesfedilen = self.kesif.cihaz_bildir(
            cihaz_kimligi=(
                istek.cihaz.cihaz_kimligi
            ),
            cihaz_adi=(
                istek.cihaz.cihaz_adi
            ),
            cihaz_turu=(
                istek.cihaz.cihaz_turu.value
            ),
            cihaz_parmak_izi=(
                istek.cihaz
                .cihaz_parmak_izi
            ),
            ag_adresi=(
                baglanti.ag_adresi
            ),
            hizmet_noktasi=(
                baglanti.hizmet_noktasi
            ),
            yetenekler=set(
                istek.cihaz.yetenekler
            ),
        )

        kesfedilen = self.kesif.cihazi_dogrula(
            cihaz_kimligi=(
                kesfedilen.cihaz_kimligi
            ),
            cihaz_parmak_izi=(
                kesfedilen
                .cihaz_parmak_izi
            ),
            oturum_anahtari=(
                istek.oturum_anahtari
            ),
        )

        return istek, kesfedilen

    def yeniden_baglan(
        self,
        *,
        baglanti: SahaCihazBaglantiBilgisi,
        oturum_anahtari: str,
    ) -> KesfedilenCihaz:
        return self.kesif.yeniden_baglan(
            cihaz_kimligi=(
                baglanti.cihaz_kimligi
            ),
            cihaz_parmak_izi=(
                baglanti
                .cihaz_parmak_izi
            ),
            oturum_anahtari=(
                oturum_anahtari
            ),
            ag_adresi=(
                baglanti.ag_adresi
            ),
            hizmet_noktasi=(
                baglanti.hizmet_noktasi
            ),
        )

    def zaman_asimlarini_kontrol_et(
        self,
    ) -> tuple[KesfedilenCihaz, ...]:
        return (
            self.kesif
            .zaman_asimlarini_kontrol_et()
        )

    def durum_ozeti(
        self,
    ) -> dict[str, Any]:
        return {
            "eşleştirme": (
                self.eslestirme.durum_ozeti()
            ),
            "keşif": (
                self.kesif.durum_ozeti()
            ),
            "sistem_durumu": "hazır",
        }
