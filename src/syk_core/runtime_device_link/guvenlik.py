"""SyKaşif cihaz bağlantısı güvenlik katmanı."""

from __future__ import annotations

import hashlib
import hmac
from collections import deque
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum
from secrets import token_hex
from threading import RLock
from typing import Any, Callable

from .protokol import (
    CihazMesaji,
    MesajDurumu,
)


class GuvenlikHatasi(RuntimeError):
    """Cihaz bağlantısı güvenlik hatası."""


class CihazYetkisi(str, Enum):
    KURUCU_KAAN = "Kurucu Kaan"
    BILGE_KAAN = "Bilge Kaan"
    ISLETMEN = "işletmen"
    GOZLEMCI = "gözlemci"


class IslemYetkisi(str, Enum):
    DURUM_OKU = "durum_oku"
    VERI_GONDER = "veri_gönder"
    BILDIRIM_GONDER = "bildirim_gönder"
    UYGULAMA_AC = "uygulama_aç"
    UYGULAMA_KAPAT = "uygulama_kapat"
    SISTEMI_BASLAT = "sistemi_başlat"
    SISTEMI_DURDUR = "sistemi_durdur"
    MASAUSTUNU_KAPAT = "masaüstünü_kapat"
    YENIDEN_BASLAT = "yeniden_başlat"
    CIHAZ_YONET = "cihaz_yönet"


@dataclass(slots=True, frozen=True)
class CihazKimligi:
    cihaz_kimligi: str
    cihaz_parmak_izi: str
    yetki: CihazYetkisi
    gizli_anahtar_ozeti: str
    etkin: bool = True
    izinler: frozenset[IslemYetkisi] = field(
        default_factory=frozenset
    )

    def __post_init__(self) -> None:
        if not self.cihaz_kimligi.strip():
            raise ValueError(
                "Cihaz kimliği boş olamaz."
            )

        if not self.cihaz_parmak_izi.strip():
            raise ValueError(
                "Cihaz parmak izi boş olamaz."
            )

        if not self.gizli_anahtar_ozeti.strip():
            raise ValueError(
                "Gizli anahtar özeti boş olamaz."
            )


@dataclass(slots=True)
class GuvenlikDenetimKaydi:
    zaman: datetime
    olay: str
    basarili: bool
    cihaz_kimligi: str | None = None
    mesaj_kimligi: str | None = None
    aciklama: str | None = None
    veri: dict[str, Any] = field(
        default_factory=dict
    )

    def sozluk(self) -> dict[str, Any]:
        return {
            "zaman": self.zaman.isoformat(),
            "olay": self.olay,
            "başarılı": self.basarili,
            "cihaz_kimliği": self.cihaz_kimligi,
            "mesaj_kimliği": self.mesaj_kimligi,
            "açıklama": self.aciklama,
            "veri": dict(self.veri),
        }


class CihazGuvenlikYoneticisi:
    """Cihaz kimliği, yetki, imza ve tekrar saldırısı denetimi."""

    def __init__(
        self,
        *,
        saat: Callable[[], datetime] | None = None,
        kullanilmis_deger_siniri: int = 10000,
        denetim_kaydi_siniri: int = 5000,
    ) -> None:
        if kullanilmis_deger_siniri <= 0:
            raise ValueError(
                "Kullanılmış değer sınırı sıfırdan büyük olmalıdır."
            )

        if denetim_kaydi_siniri <= 0:
            raise ValueError(
                "Denetim kaydı sınırı sıfırdan büyük olmalıdır."
            )

        self._saat = saat or (
            lambda: datetime.now(UTC)
        )

        self._cihazlar: dict[
            str,
            CihazKimligi,
        ] = {}

        self._anahtarlar: dict[
            str,
            str,
        ] = {}

        self._kullanilmis_degerler: set[
            str
        ] = set()

        self._kullanilmis_deger_sirasi: deque[
            str
        ] = deque()

        self._kullanilmis_deger_siniri = (
            kullanilmis_deger_siniri
        )

        self._denetim_kayitlari: deque[
            GuvenlikDenetimKaydi
        ] = deque(
            maxlen=denetim_kaydi_siniri
        )

        self._kilit = RLock()

    @staticmethod
    def anahtar_ozeti(
        gizli_anahtar: str,
    ) -> str:
        return hashlib.sha256(
            gizli_anahtar.encode("utf-8")
        ).hexdigest()

    def cihaz_kaydet(
        self,
        *,
        cihaz_kimligi: str,
        cihaz_parmak_izi: str,
        yetki: CihazYetkisi,
        gizli_anahtar: str | None = None,
        izinler: set[IslemYetkisi] | None = None,
    ) -> tuple[CihazKimligi, str]:
        if cihaz_kimligi in self._cihazlar:
            raise GuvenlikHatasi(
                "Cihaz güvenlik kaydında zaten mevcut."
            )

        anahtar = (
            gizli_anahtar
            or token_hex(32)
        )

        cihaz = CihazKimligi(
            cihaz_kimligi=cihaz_kimligi,
            cihaz_parmak_izi=(
                cihaz_parmak_izi
            ),
            yetki=yetki,
            gizli_anahtar_ozeti=(
                self.anahtar_ozeti(
                    anahtar
                )
            ),
            izinler=frozenset(
                izinler
                or self._varsayilan_izinler(
                    yetki
                )
            ),
        )

        with self._kilit:
            self._cihazlar[
                cihaz_kimligi
            ] = cihaz

            self._anahtarlar[
                cihaz_kimligi
            ] = anahtar

        self._kayit_ekle(
            olay="cihaz_kaydedildi",
            basarili=True,
            cihaz_kimligi=cihaz_kimligi,
        )

        return cihaz, anahtar

    def cihaz_getir(
        self,
        cihaz_kimligi: str,
    ) -> CihazKimligi:
        try:
            return self._cihazlar[
                cihaz_kimligi
            ]
        except KeyError as hata:
            raise GuvenlikHatasi(
                f"Cihaz güvenlik kaydı bulunamadı: {cihaz_kimligi}"
            ) from hata

    def anahtar_getir(
        self,
        cihaz_kimligi: str,
    ) -> str:
        try:
            return self._anahtarlar[
                cihaz_kimligi
            ]
        except KeyError as hata:
            raise GuvenlikHatasi(
                f"Cihaz anahtarı bulunamadı: {cihaz_kimligi}"
            ) from hata

    def cihaz_dogrula(
        self,
        *,
        cihaz_kimligi: str,
        cihaz_parmak_izi: str,
        gizli_anahtar: str,
    ) -> CihazKimligi:
        cihaz = self.cihaz_getir(
            cihaz_kimligi
        )

        if not cihaz.etkin:
            self._kayit_ekle(
                olay="cihaz_dogrulama",
                basarili=False,
                cihaz_kimligi=cihaz_kimligi,
                aciklama="Cihaz etkin değil.",
            )

            raise GuvenlikHatasi(
                "Cihaz etkin değil."
            )

        if not hmac.compare_digest(
            cihaz.cihaz_parmak_izi,
            cihaz_parmak_izi,
        ):
            self._kayit_ekle(
                olay="cihaz_dogrulama",
                basarili=False,
                cihaz_kimligi=cihaz_kimligi,
                aciklama=(
                    "Cihaz parmak izi uyuşmadı."
                ),
            )

            raise GuvenlikHatasi(
                "Cihaz parmak izi doğrulanamadı."
            )

        ozet = self.anahtar_ozeti(
            gizli_anahtar
        )

        if not hmac.compare_digest(
            cihaz.gizli_anahtar_ozeti,
            ozet,
        ):
            self._kayit_ekle(
                olay="cihaz_dogrulama",
                basarili=False,
                cihaz_kimligi=cihaz_kimligi,
                aciklama=(
                    "Cihaz gizli anahtarı uyuşmadı."
                ),
            )

            raise GuvenlikHatasi(
                "Cihaz gizli anahtarı doğrulanamadı."
            )

        self._kayit_ekle(
            olay="cihaz_dogrulama",
            basarili=True,
            cihaz_kimligi=cihaz_kimligi,
        )

        return cihaz

    def yetki_dogrula(
        self,
        *,
        cihaz_kimligi: str,
        islem_yetkisi: IslemYetkisi,
    ) -> None:
        cihaz = self.cihaz_getir(
            cihaz_kimligi
        )

        if not cihaz.etkin:
            raise GuvenlikHatasi(
                "Etkin olmayan cihaz işlem yapamaz."
            )

        if (
            islem_yetkisi
            not in cihaz.izinler
        ):
            self._kayit_ekle(
                olay="yetki_reddedildi",
                basarili=False,
                cihaz_kimligi=cihaz_kimligi,
                aciklama=(
                    f"İzin bulunamadı: {islem_yetkisi.value}"
                ),
            )

            raise GuvenlikHatasi(
                "Cihazın bu işlem için yetkisi yok."
            )

        self._kayit_ekle(
            olay="yetki_dogrulandi",
            basarili=True,
            cihaz_kimligi=cihaz_kimligi,
            veri={
                "işlem_yetkisi": (
                    islem_yetkisi.value
                )
            },
        )

    def mesaji_dogrula(
        self,
        mesaj: CihazMesaji,
    ) -> CihazMesaji:
        cihaz = self.cihaz_getir(
            mesaj.kaynak_cihaz_kimligi
        )

        if not cihaz.etkin:
            return self._mesaji_reddet(
                mesaj,
                "Kaynak cihaz etkin değil.",
            )

        anahtar = self.anahtar_getir(
            mesaj.kaynak_cihaz_kimligi
        )

        if not mesaj.imzayi_dogrula(
            anahtar
        ):
            return self._mesaji_reddet(
                mesaj,
                "Mesaj imzası doğrulanamadı.",
            )

        simdi = self._saat()

        gecerlilik_sonucu = (
            mesaj.olusturulma_zamani
            + timedelta(
                seconds=(
                    mesaj
                    .gecerlilik_suresi_saniye
                )
            )
        )

        if simdi > gecerlilik_sonucu:
            return self._mesaji_reddet(
                mesaj,
                "Mesaj geçerlilik süresini aştı.",
            )

        if (
            mesaj.olusturulma_zamani
            > simdi + timedelta(seconds=10)
        ):
            return self._mesaji_reddet(
                mesaj,
                "Mesaj zamanı gelecekte.",
            )

        if not mesaj.benzersiz_deger:
            return self._mesaji_reddet(
                mesaj,
                "Mesaj benzersiz değeri bulunmuyor.",
            )

        with self._kilit:
            if (
                mesaj.benzersiz_deger
                in self._kullanilmis_degerler
            ):
                return self._mesaji_reddet(
                    mesaj,
                    "Mesaj daha önce işlendi.",
                )

            self._kullanilmis_degerler.add(
                mesaj.benzersiz_deger
            )

            self._kullanilmis_deger_sirasi.append(
                mesaj.benzersiz_deger
            )

            while (
                len(
                    self._kullanilmis_deger_sirasi
                )
                > self._kullanilmis_deger_siniri
            ):
                eski = (
                    self._kullanilmis_deger_sirasi
                    .popleft()
                )

                self._kullanilmis_degerler.discard(
                    eski
                )

        mesaj.durum = MesajDurumu.DOGRULANDI
        mesaj.hata = None

        self._kayit_ekle(
            olay="mesaj_dogrulandi",
            basarili=True,
            cihaz_kimligi=(
                mesaj.kaynak_cihaz_kimligi
            ),
            mesaj_kimligi=(
                mesaj.mesaj_kimligi
            ),
        )

        return mesaj

    def denetim_kayitlari(
        self,
    ) -> tuple[GuvenlikDenetimKaydi, ...]:
        return tuple(
            self._denetim_kayitlari
        )

    def durum_ozeti(
        self,
    ) -> dict[str, Any]:
        return {
            "kayıtlı_cihaz_sayısı": len(
                self._cihazlar
            ),
            "etkin_cihaz_sayısı": sum(
                1
                for cihaz in self._cihazlar.values()
                if cihaz.etkin
            ),
            "kullanılmış_benzersiz_değer_sayısı": (
                len(self._kullanilmis_degerler)
            ),
            "denetim_kaydı_sayısı": len(
                self._denetim_kayitlari
            ),
            "cihazlar": [
                {
                    "cihaz_kimliği": (
                        cihaz.cihaz_kimligi
                    ),
                    "yetki": cihaz.yetki.value,
                    "etkin": cihaz.etkin,
                    "izinler": sorted(
                        izin.value
                        for izin in cihaz.izinler
                    ),
                }
                for cihaz in self._cihazlar.values()
            ],
        }

    def _mesaji_reddet(
        self,
        mesaj: CihazMesaji,
        aciklama: str,
    ) -> CihazMesaji:
        mesaj.durum = MesajDurumu.REDDEDILDI
        mesaj.hata = aciklama

        self._kayit_ekle(
            olay="mesaj_reddedildi",
            basarili=False,
            cihaz_kimligi=(
                mesaj.kaynak_cihaz_kimligi
            ),
            mesaj_kimligi=(
                mesaj.mesaj_kimligi
            ),
            aciklama=aciklama,
        )

        return mesaj

    def _kayit_ekle(
        self,
        *,
        olay: str,
        basarili: bool,
        cihaz_kimligi: str | None = None,
        mesaj_kimligi: str | None = None,
        aciklama: str | None = None,
        veri: dict[str, Any] | None = None,
    ) -> None:
        self._denetim_kayitlari.append(
            GuvenlikDenetimKaydi(
                zaman=self._saat(),
                olay=olay,
                basarili=basarili,
                cihaz_kimligi=cihaz_kimligi,
                mesaj_kimligi=mesaj_kimligi,
                aciklama=aciklama,
                veri=dict(veri or {}),
            )
        )

    @staticmethod
    def _varsayilan_izinler(
        yetki: CihazYetkisi,
    ) -> set[IslemYetkisi]:
        temel = {
            IslemYetkisi.DURUM_OKU,
            IslemYetkisi.VERI_GONDER,
            IslemYetkisi.BILDIRIM_GONDER,
        }

        if yetki is CihazYetkisi.GOZLEMCI:
            return {
                IslemYetkisi.DURUM_OKU,
            }

        if yetki is CihazYetkisi.ISLETMEN:
            return temel

        if yetki is CihazYetkisi.BILGE_KAAN:
            return temel | {
                IslemYetkisi.UYGULAMA_AC,
                IslemYetkisi.UYGULAMA_KAPAT,
                IslemYetkisi.SISTEMI_BASLAT,
                IslemYetkisi.SISTEMI_DURDUR,
            }

        return set(IslemYetkisi)
