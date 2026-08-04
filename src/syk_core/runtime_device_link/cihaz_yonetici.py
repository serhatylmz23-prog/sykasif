"""SyKaşif yetkili cihaz yönetimi ve komut yönlendirme katmanı."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from threading import RLock
from typing import Any, Callable
from uuid import uuid4

from .baglanti import CihazBaglantiYoneticisi
from .cihaz_oturumu import CihazOturumu
from .guvenlik import (
    CihazGuvenlikYoneticisi,
    CihazYetkisi,
    GuvenlikHatasi,
    IslemYetkisi,
)
from .protokol import (
    CihazMesaji,
    MesajDurumu,
    MesajTuru,
)


class CihazYonetimHatasi(RuntimeError):
    """Yetkili cihaz yönetim hatası."""


class KomutDurumu(str, Enum):
    OLUSTURULDU = "oluşturuldu"
    YETKI_BEKLIYOR = "yetki_bekliyor"
    KUYRUKTA = "kuyrukta"
    CALISIYOR = "çalışıyor"
    TAMAMLANDI = "tamamlandı"
    REDDEDILDI = "reddedildi"
    HATA = "hata"


@dataclass(slots=True, frozen=True)
class YetkiliCihazKaydi:
    cihaz_kimligi: str
    cihaz_parmak_izi: str
    yetki: CihazYetkisi
    gizli_anahtar: str
    aciklama: str | None = None
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

        if not self.gizli_anahtar.strip():
            raise ValueError(
                "Gizli anahtar boş olamaz."
            )


@dataclass(slots=True)
class CihazKomutu:
    komut_kimligi: str
    kaynak_cihaz_kimligi: str
    hedef_cihaz_kimligi: str
    islem_yetkisi: IslemYetkisi
    olusturulma_zamani: datetime
    durum: KomutDurumu = KomutDurumu.OLUSTURULDU
    icerik: dict[str, Any] = field(default_factory=dict)
    gerekce: str | None = None
    insan_onayi: str | None = None
    sonuc: dict[str, Any] = field(default_factory=dict)
    hata: str | None = None
    tamamlanma_zamani: datetime | None = None
    mesaj_kimligi: str | None = None

    def __post_init__(self) -> None:
        if not self.komut_kimligi.strip():
            raise ValueError(
                "Komut kimliği boş olamaz."
            )

        if self.olusturulma_zamani.tzinfo is None:
            raise ValueError(
                "Komut zamanı saat dilimi içermelidir."
            )

    def sozluk(self) -> dict[str, Any]:
        return {
            "komut_kimliği": self.komut_kimligi,
            "kaynak_cihaz_kimliği": (
                self.kaynak_cihaz_kimligi
            ),
            "hedef_cihaz_kimliği": (
                self.hedef_cihaz_kimligi
            ),
            "işlem_yetkisi": (
                self.islem_yetkisi.value
            ),
            "durum": self.durum.value,
            "içerik": dict(self.icerik),
            "gerekçe": self.gerekce,
            "insan_onayı": self.insan_onayi,
            "sonuç": dict(self.sonuc),
            "hata": self.hata,
            "mesaj_kimliği": self.mesaj_kimligi,
            "oluşturulma_zamanı": (
                self.olusturulma_zamani.isoformat()
            ),
            "tamamlanma_zamanı": (
                self.tamamlanma_zamani.isoformat()
                if self.tamamlanma_zamani
                else None
            ),
        }


KomutIsleyici = Callable[
    [CihazKomutu],
    dict[str, Any] | None,
]


class YetkiliCihazYoneticisi:
    """Cihaz kaydı, oturum ve güvenli komut yönlendirmesini birleştirir."""

    KRITIK_ISLEMLER = frozenset(
        {
            IslemYetkisi.MASAUSTUNU_KAPAT,
            IslemYetkisi.YENIDEN_BASLAT,
            IslemYetkisi.SISTEMI_DURDUR,
            IslemYetkisi.CIHAZ_YONET,
        }
    )

    def __init__(
        self,
        *,
        guvenlik: CihazGuvenlikYoneticisi | None = None,
        baglanti: CihazBaglantiYoneticisi | None = None,
        saat: Callable[[], datetime] | None = None,
        komut_gecmisi_siniri: int = 5000,
    ) -> None:
        if komut_gecmisi_siniri <= 0:
            raise ValueError(
                "Komut geçmişi sınırı sıfırdan büyük olmalıdır."
            )

        self._saat = saat or (
            lambda: datetime.now(UTC)
        )

        self.guvenlik = (
            guvenlik
            or CihazGuvenlikYoneticisi(
                saat=self._saat
            )
        )

        self.baglanti = (
            baglanti
            or CihazBaglantiYoneticisi(
                self.guvenlik,
                saat=self._saat,
            )
        )

        self._cihaz_kayitlari: dict[
            str,
            YetkiliCihazKaydi,
        ] = {}

        self._komutlar: dict[
            str,
            CihazKomutu,
        ] = {}

        self._komut_sirasi: deque[
            str
        ] = deque(
            maxlen=komut_gecmisi_siniri
        )

        self._bekleyen_komutlar: deque[
            str
        ] = deque()

        self._isleyiciler: dict[
            IslemYetkisi,
            KomutIsleyici,
        ] = {}

        self._kilit = RLock()

    def cihaz_kaydet(
        self,
        kayit: YetkiliCihazKaydi,
    ) -> YetkiliCihazKaydi:
        if (
            kayit.cihaz_kimligi
            in self._cihaz_kayitlari
        ):
            raise CihazYonetimHatasi(
                "Yetkili cihaz zaten kayıtlı."
            )

        izinler = (
            set(kayit.izinler)
            if kayit.izinler
            else None
        )

        self.guvenlik.cihaz_kaydet(
            cihaz_kimligi=(
                kayit.cihaz_kimligi
            ),
            cihaz_parmak_izi=(
                kayit.cihaz_parmak_izi
            ),
            yetki=kayit.yetki,
            gizli_anahtar=(
                kayit.gizli_anahtar
            ),
            izinler=izinler,
        )

        self._cihaz_kayitlari[
            kayit.cihaz_kimligi
        ] = kayit

        return kayit

    def cihaz_getir(
        self,
        cihaz_kimligi: str,
    ) -> YetkiliCihazKaydi:
        try:
            return self._cihaz_kayitlari[
                cihaz_kimligi
            ]
        except KeyError as hata:
            raise CihazYonetimHatasi(
                f"Yetkili cihaz bulunamadı: {cihaz_kimligi}"
            ) from hata

    def cihazlari_listele(
        self,
    ) -> tuple[YetkiliCihazKaydi, ...]:
        return tuple(
            self._cihaz_kayitlari[kimlik]
            for kimlik in sorted(
                self._cihaz_kayitlari
            )
        )

    def oturum_ac(
        self,
        *,
        cihaz_kimligi: str,
        cihaz_parmak_izi: str,
        gizli_anahtar: str,
        veri: dict[str, Any] | None = None,
    ) -> CihazOturumu:
        self.cihaz_getir(
            cihaz_kimligi
        )

        return self.baglanti.oturum_ac(
            cihaz_kimligi=cihaz_kimligi,
            cihaz_parmak_izi=(
                cihaz_parmak_izi
            ),
            gizli_anahtar=gizli_anahtar,
            veri=dict(veri or {}),
        )

    def isleyici_kaydet(
        self,
        islem_yetkisi: IslemYetkisi,
        isleyici: KomutIsleyici,
    ) -> None:
        if not callable(isleyici):
            raise TypeError(
                "Komut işleyici çağrılabilir olmalıdır."
            )

        self._isleyiciler[
            islem_yetkisi
        ] = isleyici

    def komut_olustur(
        self,
        *,
        oturum_kimligi: str,
        hedef_cihaz_kimligi: str,
        islem_yetkisi: IslemYetkisi,
        icerik: dict[str, Any] | None = None,
        gerekce: str | None = None,
        insan_onayi: str | None = None,
    ) -> CihazKomutu:
        oturum = self.baglanti.oturum_getir(
            oturum_kimligi
        )

        if not oturum.bagli_mi:
            raise CihazYonetimHatasi(
                "Komut için cihaz oturumu bağlı olmalıdır."
            )

        self.cihaz_getir(
            oturum.cihaz_kimligi
        )

        self.cihaz_getir(
            hedef_cihaz_kimligi
        )

        komut = CihazKomutu(
            komut_kimligi=(
                "SYK-CIHAZ-KOMUT-"
                + uuid4().hex.upper()
            ),
            kaynak_cihaz_kimligi=(
                oturum.cihaz_kimligi
            ),
            hedef_cihaz_kimligi=(
                hedef_cihaz_kimligi
            ),
            islem_yetkisi=islem_yetkisi,
            olusturulma_zamani=(
                self._saat()
            ),
            icerik=dict(icerik or {}),
            gerekce=gerekce,
            insan_onayi=insan_onayi,
        )

        try:
            self.guvenlik.yetki_dogrula(
                cihaz_kimligi=(
                    komut.kaynak_cihaz_kimligi
                ),
                islem_yetkisi=(
                    islem_yetkisi
                ),
            )

            self._kritik_onay_dogrula(
                komut
            )

            mesaj = (
                self.baglanti.mesaj_olustur(
                    oturum_kimligi=(
                        oturum_kimligi
                    ),
                    hedef_cihaz_kimligi=(
                        hedef_cihaz_kimligi
                    ),
                    mesaj_turu=(
                        MesajTuru.KOMUT
                    ),
                    icerik={
                        "komut_kimliği": (
                            komut.komut_kimligi
                        ),
                        "işlem_yetkisi": (
                            islem_yetkisi.value
                        ),
                        "içerik": dict(
                            komut.icerik
                        ),
                        "gerekçe": (
                            komut.gerekce
                        ),
                        "insan_onayı": (
                            komut.insan_onayi
                        ),
                    },
                )
            )

            komut.mesaj_kimligi = (
                mesaj.mesaj_kimligi
            )

            komut.durum = (
                KomutDurumu.KUYRUKTA
            )

            with self._kilit:
                self._komutlar[
                    komut.komut_kimligi
                ] = komut

                self._komut_sirasi.append(
                    komut.komut_kimligi
                )

                self._bekleyen_komutlar.append(
                    komut.komut_kimligi
                )

            return komut

        except (
            GuvenlikHatasi,
            CihazYonetimHatasi,
        ) as hata:
            komut.durum = (
                KomutDurumu.REDDEDILDI
            )

            komut.hata = str(hata)
            komut.tamamlanma_zamani = (
                self._saat()
            )

            self._komutlar[
                komut.komut_kimligi
            ] = komut

            self._komut_sirasi.append(
                komut.komut_kimligi
            )

            raise

    def siradaki_komutu_calistir(
        self,
    ) -> CihazKomutu | None:
        with self._kilit:
            if not self._bekleyen_komutlar:
                return None

            komut_kimligi = (
                self._bekleyen_komutlar
                .popleft()
            )

        komut = self.komut_getir(
            komut_kimligi
        )

        if (
            komut.durum
            is not KomutDurumu.KUYRUKTA
        ):
            return komut

        isleyici = self._isleyiciler.get(
            komut.islem_yetkisi
        )

        if isleyici is None:
            komut.durum = (
                KomutDurumu.HATA
            )

            komut.hata = (
                "Komut işleyicisi kayıtlı değil."
            )

            komut.tamamlanma_zamani = (
                self._saat()
            )

            return komut

        komut.durum = (
            KomutDurumu.CALISIYOR
        )

        try:
            sonuc = isleyici(
                komut
            )

            komut.sonuc = dict(
                sonuc or {}
            )

            komut.durum = (
                KomutDurumu.TAMAMLANDI
            )

            komut.hata = None

        except Exception as hata:
            komut.durum = (
                KomutDurumu.HATA
            )

            komut.hata = str(hata)

        komut.tamamlanma_zamani = (
            self._saat()
        )

        return komut

    def tum_bekleyenleri_calistir(
        self,
    ) -> tuple[CihazKomutu, ...]:
        sonuclar: list[
            CihazKomutu
        ] = []

        while True:
            komut = (
                self.siradaki_komutu_calistir()
            )

            if komut is None:
                break

            sonuclar.append(
                komut
            )

        return tuple(
            sonuclar
        )

    def komut_getir(
        self,
        komut_kimligi: str,
    ) -> CihazKomutu:
        try:
            return self._komutlar[
                komut_kimligi
            ]
        except KeyError as hata:
            raise CihazYonetimHatasi(
                f"Komut bulunamadı: {komut_kimligi}"
            ) from hata

    def komutlari_listele(
        self,
    ) -> tuple[CihazKomutu, ...]:
        return tuple(
            self._komutlar[kimlik]
            for kimlik in self._komut_sirasi
            if kimlik in self._komutlar
        )

    def canlilik_bildir(
        self,
        oturum_kimligi: str,
    ) -> CihazOturumu:
        return self.baglanti.canlilik_bildir(
            oturum_kimligi
        )

    def zaman_asimlarini_kontrol_et(
        self,
    ) -> tuple[CihazOturumu, ...]:
        return (
            self.baglanti
            .zaman_asimlarini_kontrol_et()
        )

    def durum_ozeti(
        self,
    ) -> dict[str, Any]:
        komutlar = self.komutlari_listele()

        return {
            "kayıtlı_cihaz_sayısı": len(
                self._cihaz_kayitlari
            ),
            "toplam_komut_sayısı": len(
                komutlar
            ),
            "kuyruktaki_komut_sayısı": sum(
                1
                for komut in komutlar
                if komut.durum
                is KomutDurumu.KUYRUKTA
            ),
            "tamamlanan_komut_sayısı": sum(
                1
                for komut in komutlar
                if komut.durum
                is KomutDurumu.TAMAMLANDI
            ),
            "reddedilen_komut_sayısı": sum(
                1
                for komut in komutlar
                if komut.durum
                is KomutDurumu.REDDEDILDI
            ),
            "hatalı_komut_sayısı": sum(
                1
                for komut in komutlar
                if komut.durum
                is KomutDurumu.HATA
            ),
            "bağlantı": (
                self.baglanti.durum_ozeti()
            ),
            "güvenlik": (
                self.guvenlik.durum_ozeti()
            ),
            "komutlar": [
                komut.sozluk()
                for komut in komutlar
            ],
        }

    def _kritik_onay_dogrula(
        self,
        komut: CihazKomutu,
    ) -> None:
        if (
            komut.islem_yetkisi
            not in self.KRITIK_ISLEMLER
        ):
            return

        if not komut.gerekce:
            raise CihazYonetimHatasi(
                "Kritik işlem için gerekçe zorunludur."
            )

        if (
            komut.insan_onayi
            not in {
                "Bilge Kaan",
                "Kurucu Kaan",
            }
        ):
            raise CihazYonetimHatasi(
                "Kritik işlem için Bilge Kaan veya "
                "Kurucu Kaan insan onayı zorunludur."
            )
