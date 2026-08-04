"""SyKaşif gerçek cihaz envanteri ve donanım doğrulama kayıt modeli."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any, Callable


class DonanimDogrulamaHatasi(RuntimeError):
    """Gerçek cihaz ve donanım doğrulama hatası."""


class DonanimTuru(str, Enum):
    ANA_MASAUSTU = "ana_masaüstü"
    TABLET = "tablet"
    TELEFON = "telefon"
    DIZUSTU = "dizüstü"
    SENSOR = "sensör"
    PROBE = "probe"
    KAMERA = "kamera"
    MIKROFON = "mikrofon"
    GPS = "gps"
    DIGER = "diğer"


class BaglantiTuru(str, Enum):
    USB = "usb"
    ETHERNET = "ethernet"
    WIFI = "wi-fi"
    BLUETOOTH = "bluetooth"
    SERI = "seri"
    YEREL = "yerel"
    DIGER = "diğer"


class DonanimDurumu(str, Enum):
    KAYITLI = "kayıtlı"
    BAGLI = "bağlı"
    DOGRULANDI = "doğrulandı"
    CEVRIMDISI = "çevrimdışı"
    HATALI = "hatalı"
    BEKLIYOR = "bekliyor"


class DogrulamaSonucu(str, Enum):
    BEKLIYOR = "bekliyor"
    BASARILI = "başarılı"
    BASARISIZ = "başarısız"
    KISMI = "kısmi"


@dataclass(slots=True, frozen=True)
class DonanimKimligi:
    cihaz_kimligi: str
    cihaz_adi: str
    donanim_turu: DonanimTuru
    uretici: str | None = None
    model: str | None = None
    seri_numarasi: str | None = None
    parmak_izi: str | None = None

    def __post_init__(self) -> None:
        if not self.cihaz_kimligi.strip():
            raise ValueError(
                "Cihaz kimliği boş olamaz."
            )

        if not self.cihaz_adi.strip():
            raise ValueError(
                "Cihaz adı boş olamaz."
            )

    def sozluk(self) -> dict[str, Any]:
        return {
            "cihaz_kimliği": self.cihaz_kimligi,
            "cihaz_adı": self.cihaz_adi,
            "donanım_türü": self.donanim_turu.value,
            "üretici": self.uretici,
            "model": self.model,
            "seri_numarası": self.seri_numarasi,
            "parmak_izi": self.parmak_izi,
        }


@dataclass(slots=True)
class BaglantiKaydi:
    baglanti_turu: BaglantiTuru
    baglanti_adresi: str
    baglandi_mi: bool
    kayit_zamani: datetime
    gecikme_milisaniye: float | None = None
    hata: str | None = None
    ayrintilar: dict[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        if not self.baglanti_adresi.strip():
            raise ValueError(
                "Bağlantı adresi boş olamaz."
            )

        if self.kayit_zamani.tzinfo is None:
            raise ValueError(
                "Bağlantı zamanı saat dilimi içermelidir."
            )

        if (
            self.gecikme_milisaniye is not None
            and self.gecikme_milisaniye < 0
        ):
            raise ValueError(
                "Bağlantı gecikmesi negatif olamaz."
            )

    def sozluk(self) -> dict[str, Any]:
        return {
            "bağlantı_türü": self.baglanti_turu.value,
            "bağlantı_adresi": self.baglanti_adresi,
            "bağlandı": self.baglandi_mi,
            "kayıt_zamanı": self.kayit_zamani.isoformat(),
            "gecikme_milisaniye": self.gecikme_milisaniye,
            "hata": self.hata,
            "ayrıntılar": dict(self.ayrintilar),
        }


@dataclass(slots=True)
class DonanimTestKaydi:
    test_adi: str
    sonuc: DogrulamaSonucu
    baslama_zamani: datetime
    bitis_zamani: datetime | None = None
    olcumler: dict[str, Any] = field(
        default_factory=dict
    )
    aciklama: str | None = None

    def __post_init__(self) -> None:
        if not self.test_adi.strip():
            raise ValueError(
                "Test adı boş olamaz."
            )

        if self.baslama_zamani.tzinfo is None:
            raise ValueError(
                "Test başlangıç zamanı saat dilimi içermelidir."
            )

        if (
            self.bitis_zamani is not None
            and self.bitis_zamani.tzinfo is None
        ):
            raise ValueError(
                "Test bitiş zamanı saat dilimi içermelidir."
            )

        if (
            self.bitis_zamani is not None
            and self.bitis_zamani
            < self.baslama_zamani
        ):
            raise ValueError(
                "Test bitiş zamanı başlangıçtan önce olamaz."
            )

    def sozluk(self) -> dict[str, Any]:
        return {
            "test_adı": self.test_adi,
            "sonuç": self.sonuc.value,
            "başlama_zamanı": (
                self.baslama_zamani.isoformat()
            ),
            "bitiş_zamanı": (
                self.bitis_zamani.isoformat()
                if self.bitis_zamani
                else None
            ),
            "ölçümler": dict(self.olcumler),
            "açıklama": self.aciklama,
        }


@dataclass(slots=True)
class DonanimKaydi:
    kimlik: DonanimKimligi
    olusturulma_zamani: datetime
    guncellenme_zamani: datetime
    durum: DonanimDurumu = DonanimDurumu.KAYITLI
    baglantilar: list[BaglantiKaydi] = field(
        default_factory=list
    )
    testler: list[DonanimTestKaydi] = field(
        default_factory=list
    )
    yetenekler: set[str] = field(
        default_factory=set
    )
    notlar: list[str] = field(
        default_factory=list
    )
    gercek_donanim_mi: bool = True

    def __post_init__(self) -> None:
        if self.olusturulma_zamani.tzinfo is None:
            raise ValueError(
                "Oluşturulma zamanı saat dilimi içermelidir."
            )

        if self.guncellenme_zamani.tzinfo is None:
            raise ValueError(
                "Güncellenme zamanı saat dilimi içermelidir."
            )

    @property
    def bagli_mi(self) -> bool:
        return self.durum in {
            DonanimDurumu.BAGLI,
            DonanimDurumu.DOGRULANDI,
        }

    @property
    def dogrulandi_mi(self) -> bool:
        return (
            self.durum
            is DonanimDurumu.DOGRULANDI
        )

    @property
    def son_baglanti(self) -> BaglantiKaydi | None:
        if not self.baglantilar:
            return None

        return self.baglantilar[-1]

    @property
    def son_test(self) -> DonanimTestKaydi | None:
        if not self.testler:
            return None

        return self.testler[-1]

    def sozluk(self) -> dict[str, Any]:
        return {
            "kimlik": self.kimlik.sozluk(),
            "durum": self.durum.value,
            "oluşturulma_zamanı": (
                self.olusturulma_zamani.isoformat()
            ),
            "güncellenme_zamanı": (
                self.guncellenme_zamani.isoformat()
            ),
            "bağlı": self.bagli_mi,
            "doğrulandı": self.dogrulandi_mi,
            "gerçek_donanım": self.gercek_donanim_mi,
            "yetenekler": sorted(self.yetenekler),
            "notlar": list(self.notlar),
            "bağlantılar": [
                kayit.sozluk()
                for kayit in self.baglantilar
            ],
            "testler": [
                kayit.sozluk()
                for kayit in self.testler
            ],
        }


@dataclass(slots=True, frozen=True)
class DonanimDenetimKaydi:
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


class DonanimEnvanteri:
    """Gerçek cihaz kayıtlarını ve doğrulama sonuçlarını yönetir."""

    def __init__(
        self,
        *,
        saat: Callable[[], datetime] | None = None,
    ) -> None:
        self._saat = saat or (
            lambda: datetime.now(UTC)
        )

        self._kayitlar: dict[
            str,
            DonanimKaydi,
        ] = {}

        self._denetim: list[
            DonanimDenetimKaydi
        ] = []

    def cihaz_kaydet(
        self,
        kimlik: DonanimKimligi,
        *,
        yetenekler: set[str] | None = None,
        gercek_donanim_mi: bool = True,
    ) -> DonanimKaydi:
        if kimlik.cihaz_kimligi in self._kayitlar:
            raise DonanimDogrulamaHatasi(
                "Cihaz daha önce envantere kaydedilmiş."
            )

        simdi = self._saat()

        kayit = DonanimKaydi(
            kimlik=kimlik,
            olusturulma_zamani=simdi,
            guncellenme_zamani=simdi,
            yetenekler=set(
                yetenekler or set()
            ),
            gercek_donanim_mi=(
                gercek_donanim_mi
            ),
        )

        self._kayitlar[
            kimlik.cihaz_kimligi
        ] = kayit

        self._denetim_kaydi_ekle(
            olay="cihaz_envantere_kaydedildi",
            basarili=True,
            cihaz_kimligi=kimlik.cihaz_kimligi,
        )

        return kayit

    def cihaz_getir(
        self,
        cihaz_kimligi: str,
    ) -> DonanimKaydi:
        try:
            return self._kayitlar[
                cihaz_kimligi
            ]
        except KeyError as hata:
            raise DonanimDogrulamaHatasi(
                f"Donanım kaydı bulunamadı: {cihaz_kimligi}"
            ) from hata

    def baglanti_kaydi_ekle(
        self,
        cihaz_kimligi: str,
        *,
        baglanti_turu: BaglantiTuru,
        baglanti_adresi: str,
        baglandi_mi: bool,
        gecikme_milisaniye: float | None = None,
        hata: str | None = None,
        ayrintilar: dict[str, Any] | None = None,
    ) -> BaglantiKaydi:
        cihaz = self.cihaz_getir(
            cihaz_kimligi
        )

        kayit = BaglantiKaydi(
            baglanti_turu=baglanti_turu,
            baglanti_adresi=baglanti_adresi,
            baglandi_mi=baglandi_mi,
            kayit_zamani=self._saat(),
            gecikme_milisaniye=(
                gecikme_milisaniye
            ),
            hata=hata,
            ayrintilar=dict(
                ayrintilar or {}
            ),
        )

        cihaz.baglantilar.append(
            kayit
        )
        cihaz.guncellenme_zamani = (
            kayit.kayit_zamani
        )

        if baglandi_mi:
            cihaz.durum = DonanimDurumu.BAGLI
        else:
            cihaz.durum = DonanimDurumu.HATALI

        self._denetim_kaydi_ekle(
            olay=(
                "donanım_bağlantısı_başarılı"
                if baglandi_mi
                else "donanım_bağlantısı_başarısız"
            ),
            basarili=baglandi_mi,
            cihaz_kimligi=cihaz_kimligi,
            aciklama=hata,
        )

        return kayit

    def test_baslat(
        self,
        cihaz_kimligi: str,
        *,
        test_adi: str,
    ) -> DonanimTestKaydi:
        cihaz = self.cihaz_getir(
            cihaz_kimligi
        )

        kayit = DonanimTestKaydi(
            test_adi=test_adi,
            sonuc=DogrulamaSonucu.BEKLIYOR,
            baslama_zamani=self._saat(),
        )

        cihaz.testler.append(
            kayit
        )
        cihaz.durum = DonanimDurumu.BEKLIYOR
        cihaz.guncellenme_zamani = (
            kayit.baslama_zamani
        )

        self._denetim_kaydi_ekle(
            olay="donanım_testi_başlatıldı",
            basarili=True,
            cihaz_kimligi=cihaz_kimligi,
            aciklama=test_adi,
        )

        return kayit

    def test_tamamla(
        self,
        cihaz_kimligi: str,
        *,
        sonuc: DogrulamaSonucu,
        olcumler: dict[str, Any] | None = None,
        aciklama: str | None = None,
    ) -> DonanimTestKaydi:
        cihaz = self.cihaz_getir(
            cihaz_kimligi
        )

        test = cihaz.son_test

        if test is None:
            raise DonanimDogrulamaHatasi(
                "Tamamlanacak açık donanım testi bulunamadı."
            )

        if test.sonuc is not DogrulamaSonucu.BEKLIYOR:
            raise DonanimDogrulamaHatasi(
                "Donanım testi daha önce tamamlanmış."
            )

        if sonuc is DogrulamaSonucu.BEKLIYOR:
            raise DonanimDogrulamaHatasi(
                "Tamamlanan test bekliyor sonucunda bırakılamaz."
            )

        simdi = self._saat()

        test.sonuc = sonuc
        test.bitis_zamani = simdi
        test.olcumler = dict(
            olcumler or {}
        )
        test.aciklama = aciklama

        cihaz.guncellenme_zamani = simdi

        if sonuc is DogrulamaSonucu.BASARILI:
            cihaz.durum = (
                DonanimDurumu.DOGRULANDI
            )
        elif sonuc is DogrulamaSonucu.KISMI:
            cihaz.durum = (
                DonanimDurumu.BAGLI
            )
        else:
            cihaz.durum = (
                DonanimDurumu.HATALI
            )

        self._denetim_kaydi_ekle(
            olay="donanım_testi_tamamlandı",
            basarili=(
                sonuc
                is DogrulamaSonucu.BASARILI
            ),
            cihaz_kimligi=cihaz_kimligi,
            aciklama=aciklama,
        )

        return test

    def not_ekle(
        self,
        cihaz_kimligi: str,
        not_metni: str,
    ) -> None:
        if not not_metni.strip():
            raise DonanimDogrulamaHatasi(
                "Donanım notu boş olamaz."
            )

        cihaz = self.cihaz_getir(
            cihaz_kimligi
        )

        cihaz.notlar.append(
            not_metni.strip()
        )
        cihaz.guncellenme_zamani = (
            self._saat()
        )

    def cihazlari_listele(
        self,
    ) -> tuple[DonanimKaydi, ...]:
        return tuple(
            self._kayitlar[kimlik]
            for kimlik in sorted(
                self._kayitlar
            )
        )

    def dogrulanan_cihazlari_listele(
        self,
    ) -> tuple[DonanimKaydi, ...]:
        return tuple(
            cihaz
            for cihaz in self.cihazlari_listele()
            if cihaz.dogrulandi_mi
        )

    def denetim_kayitlari(
        self,
    ) -> tuple[DonanimDenetimKaydi, ...]:
        return tuple(
            self._denetim
        )

    def durum_ozeti(
        self,
    ) -> dict[str, Any]:
        cihazlar = self.cihazlari_listele()

        return {
            "toplam_cihaz_sayısı": len(
                cihazlar
            ),
            "gerçek_donanım_sayısı": sum(
                cihaz.gercek_donanim_mi
                for cihaz in cihazlar
            ),
            "bağlı_cihaz_sayısı": sum(
                cihaz.bagli_mi
                for cihaz in cihazlar
            ),
            "doğrulanan_cihaz_sayısı": sum(
                cihaz.dogrulandi_mi
                for cihaz in cihazlar
            ),
            "hatalı_cihaz_sayısı": sum(
                cihaz.durum
                is DonanimDurumu.HATALI
                for cihaz in cihazlar
            ),
            "denetim_kaydı_sayısı": len(
                self._denetim
            ),
            "gerçek_donanım_doğrulaması": (
                "başladı"
                if cihazlar
                else "bekliyor"
            ),
            "cihazlar": [
                cihaz.sozluk()
                for cihaz in cihazlar
            ],
        }

    def _denetim_kaydi_ekle(
        self,
        *,
        olay: str,
        basarili: bool,
        cihaz_kimligi: str,
        aciklama: str | None = None,
    ) -> None:
        self._denetim.append(
            DonanimDenetimKaydi(
                zaman=self._saat(),
                olay=olay,
                basarili=basarili,
                cihaz_kimligi=cihaz_kimligi,
                aciklama=aciklama,
            )
        )
