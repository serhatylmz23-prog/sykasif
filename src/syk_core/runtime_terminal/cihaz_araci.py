"""SyKaşif masaüstü yetkili cihaz aracısı."""

from __future__ import annotations

from collections import deque
from datetime import UTC, datetime
from threading import RLock
from typing import Any, Callable
from uuid import uuid4

from syk_core.runtime_kernel import (
    RuntimeEvent,
    RuntimeEventBus,
)

from .arac_modelleri import (
    AracDurumu,
    AracIslemi,
    CihazAraciHatasi,
    IslemDurumu,
    IslemTuru,
    UygulamaDurumu,
    UygulamaTanimi,
)
from .modeller import (
    KomutTuru,
    TerminalHatasi,
    TerminalKomutu,
    YetkiSeviyesi,
)
from .terminal import CalismaTerminali


UygulamaBaslatici = Callable[
    [UygulamaTanimi],
    int,
]

UygulamaKapatmaIsleyicisi = Callable[
    [UygulamaTanimi, UygulamaDurumu],
    bool,
]

SistemIsleyicisi = Callable[
    [IslemTuru, dict[str, Any]],
    dict[str, Any] | None,
]


class YetkiliCihazAraci:
    """Masaüstü uygulamalarını ve güvenli sistem işlemlerini yönetir."""

    def __init__(
        self,
        terminal: CalismaTerminali,
        *,
        cihaz_kimligi: str,
        olay_hatti: RuntimeEventBus | None = None,
        saat: Callable[[], datetime] | None = None,
        uygulama_baslatici: UygulamaBaslatici | None = None,
        uygulama_kapatici: UygulamaKapatmaIsleyicisi | None = None,
        sistem_isleyicisi: SistemIsleyicisi | None = None,
        islem_gecmisi_siniri: int = 1000,
    ) -> None:
        if not cihaz_kimligi.strip():
            raise ValueError(
                "Cihaz kimliği boş olamaz."
            )

        if islem_gecmisi_siniri <= 0:
            raise ValueError(
                "İşlem geçmişi sınırı sıfırdan büyük olmalıdır."
            )

        self.terminal = terminal
        self.cihaz_kimligi = cihaz_kimligi
        self.olay_hatti = (
            olay_hatti
            or terminal.olay_hatti
        )
        self._saat = saat or (
            lambda: datetime.now(UTC)
        )

        self._uygulama_baslatici = (
            uygulama_baslatici
            or self._varsayilan_uygulama_baslatici
        )
        self._uygulama_kapatici = (
            uygulama_kapatici
            or self._varsayilan_uygulama_kapatici
        )
        self._sistem_isleyicisi = (
            sistem_isleyicisi
            or self._varsayilan_sistem_isleyicisi
        )

        self.durum = AracDurumu.HAZIRLANIYOR
        self.son_hata: str | None = None
        self.baslama_zamani: datetime | None = None
        self.durdurma_zamani: datetime | None = None
        self.islenen_komut_sayisi = 0
        self.reddedilen_komut_sayisi = 0
        self.hatali_komut_sayisi = 0

        self._uygulamalar: dict[
            str,
            UygulamaTanimi,
        ] = {}

        self._uygulama_durumlari: dict[
            str,
            UygulamaDurumu,
        ] = {}

        self._islemler: dict[
            str,
            AracIslemi,
        ] = {}

        self._islem_gecmisi: deque[
            str
        ] = deque(
            maxlen=islem_gecmisi_siniri
        )

        self._kilit = RLock()

        self._cihazi_dogrula()
        self._komut_isleyicilerini_kaydet()

        self.durum = AracDurumu.HAZIR
        self.baslama_zamani = self._saat()

        self._olay_yayinla(
            konu="terminal.arac.hazir",
            icerik={
                "cihaz_kimliği": self.cihaz_kimligi,
            },
        )

    def uygulama_kaydet(
        self,
        tanim: UygulamaTanimi,
    ) -> UygulamaTanimi:
        with self._kilit:
            if (
                tanim.uygulama_kimligi
                in self._uygulamalar
            ):
                raise CihazAraciHatasi(
                    "Uygulama zaten kayıtlı: "
                    f"{tanim.uygulama_kimligi}"
                )

            self._uygulamalar[
                tanim.uygulama_kimligi
            ] = tanim

            self._uygulama_durumlari[
                tanim.uygulama_kimligi
            ] = UygulamaDurumu(
                uygulama_kimligi=(
                    tanim.uygulama_kimligi
                )
            )

        self._olay_yayinla(
            konu="terminal.arac.uygulama_kaydedildi",
            icerik=tanim.sozluk(),
        )

        return tanim

    def uygulama_getir(
        self,
        uygulama_kimligi: str,
    ) -> UygulamaTanimi:
        try:
            return self._uygulamalar[
                uygulama_kimligi
            ]
        except KeyError as hata:
            raise CihazAraciHatasi(
                "Uygulama bulunamadı: "
                f"{uygulama_kimligi}"
            ) from hata

    def uygulama_durumu_getir(
        self,
        uygulama_kimligi: str,
    ) -> UygulamaDurumu:
        self.uygulama_getir(
            uygulama_kimligi
        )

        return self._uygulama_durumlari[
            uygulama_kimligi
        ]

    def uygulamalari_listele(
        self,
    ) -> tuple[UygulamaTanimi, ...]:
        return tuple(
            self._uygulamalar[kimlik]
            for kimlik in sorted(
                self._uygulamalar
            )
        )

    def uygulamayi_ac(
        self,
        *,
        kaynak_cihaz_kimligi: str,
        uygulama_kimligi: str,
        gerekce: str | None = None,
    ) -> AracIslemi:
        islem = self._islem_olustur(
            islem_turu=IslemTuru.UYGULAMA_AC,
            kaynak_cihaz_kimligi=(
                kaynak_cihaz_kimligi
            ),
            uygulama_kimligi=(
                uygulama_kimligi
            ),
            gerekce=gerekce,
        )

        tanim = self.uygulama_getir(
            uygulama_kimligi
        )
        durum = self.uygulama_durumu_getir(
            uygulama_kimligi
        )

        if durum.calisiyor_mu:
            return self._islemi_reddet(
                islem,
                "Uygulama zaten çalışıyor.",
            )

        self._islemi_baslat(islem)

        try:
            islem_kimligi = (
                self._uygulama_baslatici(
                    tanim
                )
            )

            if (
                not isinstance(
                    islem_kimligi,
                    int,
                )
                or islem_kimligi <= 0
            ):
                raise CihazAraciHatasi(
                    "Uygulama başlatıcısı geçerli "
                    "bir işlem kimliği döndürmedi."
                )

            simdi = self._saat()

            durum.calisiyor_mu = True
            durum.islem_kimligi = (
                islem_kimligi
            )
            durum.baslama_zamani = simdi
            durum.kapanma_zamani = None
            durum.son_hata = None
            durum.baslatma_sayisi += 1

            return self._islemi_tamamla(
                islem,
                {
                    "uygulama_kimliği": (
                        uygulama_kimligi
                    ),
                    "uygulama_adı": (
                        tanim.gorunen_ad
                    ),
                    "işlem_kimliği": (
                        islem_kimligi
                    ),
                    "durum": "açıldı",
                },
            )

        except Exception as hata:
            durum.son_hata = str(hata)

            return self._islemi_hata_yap(
                islem,
                str(hata),
            )

    def uygulamayi_kapat(
        self,
        *,
        kaynak_cihaz_kimligi: str,
        uygulama_kimligi: str,
        gerekce: str | None = None,
    ) -> AracIslemi:
        islem = self._islem_olustur(
            islem_turu=IslemTuru.UYGULAMA_KAPAT,
            kaynak_cihaz_kimligi=(
                kaynak_cihaz_kimligi
            ),
            uygulama_kimligi=(
                uygulama_kimligi
            ),
            gerekce=gerekce,
        )

        tanim = self.uygulama_getir(
            uygulama_kimligi
        )
        durum = self.uygulama_durumu_getir(
            uygulama_kimligi
        )

        if not durum.calisiyor_mu:
            return self._islemi_reddet(
                islem,
                "Uygulama çalışmıyor.",
            )

        if not tanim.guvenli_kapatma_destegi:
            return self._islemi_reddet(
                islem,
                "Uygulama güvenli kapatmayı desteklemiyor.",
            )

        self._islemi_baslat(islem)

        try:
            kapandi_mi = (
                self._uygulama_kapatici(
                    tanim,
                    durum,
                )
            )

            if not kapandi_mi:
                raise CihazAraciHatasi(
                    "Uygulama güvenli biçimde kapatılamadı."
                )

            simdi = self._saat()

            durum.calisiyor_mu = False
            durum.islem_kimligi = None
            durum.kapanma_zamani = simdi
            durum.son_hata = None
            durum.kapatma_sayisi += 1

            return self._islemi_tamamla(
                islem,
                {
                    "uygulama_kimliği": (
                        uygulama_kimligi
                    ),
                    "uygulama_adı": (
                        tanim.gorunen_ad
                    ),
                    "durum": "kapatıldı",
                },
            )

        except Exception as hata:
            durum.son_hata = str(hata)

            return self._islemi_hata_yap(
                islem,
                str(hata),
            )

    def sistem_islemi_calistir(
        self,
        *,
        kaynak_cihaz_kimligi: str,
        islem_turu: IslemTuru,
        insan_onayi: str | None,
        gerekce: str,
        icerik: dict[str, Any] | None = None,
    ) -> AracIslemi:
        izinli_islemler = {
            IslemTuru.MASAUSTUNU_KAPAT,
            IslemTuru.MASAUSTUNU_UYANDIR,
            IslemTuru.GUVENLI_YENIDEN_BASLAT,
            IslemTuru.CALISMA_SISTEMINI_BASLAT,
            IslemTuru.CALISMA_SISTEMINI_DURDUR,
        }

        if islem_turu not in izinli_islemler:
            raise CihazAraciHatasi(
                "Bu yöntem yalnız sistem işlemleri için kullanılabilir."
            )

        islem = self._islem_olustur(
            islem_turu=islem_turu,
            kaynak_cihaz_kimligi=(
                kaynak_cihaz_kimligi
            ),
            insan_onayi=insan_onayi,
            gerekce=gerekce,
            icerik=dict(icerik or {}),
        )

        try:
            self._kritik_islem_yetkisini_dogrula(
                kaynak_cihaz_kimligi=(
                    kaynak_cihaz_kimligi
                ),
                insan_onayi=insan_onayi,
                gerekce=gerekce,
            )

        except Exception as hata:
            return self._islemi_reddet(
                islem,
                str(hata),
            )

        self._islemi_baslat(islem)

        try:
            sonuc = self._sistem_isleyicisi(
                islem_turu,
                dict(icerik or {}),
            )

            return self._islemi_tamamla(
                islem,
                dict(sonuc or {}),
            )

        except Exception as hata:
            return self._islemi_hata_yap(
                islem,
                str(hata),
            )

    def durum_bilgisi(
        self,
        *,
        kaynak_cihaz_kimligi: str,
    ) -> AracIslemi:
        islem = self._islem_olustur(
            islem_turu=IslemTuru.DURUM_BILGISI,
            kaynak_cihaz_kimligi=(
                kaynak_cihaz_kimligi
            ),
        )

        self._islemi_baslat(islem)

        return self._islemi_tamamla(
            islem,
            self.durum_ozeti(),
        )

    def komutu_isle(
        self,
        komut: TerminalKomutu,
    ) -> dict[str, Any]:
        if (
            komut.hedef_cihaz_kimligi
            != self.cihaz_kimligi
        ):
            raise CihazAraciHatasi(
                "Komut bu cihaz aracısına ait değil."
            )

        if komut.komut_turu is KomutTuru.DURUM_ISTE:
            islem = self.durum_bilgisi(
                kaynak_cihaz_kimligi=(
                    komut.kaynak_cihaz_kimligi
                )
            )

        elif komut.komut_turu is KomutTuru.UYGULAMA_AC:
            uygulama_kimligi = str(
                komut.icerik.get(
                    "uygulama_kimliği",
                    "",
                )
            )

            islem = self.uygulamayi_ac(
                kaynak_cihaz_kimligi=(
                    komut.kaynak_cihaz_kimligi
                ),
                uygulama_kimligi=(
                    uygulama_kimligi
                ),
                gerekce=komut.gerekce,
            )

        elif komut.komut_turu is KomutTuru.UYGULAMA_KAPAT:
            uygulama_kimligi = str(
                komut.icerik.get(
                    "uygulama_kimliği",
                    "",
                )
            )

            islem = self.uygulamayi_kapat(
                kaynak_cihaz_kimligi=(
                    komut.kaynak_cihaz_kimligi
                ),
                uygulama_kimligi=(
                    uygulama_kimligi
                ),
                gerekce=komut.gerekce,
            )

        elif komut.komut_turu is KomutTuru.MASAUSTUNU_KAPAT:
            islem = self.sistem_islemi_calistir(
                kaynak_cihaz_kimligi=(
                    komut.kaynak_cihaz_kimligi
                ),
                islem_turu=(
                    IslemTuru.MASAUSTUNU_KAPAT
                ),
                insan_onayi=komut.onaylayan,
                gerekce=(
                    komut.gerekce
                    or "Yetkili terminal komutu"
                ),
                icerik=komut.icerik,
            )

        elif komut.komut_turu is KomutTuru.MASAUSTUNU_UYANDIR:
            islem = self.sistem_islemi_calistir(
                kaynak_cihaz_kimligi=(
                    komut.kaynak_cihaz_kimligi
                ),
                islem_turu=(
                    IslemTuru.MASAUSTUNU_UYANDIR
                ),
                insan_onayi=komut.onaylayan,
                gerekce=(
                    komut.gerekce
                    or "Yetkili terminal komutu"
                ),
                icerik=komut.icerik,
            )

        elif (
            komut.komut_turu
            is KomutTuru.CALISMA_SISTEMINI_BASLAT
        ):
            islem = self.sistem_islemi_calistir(
                kaynak_cihaz_kimligi=(
                    komut.kaynak_cihaz_kimligi
                ),
                islem_turu=(
                    IslemTuru.CALISMA_SISTEMINI_BASLAT
                ),
                insan_onayi=(
                    komut.onaylayan
                    or komut.kaynak_cihaz_kimligi
                ),
                gerekce=(
                    komut.gerekce
                    or "Çalışma sistemi başlatma"
                ),
                icerik=komut.icerik,
            )

        elif (
            komut.komut_turu
            is KomutTuru.CALISMA_SISTEMINI_DURDUR
        ):
            islem = self.sistem_islemi_calistir(
                kaynak_cihaz_kimligi=(
                    komut.kaynak_cihaz_kimligi
                ),
                islem_turu=(
                    IslemTuru.CALISMA_SISTEMINI_DURDUR
                ),
                insan_onayi=komut.onaylayan,
                gerekce=(
                    komut.gerekce
                    or "Çalışma sistemi durdurma"
                ),
                icerik=komut.icerik,
            )

        else:
            raise CihazAraciHatasi(
                "Desteklenmeyen terminal komutu: "
                f"{komut.komut_turu.value}"
            )

        if islem.durum is IslemDurumu.TAMAMLANDI:
            return {
                "işlem_kimliği": (
                    islem.islem_kimligi
                ),
                "durum": "tamamlandı",
                "sonuç": dict(islem.sonuc),
            }

        if islem.durum is IslemDurumu.REDDEDILDI:
            raise CihazAraciHatasi(
                islem.hata
                or "İşlem reddedildi."
            )

        raise CihazAraciHatasi(
            islem.hata
            or "İşlem tamamlanamadı."
        )

    def islemi_getir(
        self,
        islem_kimligi: str,
    ) -> AracIslemi:
        try:
            return self._islemler[
                islem_kimligi
            ]
        except KeyError as hata:
            raise CihazAraciHatasi(
                "İşlem bulunamadı: "
                f"{islem_kimligi}"
            ) from hata

    def islemleri_listele(
        self,
    ) -> tuple[AracIslemi, ...]:
        return tuple(
            self._islemler[kimlik]
            for kimlik in self._islem_gecmisi
            if kimlik in self._islemler
        )

    def guvenli_durdur(
        self,
    ) -> None:
        if self.durum is AracDurumu.DURDURULDU:
            return

        for uygulama_kimligi in tuple(
            self._uygulamalar
        ):
            durum = self.uygulama_durumu_getir(
                uygulama_kimligi
            )

            if not durum.calisiyor_mu:
                continue

            tanim = self.uygulama_getir(
                uygulama_kimligi
            )

            if not tanim.guvenli_kapatma_destegi:
                continue

            try:
                self._uygulama_kapatici(
                    tanim,
                    durum,
                )

                durum.calisiyor_mu = False
                durum.islem_kimligi = None
                durum.kapanma_zamani = (
                    self._saat()
                )
                durum.kapatma_sayisi += 1

            except Exception as hata:
                durum.son_hata = str(hata)

        self.durum = AracDurumu.DURDURULDU
        self.durdurma_zamani = self._saat()

        self._olay_yayinla(
            konu="terminal.arac.durduruldu",
            icerik={
                "cihaz_kimliği": self.cihaz_kimligi,
            },
        )

    def durum_ozeti(
        self,
    ) -> dict[str, Any]:
        uygulamalar = self.uygulamalari_listele()
        islemler = self.islemleri_listele()

        return {
            "cihaz_kimliği": self.cihaz_kimligi,
            "araç_durumu": self.durum.value,
            "başlama_zamanı": (
                self.baslama_zamani.isoformat()
                if self.baslama_zamani
                else None
            ),
            "durdurma_zamanı": (
                self.durdurma_zamani.isoformat()
                if self.durdurma_zamani
                else None
            ),
            "son_hata": self.son_hata,
            "kayıtlı_uygulama_sayısı": len(
                uygulamalar
            ),
            "çalışan_uygulama_sayısı": sum(
                1
                for tanim in uygulamalar
                if self._uygulama_durumlari[
                    tanim.uygulama_kimligi
                ].calisiyor_mu
            ),
            "işlenen_komut_sayısı": (
                self.islenen_komut_sayisi
            ),
            "reddedilen_komut_sayısı": (
                self.reddedilen_komut_sayisi
            ),
            "hatalı_komut_sayısı": (
                self.hatali_komut_sayisi
            ),
            "uygulamalar": [
                {
                    **tanim.sozluk(),
                    "durum": (
                        self._uygulama_durumlari[
                            tanim.uygulama_kimligi
                        ].sozluk()
                    ),
                }
                for tanim in uygulamalar
            ],
            "işlemler": [
                islem.sozluk()
                for islem in islemler
            ],
        }

    def _cihazi_dogrula(
        self,
    ) -> None:
        cihaz = self.terminal.cihaz_getir(
            self.cihaz_kimligi
        )

        if cihaz.engelli_mi:
            raise CihazAraciHatasi(
                "Engelli cihaz için araç başlatılamaz."
            )

        if (
            cihaz.tanim.yetki_seviyesi
            not in {
                YetkiSeviyesi.BILGE_KAAN,
                YetkiSeviyesi.KURUCU_KAAN,
            }
        ):
            raise CihazAraciHatasi(
                "Cihaz aracısı için Bilge Kaan "
                "veya Kurucu Kaan yetkisi gerekir."
            )

    def _komut_isleyicilerini_kaydet(
        self,
    ) -> None:
        for komut_turu in (
            KomutTuru.DURUM_ISTE,
            KomutTuru.UYGULAMA_AC,
            KomutTuru.UYGULAMA_KAPAT,
            KomutTuru.MASAUSTUNU_KAPAT,
            KomutTuru.MASAUSTUNU_UYANDIR,
            KomutTuru.CALISMA_SISTEMINI_BASLAT,
            KomutTuru.CALISMA_SISTEMINI_DURDUR,
        ):
            self.terminal.isleyici_kaydet(
                komut_turu,
                self.komutu_isle,
            )

    def _kritik_islem_yetkisini_dogrula(
        self,
        *,
        kaynak_cihaz_kimligi: str,
        insan_onayi: str | None,
        gerekce: str,
    ) -> None:
        kaynak = self.terminal.cihaz_getir(
            kaynak_cihaz_kimligi
        )

        if not kaynak.bagli_mi:
            raise CihazAraciHatasi(
                "Kaynak cihaz bağlı değil."
            )

        if (
            kaynak.tanim.yetki_seviyesi
            not in {
                YetkiSeviyesi.BILGE_KAAN,
                YetkiSeviyesi.KURUCU_KAAN,
            }
        ):
            raise CihazAraciHatasi(
                "Kritik işlem için Bilge Kaan "
                "veya Kurucu Kaan yetkisi gerekir."
            )

        if not insan_onayi:
            raise CihazAraciHatasi(
                "Kritik işlem için insan onayı gerekir."
            )

        if not gerekce.strip():
            raise CihazAraciHatasi(
                "Kritik işlem gerekçesi boş olamaz."
            )

    def _islem_olustur(
        self,
        *,
        islem_turu: IslemTuru,
        kaynak_cihaz_kimligi: str,
        uygulama_kimligi: str | None = None,
        insan_onayi: str | None = None,
        gerekce: str | None = None,
        icerik: dict[str, Any] | None = None,
    ) -> AracIslemi:
        self.terminal.cihaz_getir(
            kaynak_cihaz_kimligi
        )

        islem = AracIslemi(
            islem_kimligi=(
                "SYK-ARAC-ISLEM-"
                + uuid4().hex.upper()
            ),
            islem_turu=islem_turu,
            kaynak_cihaz_kimligi=(
                kaynak_cihaz_kimligi
            ),
            uygulama_kimligi=(
                uygulama_kimligi
            ),
            insan_onayi=insan_onayi,
            gerekce=gerekce,
            icerik=dict(icerik or {}),
            olusturulma_zamani=self._saat(),
        )

        with self._kilit:
            self._islemler[
                islem.islem_kimligi
            ] = islem
            self._islem_gecmisi.append(
                islem.islem_kimligi
            )

        self._olay_yayinla(
            konu="terminal.arac.islem_olusturuldu",
            icerik={
                "işlem_kimliği": (
                    islem.islem_kimligi
                ),
                "işlem_türü": (
                    islem.islem_turu.value
                ),
                "kaynak_cihaz_kimliği": (
                    kaynak_cihaz_kimligi
                ),
            },
        )

        return islem

    def _islemi_baslat(
        self,
        islem: AracIslemi,
    ) -> None:
        islem.durum = IslemDurumu.CALISIYOR
        islem.baslama_zamani = self._saat()

        self._olay_yayinla(
            konu="terminal.arac.islem_basladi",
            icerik={
                "işlem_kimliği": (
                    islem.islem_kimligi
                ),
            },
        )

    def _islemi_tamamla(
        self,
        islem: AracIslemi,
        sonuc: dict[str, Any],
    ) -> AracIslemi:
        islem.durum = IslemDurumu.TAMAMLANDI
        islem.tamamlanma_zamani = self._saat()
        islem.sonuc = dict(sonuc)
        self.islenen_komut_sayisi += 1

        self._olay_yayinla(
            konu="terminal.arac.islem_tamamlandi",
            icerik={
                "işlem_kimliği": (
                    islem.islem_kimligi
                ),
                "sonuç": dict(sonuc),
            },
        )

        return islem

    def _islemi_reddet(
        self,
        islem: AracIslemi,
        hata: str,
    ) -> AracIslemi:
        islem.durum = IslemDurumu.REDDEDILDI
        islem.tamamlanma_zamani = self._saat()
        islem.hata = hata
        self.reddedilen_komut_sayisi += 1

        self._olay_yayinla(
            konu="terminal.arac.islem_reddedildi",
            icerik={
                "işlem_kimliği": (
                    islem.islem_kimligi
                ),
                "hata": hata,
            },
        )

        return islem

    def _islemi_hata_yap(
        self,
        islem: AracIslemi,
        hata: str,
    ) -> AracIslemi:
        islem.durum = IslemDurumu.HATA
        islem.tamamlanma_zamani = self._saat()
        islem.hata = hata
        self.hatali_komut_sayisi += 1
        self.son_hata = hata

        self._olay_yayinla(
            konu="terminal.arac.islem_hata",
            icerik={
                "işlem_kimliği": (
                    islem.islem_kimligi
                ),
                "hata": hata,
            },
        )

        return islem

    def _olay_yayinla(
        self,
        *,
        konu: str,
        icerik: dict[str, Any],
    ) -> None:
        self.olay_hatti.publish(
            RuntimeEvent(
                topic=konu,
                source="yetkili_cihaz_araci",
                payload=icerik,
            )
        )

    @staticmethod
    def _varsayilan_uygulama_baslatici(
        tanim: UygulamaTanimi,
    ) -> int:
        raise CihazAraciHatasi(
            "Gerçek uygulama başlatıcısı yapılandırılmadı."
        )

    @staticmethod
    def _varsayilan_uygulama_kapatici(
        tanim: UygulamaTanimi,
        durum: UygulamaDurumu,
    ) -> bool:
        raise CihazAraciHatasi(
            "Gerçek uygulama kapatıcısı yapılandırılmadı."
        )

    @staticmethod
    def _varsayilan_sistem_isleyicisi(
        islem_turu: IslemTuru,
        icerik: dict[str, Any],
    ) -> dict[str, Any]:
        raise CihazAraciHatasi(
            "Gerçek sistem işleyicisi yapılandırılmadı."
        )
