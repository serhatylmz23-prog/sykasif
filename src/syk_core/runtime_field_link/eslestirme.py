"""SyKaşif saha cihazı güvenli eşleştirme katmanı."""

from __future__ import annotations

import hashlib
import hmac
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum
from secrets import randbelow, token_hex
from typing import Any, Callable
from uuid import uuid4


class SahaEslestirmeHatasi(RuntimeError):
    """Saha cihazı eşleştirme hatası."""


class SahaCihazTuru(str, Enum):
    ANA_MAKINE = "ana_makine"
    TABLET = "tablet"
    TELEFON = "telefon"
    DIZUSTU = "dizüstü"
    DRONE = "drone"
    SENSOR = "sensör"
    DIGER = "diğer"


class EslestirmeDurumu(str, Enum):
    ONAY_BEKLIYOR = "onay_bekliyor"
    ONAYLANDI = "onaylandı"
    TAMAMLANDI = "tamamlandı"
    REDDEDILDI = "reddedildi"
    SURESI_DOLDU = "süresi_doldu"


@dataclass(slots=True, frozen=True)
class SahaCihazAdayi:
    cihaz_kimligi: str
    cihaz_adi: str
    cihaz_turu: SahaCihazTuru
    cihaz_parmak_izi: str
    yerel_ag_adresi: str | None = None
    uygulama_surumu: str | None = None
    sistem_surumu: str | None = None
    yetenekler: frozenset[str] = field(
        default_factory=frozenset
    )

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

    def sozluk(self) -> dict[str, Any]:
        return {
            "cihaz_kimliği": self.cihaz_kimligi,
            "cihaz_adı": self.cihaz_adi,
            "cihaz_türü": self.cihaz_turu.value,
            "cihaz_parmak_izi": (
                self.cihaz_parmak_izi
            ),
            "yerel_ağ_adresi": (
                self.yerel_ag_adresi
            ),
            "uygulama_sürümü": (
                self.uygulama_surumu
            ),
            "sistem_sürümü": (
                self.sistem_surumu
            ),
            "yetenekler": sorted(
                self.yetenekler
            ),
        }


@dataclass(slots=True)
class EslestirmeIstegi:
    istek_kimligi: str
    cihaz: SahaCihazAdayi
    olusturulma_zamani: datetime
    sona_erme_zamani: datetime
    kod_ozeti: str
    azami_deneme_sayisi: int
    durum: EslestirmeDurumu = (
        EslestirmeDurumu.ONAY_BEKLIYOR
    )
    onaylayan: str | None = None
    onay_zamani: datetime | None = None
    tamamlanma_zamani: datetime | None = None
    reddetme_gerekcesi: str | None = None
    basarisiz_deneme_sayisi: int = 0
    oturum_anahtari: str | None = None
    son_hata: str | None = None

    @property
    def tamamlandi_mi(self) -> bool:
        return (
            self.durum
            is EslestirmeDurumu.TAMAMLANDI
        )

    @property
    def kapandi_mi(self) -> bool:
        return self.durum in {
            EslestirmeDurumu.TAMAMLANDI,
            EslestirmeDurumu.REDDEDILDI,
            EslestirmeDurumu.SURESI_DOLDU,
        }

    def sozluk(self) -> dict[str, Any]:
        return {
            "istek_kimliği": self.istek_kimligi,
            "cihaz": self.cihaz.sozluk(),
            "durum": self.durum.value,
            "oluşturulma_zamanı": (
                self.olusturulma_zamani.isoformat()
            ),
            "sona_erme_zamanı": (
                self.sona_erme_zamani.isoformat()
            ),
            "onaylayan": self.onaylayan,
            "başarısız_deneme_sayısı": (
                self.basarisiz_deneme_sayisi
            ),
            "oturum_anahtarı_üretildi": (
                self.oturum_anahtari is not None
            ),
            "son_hata": self.son_hata,
        }


@dataclass(slots=True)
class EslestirmeDenetimKaydi:
    zaman: datetime
    olay: str
    basarili: bool
    istek_kimligi: str
    cihaz_kimligi: str
    aciklama: str | None = None


class SahaCihazEslestirmeYoneticisi:
    YETKILI_ONAYLAYANLAR = frozenset(
        {
            "Bilge Kaan",
            "Kurucu Kaan",
        }
    )

    def __init__(
        self,
        *,
        saat: Callable[[], datetime] | None = None,
        kod_gecerlilik_dakikasi: int = 10,
        azami_deneme_sayisi: int = 5,
        ana_gizli_deger: str | None = None,
    ) -> None:
        if kod_gecerlilik_dakikasi <= 0:
            raise ValueError(
                "Kod geçerlilik süresi sıfırdan büyük olmalıdır."
            )

        if azami_deneme_sayisi <= 0:
            raise ValueError(
                "Azami deneme sayısı sıfırdan büyük olmalıdır."
            )

        self._saat = saat or (
            lambda: datetime.now(UTC)
        )

        self._gecerlilik = timedelta(
            minutes=kod_gecerlilik_dakikasi
        )

        self._azami_deneme = (
            azami_deneme_sayisi
        )

        self._ana_gizli = (
            ana_gizli_deger
            or token_hex(32)
        )

        self._istekler: dict[
            str,
            EslestirmeIstegi,
        ] = {}

        self._cihaz_istekleri: dict[
            str,
            str,
        ] = {}

        self._eslesenler: dict[
            str,
            SahaCihazAdayi,
        ] = {}

        self._denetim: list[
            EslestirmeDenetimKaydi
        ] = []

    def eslestirme_istegi_olustur(
        self,
        cihaz: SahaCihazAdayi,
    ) -> tuple[EslestirmeIstegi, str]:
        if (
            cihaz.cihaz_kimligi
            in self._eslesenler
        ):
            raise SahaEslestirmeHatasi(
                "Cihaz daha önce eşleştirilmiş."
            )

        mevcut_kimlik = (
            self._cihaz_istekleri.get(
                cihaz.cihaz_kimligi
            )
        )

        if mevcut_kimlik:
            mevcut = self.istegi_getir(
                mevcut_kimlik
            )

            if not mevcut.kapandi_mi:
                raise SahaEslestirmeHatasi(
                    "Cihaz için açık bir eşleştirme isteği var."
                )

        simdi = self._saat()
        kod = f"{randbelow(1000000):06d}"

        istek = EslestirmeIstegi(
            istek_kimligi=(
                "SYK-SAHA-ESLESTIRME-"
                + uuid4().hex.upper()
            ),
            cihaz=cihaz,
            olusturulma_zamani=simdi,
            sona_erme_zamani=(
                simdi + self._gecerlilik
            ),
            kod_ozeti=self._kod_ozeti(
                kod
            ),
            azami_deneme_sayisi=(
                self._azami_deneme
            ),
        )

        self._istekler[
            istek.istek_kimligi
        ] = istek

        self._cihaz_istekleri[
            cihaz.cihaz_kimligi
        ] = istek.istek_kimligi

        self._kaydet(
            "eşleştirme_isteği_oluşturuldu",
            True,
            istek,
        )

        return istek, kod

    def istegi_getir(
        self,
        istek_kimligi: str,
    ) -> EslestirmeIstegi:
        try:
            istek = self._istekler[
                istek_kimligi
            ]
        except KeyError as hata:
            raise SahaEslestirmeHatasi(
                "Eşleştirme isteği bulunamadı."
            ) from hata

        self._sureyi_kontrol_et(
            istek
        )

        return istek

    def istegi_onayla(
        self,
        istek_kimligi: str,
        *,
        onaylayan: str,
    ) -> EslestirmeIstegi:
        istek = self.istegi_getir(
            istek_kimligi
        )

        if istek.kapandi_mi:
            raise SahaEslestirmeHatasi(
                "Kapalı eşleştirme isteği onaylanamaz."
            )

        if (
            onaylayan
            not in self.YETKILI_ONAYLAYANLAR
        ):
            raise SahaEslestirmeHatasi(
                "Eşleştirme için Bilge Kaan veya "
                "Kurucu Kaan onayı zorunludur."
            )

        istek.durum = (
            EslestirmeDurumu.ONAYLANDI
        )

        istek.onaylayan = onaylayan
        istek.onay_zamani = self._saat()
        istek.son_hata = None

        self._kaydet(
            "eşleştirme_onaylandı",
            True,
            istek,
            onaylayan,
        )

        return istek

    def eslestirmeyi_tamamla(
        self,
        istek_kimligi: str,
        *,
        kod: str,
        cihaz_parmak_izi: str,
    ) -> EslestirmeIstegi:
        istek = self.istegi_getir(
            istek_kimligi
        )

        if (
            istek.durum
            is not EslestirmeDurumu.ONAYLANDI
        ):
            raise SahaEslestirmeHatasi(
                "Eşleştirme önce yetkili kişi "
                "tarafından onaylanmalıdır."
            )

        if not hmac.compare_digest(
            istek.cihaz.cihaz_parmak_izi,
            cihaz_parmak_izi,
        ):
            self._basarisiz(
                istek,
                "Cihaz parmak izi doğrulanamadı.",
            )

        if not hmac.compare_digest(
            istek.kod_ozeti,
            self._kod_ozeti(kod),
        ):
            self._basarisiz(
                istek,
                "Eşleştirme kodu doğrulanamadı.",
            )

        istek.durum = (
            EslestirmeDurumu.TAMAMLANDI
        )

        istek.tamamlanma_zamani = (
            self._saat()
        )

        istek.oturum_anahtari = (
            self._oturum_anahtari(
                istek
            )
        )

        istek.son_hata = None

        self._eslesenler[
            istek.cihaz.cihaz_kimligi
        ] = istek.cihaz

        self._kaydet(
            "eşleştirme_tamamlandı",
            True,
            istek,
        )

        return istek

    def istegi_reddet(
        self,
        istek_kimligi: str,
        *,
        gerekce: str,
        reddeden: str,
    ) -> EslestirmeIstegi:
        istek = self.istegi_getir(
            istek_kimligi
        )

        if (
            reddeden
            not in self.YETKILI_ONAYLAYANLAR
        ):
            raise SahaEslestirmeHatasi(
                "Eşleştirme isteğini reddetme yetkisi yok."
            )

        if not gerekce.strip():
            raise SahaEslestirmeHatasi(
                "Reddetme gerekçesi zorunludur."
            )

        if not istek.kapandi_mi:
            istek.durum = (
                EslestirmeDurumu.REDDEDILDI
            )

            istek.reddetme_gerekcesi = gerekce
            istek.son_hata = gerekce

            self._kaydet(
                "eşleştirme_reddedildi",
                True,
                istek,
                gerekce,
            )

        return istek

    def eslesen_cihazlari_listele(
        self,
    ) -> tuple[SahaCihazAdayi, ...]:
        return tuple(
            self._eslesenler[kimlik]
            for kimlik in sorted(
                self._eslesenler
            )
        )

    def denetim_kayitlari(
        self,
    ) -> tuple[EslestirmeDenetimKaydi, ...]:
        return tuple(
            self._denetim
        )

    def durum_ozeti(
        self,
    ) -> dict[str, Any]:
        istekler = tuple(
            self.istegi_getir(kimlik)
            for kimlik in sorted(
                self._istekler
            )
        )

        return {
            "toplam_istek_sayısı": len(
                istekler
            ),
            "onay_bekleyen_istek_sayısı": sum(
                istek.durum
                is EslestirmeDurumu.ONAY_BEKLIYOR
                for istek in istekler
            ),
            "onaylanan_istek_sayısı": sum(
                istek.durum
                is EslestirmeDurumu.ONAYLANDI
                for istek in istekler
            ),
            "tamamlanan_istek_sayısı": sum(
                istek.durum
                is EslestirmeDurumu.TAMAMLANDI
                for istek in istekler
            ),
            "eşleşmiş_cihaz_sayısı": len(
                self._eslesenler
            ),
            "denetim_kaydı_sayısı": len(
                self._denetim
            ),
            "istekler": [
                istek.sozluk()
                for istek in istekler
            ],
            "eşleşmiş_cihazlar": [
                cihaz.sozluk()
                for cihaz
                in self.eslesen_cihazlari_listele()
            ],
        }

    def _basarisiz(
        self,
        istek: EslestirmeIstegi,
        aciklama: str,
    ) -> None:
        istek.basarisiz_deneme_sayisi += 1
        istek.son_hata = aciklama

        if (
            istek.basarisiz_deneme_sayisi
            >= istek.azami_deneme_sayisi
        ):
            istek.durum = (
                EslestirmeDurumu.REDDEDILDI
            )

            istek.reddetme_gerekcesi = (
                "Azami doğrulama denemesi aşıldı."
            )

        self._kaydet(
            "eşleştirme_doğrulaması_başarısız",
            False,
            istek,
            aciklama,
        )

        raise SahaEslestirmeHatasi(
            aciklama
        )

    def _sureyi_kontrol_et(
        self,
        istek: EslestirmeIstegi,
    ) -> None:
        if (
            not istek.kapandi_mi
            and self._saat()
            > istek.sona_erme_zamani
        ):
            istek.durum = (
                EslestirmeDurumu.SURESI_DOLDU
            )

            istek.son_hata = (
                "Eşleştirme kodunun süresi doldu."
            )

            self._kaydet(
                "eşleştirme_süresi_doldu",
                False,
                istek,
                istek.son_hata,
            )

    def _kod_ozeti(
        self,
        kod: str,
    ) -> str:
        return hmac.new(
            self._ana_gizli.encode(
                "utf-8"
            ),
            kod.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    def _oturum_anahtari(
        self,
        istek: EslestirmeIstegi,
    ) -> str:
        ham = (
            f"{istek.istek_kimligi}:"
            f"{istek.cihaz.cihaz_kimligi}:"
            f"{istek.cihaz.cihaz_parmak_izi}:"
            f"{self._saat().isoformat()}:"
            f"{token_hex(32)}"
        )

        return hmac.new(
            self._ana_gizli.encode(
                "utf-8"
            ),
            ham.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    def _kaydet(
        self,
        olay: str,
        basarili: bool,
        istek: EslestirmeIstegi,
        aciklama: str | None = None,
    ) -> None:
        self._denetim.append(
            EslestirmeDenetimKaydi(
                zaman=self._saat(),
                olay=olay,
                basarili=basarili,
                istek_kimligi=(
                    istek.istek_kimligi
                ),
                cihaz_kimligi=(
                    istek.cihaz.cihaz_kimligi
                ),
                aciklama=aciklama,
            )
        )
