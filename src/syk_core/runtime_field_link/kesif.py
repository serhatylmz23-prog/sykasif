"""SyKaşif yerel saha cihazı keşfi ve yeniden bağlantı katmanı."""

from __future__ import annotations

import hashlib
import hmac
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any, Callable


class SahaKesifHatasi(RuntimeError):
    """Saha cihazı keşif ve bağlantı hatası."""


class KesifDurumu(str, Enum):
    YENI = "yeni"
    GORULDU = "görüldü"
    DOGRULANDI = "doğrulandı"
    BAGLI = "bağlı"
    BEKLIYOR = "bekliyor"
    CEVRIMDISI = "çevrimdışı"
    REDDEDILDI = "reddedildi"


@dataclass(slots=True)
class KesfedilenCihaz:
    cihaz_kimligi: str
    cihaz_adi: str
    cihaz_turu: str
    cihaz_parmak_izi: str
    ag_adresi: str
    hizmet_noktasi: int
    ilk_gorulme_zamani: datetime
    son_gorulme_zamani: datetime
    durum: KesifDurumu = KesifDurumu.YENI
    yetenekler: frozenset[str] = field(
        default_factory=frozenset
    )
    oturum_anahtari_ozeti: str | None = None
    yeniden_baglanma_sayisi: int = 0
    son_hata: str | None = None

    def __post_init__(self) -> None:
        if not self.cihaz_kimligi.strip():
            raise ValueError(
                "Cihaz kimliği boş olamaz."
            )

        if not self.cihaz_adi.strip():
            raise ValueError(
                "Cihaz adı boş olamaz."
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
                "Hizmet noktası 1–65535 aralığında olmalıdır."
            )

        if self.ilk_gorulme_zamani.tzinfo is None:
            raise ValueError(
                "İlk görülme zamanı saat dilimi içermelidir."
            )

        if self.son_gorulme_zamani.tzinfo is None:
            raise ValueError(
                "Son görülme zamanı saat dilimi içermelidir."
            )

    @property
    def bagli_mi(self) -> bool:
        return self.durum is KesifDurumu.BAGLI

    def sozluk(self) -> dict[str, Any]:
        return {
            "cihaz_kimliği": self.cihaz_kimligi,
            "cihaz_adı": self.cihaz_adi,
            "cihaz_türü": self.cihaz_turu,
            "cihaz_parmak_izi": (
                self.cihaz_parmak_izi
            ),
            "ağ_adresi": self.ag_adresi,
            "hizmet_noktası": (
                self.hizmet_noktasi
            ),
            "durum": self.durum.value,
            "ilk_görülme_zamanı": (
                self.ilk_gorulme_zamani.isoformat()
            ),
            "son_görülme_zamanı": (
                self.son_gorulme_zamani.isoformat()
            ),
            "yetenekler": sorted(
                self.yetenekler
            ),
            "oturum_anahtarı_kayıtlı": (
                self.oturum_anahtari_ozeti
                is not None
            ),
            "yeniden_bağlanma_sayısı": (
                self.yeniden_baglanma_sayisi
            ),
            "son_hata": self.son_hata,
        }


@dataclass(slots=True)
class KesifDenetimKaydi:
    zaman: datetime
    olay: str
    basarili: bool
    cihaz_kimligi: str
    aciklama: str | None = None

    def sozluk(self) -> dict[str, Any]:
        return {
            "zaman": self.zaman.isoformat(),
            "olay": self.olay,
            "başarılı": self.basarili,
            "cihaz_kimliği": self.cihaz_kimligi,
            "açıklama": self.aciklama,
        }


class SahaCihazKesifYoneticisi:
    """Yerel ağdaki yetkili saha cihazlarını takip eder."""

    def __init__(
        self,
        *,
        saat: Callable[[], datetime] | None = None,
        cevrimdisi_suresi_saniye: int = 30,
        kayit_silme_suresi_dakika: int = 60,
    ) -> None:
        if cevrimdisi_suresi_saniye <= 0:
            raise ValueError(
                "Çevrimdışı süresi sıfırdan büyük olmalıdır."
            )

        if kayit_silme_suresi_dakika <= 0:
            raise ValueError(
                "Kayıt silme süresi sıfırdan büyük olmalıdır."
            )

        self._saat = saat or (
            lambda: datetime.now(UTC)
        )

        self._cevrimdisi_suresi = timedelta(
            seconds=cevrimdisi_suresi_saniye
        )

        self._kayit_silme_suresi = timedelta(
            minutes=kayit_silme_suresi_dakika
        )

        self._cihazlar: dict[
            str,
            KesfedilenCihaz,
        ] = {}

        self._denetim: list[
            KesifDenetimKaydi
        ] = []

    @staticmethod
    def anahtar_ozeti(
        oturum_anahtari: str,
    ) -> str:
        if not oturum_anahtari:
            raise SahaKesifHatasi(
                "Oturum anahtarı boş olamaz."
            )

        return hashlib.sha256(
            oturum_anahtari.encode("utf-8")
        ).hexdigest()

    def cihaz_bildir(
        self,
        *,
        cihaz_kimligi: str,
        cihaz_adi: str,
        cihaz_turu: str,
        cihaz_parmak_izi: str,
        ag_adresi: str,
        hizmet_noktasi: int,
        yetenekler: set[str] | None = None,
    ) -> KesfedilenCihaz:
        simdi = self._saat()

        mevcut = self._cihazlar.get(
            cihaz_kimligi
        )

        if mevcut is None:
            cihaz = KesfedilenCihaz(
                cihaz_kimligi=cihaz_kimligi,
                cihaz_adi=cihaz_adi,
                cihaz_turu=cihaz_turu,
                cihaz_parmak_izi=(
                    cihaz_parmak_izi
                ),
                ag_adresi=ag_adresi,
                hizmet_noktasi=(
                    hizmet_noktasi
                ),
                ilk_gorulme_zamani=simdi,
                son_gorulme_zamani=simdi,
                durum=KesifDurumu.GORULDU,
                yetenekler=frozenset(
                    yetenekler or set()
                ),
            )

            self._cihazlar[
                cihaz_kimligi
            ] = cihaz

            self._kaydet(
                olay="cihaz_keşfedildi",
                basarili=True,
                cihaz=cihaz,
            )

            return cihaz

        if not hmac.compare_digest(
            mevcut.cihaz_parmak_izi,
            cihaz_parmak_izi,
        ):
            mevcut.durum = (
                KesifDurumu.REDDEDILDI
            )
            mevcut.son_hata = (
                "Cihaz parmak izi değişti."
            )

            self._kaydet(
                olay="cihaz_reddedildi",
                basarili=False,
                cihaz=mevcut,
                aciklama=mevcut.son_hata,
            )

            raise SahaKesifHatasi(
                "Kayıtlı cihazın parmak izi değiştirilemez."
            )

        onceki_durum = mevcut.durum

        mevcut.cihaz_adi = cihaz_adi
        mevcut.cihaz_turu = cihaz_turu
        mevcut.ag_adresi = ag_adresi
        mevcut.hizmet_noktasi = (
            hizmet_noktasi
        )
        mevcut.yetenekler = frozenset(
            yetenekler or set()
        )
        mevcut.son_gorulme_zamani = simdi
        mevcut.son_hata = None

        if (
            onceki_durum
            is KesifDurumu.CEVRIMDISI
        ):
            mevcut.yeniden_baglanma_sayisi += 1

        if mevcut.oturum_anahtari_ozeti:
            mevcut.durum = KesifDurumu.BAGLI
        else:
            mevcut.durum = KesifDurumu.GORULDU

        self._kaydet(
            olay="cihaz_yeniden_görüldü",
            basarili=True,
            cihaz=mevcut,
        )

        return mevcut

    def cihazi_dogrula(
        self,
        *,
        cihaz_kimligi: str,
        cihaz_parmak_izi: str,
        oturum_anahtari: str,
    ) -> KesfedilenCihaz:
        cihaz = self.cihaz_getir(
            cihaz_kimligi
        )

        if cihaz.durum is KesifDurumu.REDDEDILDI:
            raise SahaKesifHatasi(
                "Reddedilmiş cihaz doğrulanamaz."
            )

        if not hmac.compare_digest(
            cihaz.cihaz_parmak_izi,
            cihaz_parmak_izi,
        ):
            cihaz.son_hata = (
                "Cihaz parmak izi doğrulanamadı."
            )

            self._kaydet(
                olay="cihaz_doğrulaması_başarısız",
                basarili=False,
                cihaz=cihaz,
                aciklama=cihaz.son_hata,
            )

            raise SahaKesifHatasi(
                cihaz.son_hata
            )

        cihaz.oturum_anahtari_ozeti = (
            self.anahtar_ozeti(
                oturum_anahtari
            )
        )

        cihaz.durum = KesifDurumu.BAGLI
        cihaz.son_gorulme_zamani = (
            self._saat()
        )
        cihaz.son_hata = None

        self._kaydet(
            olay="cihaz_doğrulandı",
            basarili=True,
            cihaz=cihaz,
        )

        return cihaz

    def yeniden_baglan(
        self,
        *,
        cihaz_kimligi: str,
        cihaz_parmak_izi: str,
        oturum_anahtari: str,
        ag_adresi: str,
        hizmet_noktasi: int,
    ) -> KesfedilenCihaz:
        cihaz = self.cihaz_getir(
            cihaz_kimligi
        )

        if not cihaz.oturum_anahtari_ozeti:
            raise SahaKesifHatasi(
                "Cihaz için kayıtlı oturum anahtarı yok."
            )

        if not hmac.compare_digest(
            cihaz.cihaz_parmak_izi,
            cihaz_parmak_izi,
        ):
            raise SahaKesifHatasi(
                "Yeniden bağlantı parmak izi doğrulanamadı."
            )

        gelen_ozet = self.anahtar_ozeti(
            oturum_anahtari
        )

        if not hmac.compare_digest(
            cihaz.oturum_anahtari_ozeti,
            gelen_ozet,
        ):
            cihaz.son_hata = (
                "Yeniden bağlantı anahtarı doğrulanamadı."
            )

            self._kaydet(
                olay="yeniden_bağlantı_reddedildi",
                basarili=False,
                cihaz=cihaz,
                aciklama=cihaz.son_hata,
            )

            raise SahaKesifHatasi(
                cihaz.son_hata
            )

        cihaz.ag_adresi = ag_adresi
        cihaz.hizmet_noktasi = (
            hizmet_noktasi
        )
        cihaz.son_gorulme_zamani = (
            self._saat()
        )
        cihaz.durum = KesifDurumu.BAGLI
        cihaz.yeniden_baglanma_sayisi += 1
        cihaz.son_hata = None

        self._kaydet(
            olay="cihaz_yeniden_bağlandı",
            basarili=True,
            cihaz=cihaz,
        )

        return cihaz

    def zaman_asimlarini_kontrol_et(
        self,
    ) -> tuple[KesfedilenCihaz, ...]:
        simdi = self._saat()
        degisenler: list[
            KesfedilenCihaz
        ] = []

        for cihaz in self._cihazlar.values():
            if cihaz.durum in {
                KesifDurumu.REDDEDILDI,
                KesifDurumu.CEVRIMDISI,
            }:
                continue

            if (
                simdi
                - cihaz.son_gorulme_zamani
                >= self._cevrimdisi_suresi
            ):
                cihaz.durum = (
                    KesifDurumu.CEVRIMDISI
                )
                cihaz.son_hata = (
                    "Cihaz canlılık zaman aşımına uğradı."
                )
                degisenler.append(
                    cihaz
                )

                self._kaydet(
                    olay="cihaz_çevrimdışı",
                    basarili=False,
                    cihaz=cihaz,
                    aciklama=cihaz.son_hata,
                )

        return tuple(
            degisenler
        )

    def eski_kayitlari_temizle(
        self,
    ) -> tuple[str, ...]:
        simdi = self._saat()

        silinecekler = [
            cihaz_kimligi
            for cihaz_kimligi, cihaz
            in self._cihazlar.items()
            if (
                cihaz.durum
                is KesifDurumu.CEVRIMDISI
                and (
                    simdi
                    - cihaz.son_gorulme_zamani
                    >= self._kayit_silme_suresi
                )
            )
        ]

        for cihaz_kimligi in silinecekler:
            self._cihazlar.pop(
                cihaz_kimligi,
                None,
            )

        return tuple(
            sorted(silinecekler)
        )

    def cihaz_getir(
        self,
        cihaz_kimligi: str,
    ) -> KesfedilenCihaz:
        try:
            return self._cihazlar[
                cihaz_kimligi
            ]
        except KeyError as hata:
            raise SahaKesifHatasi(
                f"Keşfedilmiş cihaz bulunamadı: {cihaz_kimligi}"
            ) from hata

    def cihazlari_listele(
        self,
    ) -> tuple[KesfedilenCihaz, ...]:
        return tuple(
            self._cihazlar[kimlik]
            for kimlik in sorted(
                self._cihazlar
            )
        )

    def denetim_kayitlari(
        self,
    ) -> tuple[KesifDenetimKaydi, ...]:
        return tuple(
            self._denetim
        )

    def durum_ozeti(
        self,
    ) -> dict[str, Any]:
        cihazlar = self.cihazlari_listele()

        return {
            "keşfedilen_cihaz_sayısı": len(
                cihazlar
            ),
            "bağlı_cihaz_sayısı": sum(
                cihaz.bagli_mi
                for cihaz in cihazlar
            ),
            "çevrimdışı_cihaz_sayısı": sum(
                cihaz.durum
                is KesifDurumu.CEVRIMDISI
                for cihaz in cihazlar
            ),
            "reddedilen_cihaz_sayısı": sum(
                cihaz.durum
                is KesifDurumu.REDDEDILDI
                for cihaz in cihazlar
            ),
            "denetim_kaydı_sayısı": len(
                self._denetim
            ),
            "cihazlar": [
                cihaz.sozluk()
                for cihaz in cihazlar
            ],
        }

    def _kaydet(
        self,
        *,
        olay: str,
        basarili: bool,
        cihaz: KesfedilenCihaz,
        aciklama: str | None = None,
    ) -> None:
        self._denetim.append(
            KesifDenetimKaydi(
                zaman=self._saat(),
                olay=olay,
                basarili=basarili,
                cihaz_kimligi=(
                    cihaz.cihaz_kimligi
                ),
                aciklama=aciklama,
            )
        )
