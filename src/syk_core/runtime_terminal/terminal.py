"""SyKaşif yetkili cihaz ve terminal komut yöneticisi."""

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

from .modeller import (
    BildirimTuru,
    CihazDurumu,
    KomutDurumu,
    KomutTuru,
    TerminalBildirimi,
    TerminalHatasi,
    TerminalKomutu,
    YetkiliCihaz,
    YetkiliCihazTanimi,
    YetkiSeviyesi,
)


KomutIsleyici = Callable[
    [TerminalKomutu],
    dict[str, Any] | None,
]


class CalismaTerminali:
    """Yetkili cihazları ve güvenli terminal komutlarını yönetir."""

    def __init__(
        self,
        *,
        olay_hatti: RuntimeEventBus | None = None,
        saat: Callable[[], datetime] | None = None,
        kuyruk_siniri: int = 1000,
        bildirim_siniri: int = 1000,
    ) -> None:
        if kuyruk_siniri <= 0:
            raise ValueError(
                "Komut kuyruğu sınırı sıfırdan büyük olmalıdır."
            )

        if bildirim_siniri <= 0:
            raise ValueError(
                "Bildirim sınırı sıfırdan büyük olmalıdır."
            )

        self.olay_hatti = olay_hatti or RuntimeEventBus()
        self._saat = saat or (
            lambda: datetime.now(UTC)
        )

        self.kuyruk_siniri = kuyruk_siniri
        self.bildirim_siniri = bildirim_siniri

        self._cihazlar: dict[
            str,
            YetkiliCihaz,
        ] = {}

        self._komutlar: dict[
            str,
            TerminalKomutu,
        ] = {}

        self._komut_kuyrugu: deque[
            str
        ] = deque()

        self._bildirimler: deque[
            TerminalBildirimi
        ] = deque(
            maxlen=bildirim_siniri
        )

        self._isleyiciler: dict[
            KomutTuru,
            KomutIsleyici,
        ] = {}

        self._kilit = RLock()

    def cihaz_kaydet(
        self,
        tanim: YetkiliCihazTanimi,
    ) -> YetkiliCihaz:
        with self._kilit:
            if (
                tanim.cihaz_kimligi
                in self._cihazlar
            ):
                raise TerminalHatasi(
                    "Cihaz zaten kayıtlı: "
                    f"{tanim.cihaz_kimligi}"
                )

            cihaz = YetkiliCihaz(
                tanim=tanim,
                kayit_zamani=self._saat(),
            )

            self._cihazlar[
                tanim.cihaz_kimligi
            ] = cihaz

        self._olay_yayinla(
            konu="terminal.cihaz.kaydedildi",
            icerik={
                "cihaz_kimliği": (
                    tanim.cihaz_kimligi
                ),
                "cihaz_türü": (
                    tanim.cihaz_turu.value
                ),
                "yetki_seviyesi": (
                    tanim.yetki_seviyesi.value
                ),
            },
        )

        return cihaz

    def cihaz_bagla(
        self,
        cihaz_kimligi: str,
        *,
        cihaz_parmak_izi: str,
    ) -> YetkiliCihaz:
        cihaz = self.cihaz_getir(
            cihaz_kimligi
        )

        if cihaz.engelli_mi:
            raise TerminalHatasi(
                "Engelli cihaz bağlanamaz."
            )

        if (
            cihaz.tanim.cihaz_parmak_izi
            != cihaz_parmak_izi
        ):
            cihaz.durum = CihazDurumu.HATA
            cihaz.son_hata = (
                "Cihaz parmak izi uyuşmuyor."
            )

            self._olay_yayinla(
                konu=(
                    "terminal.cihaz."
                    "kimlik_dogrulama_hatasi"
                ),
                icerik={
                    "cihaz_kimliği": cihaz_kimligi,
                },
            )

            raise TerminalHatasi(
                "Cihaz kimliği doğrulanamadı."
            )

        cihaz.durum = CihazDurumu.BAGLI
        cihaz.son_baglanti_zamani = (
            self._saat()
        )
        cihaz.son_hata = None
        cihaz.baglanti_sayisi += 1

        self._olay_yayinla(
            konu="terminal.cihaz.baglandi",
            icerik={
                "cihaz_kimliği": cihaz_kimligi,
            },
        )

        return cihaz

    def cihaz_ayir(
        self,
        cihaz_kimligi: str,
        *,
        aciklama: str | None = None,
    ) -> YetkiliCihaz:
        cihaz = self.cihaz_getir(
            cihaz_kimligi
        )

        cihaz.durum = CihazDurumu.CEVRIMDISI
        cihaz.son_ayrilma_zamani = (
            self._saat()
        )
        cihaz.son_hata = aciklama

        self._olay_yayinla(
            konu="terminal.cihaz.ayrildi",
            icerik={
                "cihaz_kimliği": cihaz_kimligi,
                "açıklama": aciklama,
            },
        )

        return cihaz

    def cihaz_engelle(
        self,
        cihaz_kimligi: str,
        *,
        gerekce: str,
    ) -> YetkiliCihaz:
        cihaz = self.cihaz_getir(
            cihaz_kimligi
        )

        cihaz.durum = CihazDurumu.ENGELLI
        cihaz.son_hata = gerekce
        cihaz.son_ayrilma_zamani = (
            self._saat()
        )

        self._olay_yayinla(
            konu="terminal.cihaz.engellendi",
            icerik={
                "cihaz_kimliği": cihaz_kimligi,
                "gerekçe": gerekce,
            },
        )

        return cihaz

    def cihaz_engelini_kaldir(
        self,
        cihaz_kimligi: str,
    ) -> YetkiliCihaz:
        cihaz = self.cihaz_getir(
            cihaz_kimligi
        )

        cihaz.durum = CihazDurumu.KAYITLI
        cihaz.son_hata = None

        self._olay_yayinla(
            konu=(
                "terminal.cihaz."
                "engeli_kaldirildi"
            ),
            icerik={
                "cihaz_kimliği": cihaz_kimligi,
            },
        )

        return cihaz

    def cihaz_getir(
        self,
        cihaz_kimligi: str,
    ) -> YetkiliCihaz:
        try:
            return self._cihazlar[
                cihaz_kimligi
            ]
        except KeyError as hata:
            raise TerminalHatasi(
                f"Cihaz bulunamadı: {cihaz_kimligi}"
            ) from hata

    def cihazlari_listele(
        self,
    ) -> tuple[YetkiliCihaz, ...]:
        return tuple(
            self._cihazlar[kimlik]
            for kimlik in sorted(
                self._cihazlar
            )
        )

    def isleyici_kaydet(
        self,
        komut_turu: KomutTuru,
        isleyici: KomutIsleyici,
    ) -> None:
        if not callable(isleyici):
            raise TypeError(
                "Komut işleyici çağrılabilir olmalıdır."
            )

        self._isleyiciler[
            komut_turu
        ] = isleyici

    def komut_olustur(
        self,
        *,
        kaynak_cihaz_kimligi: str,
        hedef_cihaz_kimligi: str,
        komut_turu: KomutTuru,
        icerik: dict[str, Any] | None = None,
        gerekce: str | None = None,
        onaylayan: str | None = None,
        komut_kimligi: str | None = None,
    ) -> TerminalKomutu:
        kaynak = self.cihaz_getir(
            kaynak_cihaz_kimligi
        )
        hedef = self.cihaz_getir(
            hedef_cihaz_kimligi
        )

        self._komut_yetkisini_dogrula(
            kaynak=kaynak,
            hedef=hedef,
            komut_turu=komut_turu,
            onaylayan=onaylayan,
        )

        if (
            len(self._komut_kuyrugu)
            >= self.kuyruk_siniri
        ):
            raise TerminalHatasi(
                "Komut kuyruğu dolu."
            )

        kimlik = (
            komut_kimligi
            or "SYK-KOMUT-"
            + uuid4().hex.upper()
        )

        if kimlik in self._komutlar:
            raise TerminalHatasi(
                f"Komut kimliği zaten kayıtlı: {kimlik}"
            )

        komut = TerminalKomutu(
            komut_kimligi=kimlik,
            komut_turu=komut_turu,
            kaynak_cihaz_kimligi=(
                kaynak_cihaz_kimligi
            ),
            hedef_cihaz_kimligi=(
                hedef_cihaz_kimligi
            ),
            olusturulma_zamani=self._saat(),
            durum=KomutDurumu.KUYRUKTA,
            icerik=dict(icerik or {}),
            gerekce=gerekce,
            onaylayan=onaylayan,
        )

        with self._kilit:
            self._komutlar[kimlik] = komut
            self._komut_kuyrugu.append(
                kimlik
            )

        kaynak.gonderilen_komut_sayisi += 1

        self._olay_yayinla(
            konu="terminal.komut.kuyruga_alindi",
            icerik={
                "komut_kimliği": kimlik,
                "komut_türü": komut_turu.value,
                "kaynak_cihaz_kimliği": (
                    kaynak_cihaz_kimligi
                ),
                "hedef_cihaz_kimliği": (
                    hedef_cihaz_kimligi
                ),
            },
        )

        return komut

    def siradaki_komutu_calistir(
        self,
    ) -> TerminalKomutu | None:
        with self._kilit:
            if not self._komut_kuyrugu:
                return None

            komut_kimligi = (
                self._komut_kuyrugu.popleft()
            )

        komut = self.komut_getir(
            komut_kimligi
        )

        hedef = self.cihaz_getir(
            komut.hedef_cihaz_kimligi
        )

        if not hedef.bagli_mi:
            return self._komutu_reddet(
                komut,
                "Hedef cihaz bağlı değil.",
            )

        isleyici = self._isleyiciler.get(
            komut.komut_turu
        )

        if isleyici is None:
            return self._komutu_reddet(
                komut,
                "Komut işleyicisi bulunamadı.",
            )

        komut.durum = KomutDurumu.CALISIYOR
        komut.calisma_zamani = self._saat()

        self._olay_yayinla(
            konu="terminal.komut.basladi",
            icerik={
                "komut_kimliği": (
                    komut.komut_kimligi
                ),
            },
        )

        try:
            sonuc = isleyici(komut)

            komut.durum = KomutDurumu.TAMAMLANDI
            komut.tamamlanma_zamani = (
                self._saat()
            )
            komut.sonuc = dict(
                sonuc or {}
            )

            hedef.tamamlanan_komut_sayisi += 1

            self._olay_yayinla(
                konu="terminal.komut.tamamlandi",
                icerik={
                    "komut_kimliği": (
                        komut.komut_kimligi
                    ),
                    "sonuç": dict(
                        komut.sonuc
                    ),
                },
            )

            return komut

        except Exception as hata:
            komut.durum = KomutDurumu.HATA
            komut.tamamlanma_zamani = (
                self._saat()
            )
            komut.hata = str(hata)

            self._olay_yayinla(
                konu="terminal.komut.hata",
                icerik={
                    "komut_kimliği": (
                        komut.komut_kimligi
                    ),
                    "hata": str(hata),
                },
            )

            return komut

    def kuyrugu_calistir(
        self,
        *,
        sinir: int | None = None,
    ) -> tuple[TerminalKomutu, ...]:
        if sinir is not None and sinir <= 0:
            raise ValueError(
                "Çalıştırma sınırı sıfırdan büyük olmalıdır."
            )

        sonuclar: list[
            TerminalKomutu
        ] = []

        while self._komut_kuyrugu:
            if (
                sinir is not None
                and len(sonuclar) >= sinir
            ):
                break

            komut = (
                self.siradaki_komutu_calistir()
            )

            if komut is not None:
                sonuclar.append(komut)

        return tuple(sonuclar)

    def komut_iptal_et(
        self,
        komut_kimligi: str,
        *,
        gerekce: str,
    ) -> TerminalKomutu:
        komut = self.komut_getir(
            komut_kimligi
        )

        if komut.sonlandi_mi:
            raise TerminalHatasi(
                "Sonlanmış komut iptal edilemez."
            )

        if (
            komut.durum
            is KomutDurumu.CALISIYOR
        ):
            raise TerminalHatasi(
                "Çalışan komut iptal edilemez."
            )

        komut.durum = (
            KomutDurumu.IPTAL_EDILDI
        )
        komut.tamamlanma_zamani = (
            self._saat()
        )
        komut.hata = gerekce

        try:
            self._komut_kuyrugu.remove(
                komut_kimligi
            )
        except ValueError:
            pass

        self._olay_yayinla(
            konu="terminal.komut.iptal_edildi",
            icerik={
                "komut_kimliği": komut_kimligi,
                "gerekçe": gerekce,
            },
        )

        return komut

    def komut_getir(
        self,
        komut_kimligi: str,
    ) -> TerminalKomutu:
        try:
            return self._komutlar[
                komut_kimligi
            ]
        except KeyError as hata:
            raise TerminalHatasi(
                f"Komut bulunamadı: {komut_kimligi}"
            ) from hata

    def komutlari_listele(
        self,
    ) -> tuple[TerminalKomutu, ...]:
        return tuple(
            self._komutlar[kimlik]
            for kimlik in sorted(
                self._komutlar
            )
        )

    def bildirim_olustur(
        self,
        *,
        bildirim_turu: BildirimTuru,
        baslik: str,
        aciklama: str,
        hedef_cihaz_kimligi: str | None = None,
        veri: dict[str, Any] | None = None,
    ) -> TerminalBildirimi:
        if hedef_cihaz_kimligi is not None:
            self.cihaz_getir(
                hedef_cihaz_kimligi
            )

        bildirim = TerminalBildirimi(
            bildirim_kimligi=(
                "SYK-BILDIRIM-"
                + uuid4().hex.upper()
            ),
            bildirim_turu=bildirim_turu,
            baslik=baslik,
            aciklama=aciklama,
            olusturulma_zamani=self._saat(),
            hedef_cihaz_kimligi=(
                hedef_cihaz_kimligi
            ),
            veri=dict(veri or {}),
        )

        self._bildirimler.append(
            bildirim
        )

        self._olay_yayinla(
            konu="terminal.bildirim.olusturuldu",
            icerik=bildirim.sozluk(),
        )

        return bildirim

    @property
    def bildirimler(
        self,
    ) -> tuple[TerminalBildirimi, ...]:
        return tuple(self._bildirimler)

    @property
    def kuyruktaki_komut_sayisi(
        self,
    ) -> int:
        return len(self._komut_kuyrugu)

    def durum_ozeti(
        self,
    ) -> dict[str, Any]:
        cihazlar = self.cihazlari_listele()
        komutlar = self.komutlari_listele()

        return {
            "toplam_cihaz_sayısı": len(cihazlar),
            "bağlı_cihaz_sayısı": sum(
                1
                for cihaz in cihazlar
                if cihaz.bagli_mi
            ),
            "çevrimdışı_cihaz_sayısı": sum(
                1
                for cihaz in cihazlar
                if cihaz.durum
                is CihazDurumu.CEVRIMDISI
            ),
            "engelli_cihaz_sayısı": sum(
                1
                for cihaz in cihazlar
                if cihaz.engelli_mi
            ),
            "toplam_komut_sayısı": len(
                komutlar
            ),
            "kuyruktaki_komut_sayısı": (
                self.kuyruktaki_komut_sayisi
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
            "bildirim_sayısı": len(
                self._bildirimler
            ),
            "cihazlar": [
                cihaz.sozluk()
                for cihaz in cihazlar
            ],
            "komutlar": [
                komut.sozluk()
                for komut in komutlar
            ],
            "bildirimler": [
                bildirim.sozluk()
                for bildirim
                in self._bildirimler
            ],
        }

    def _komut_yetkisini_dogrula(
        self,
        *,
        kaynak: YetkiliCihaz,
        hedef: YetkiliCihaz,
        komut_turu: KomutTuru,
        onaylayan: str | None,
    ) -> None:
        if kaynak.engelli_mi:
            raise TerminalHatasi(
                "Engelli cihaz komut gönderemez."
            )

        if hedef.engelli_mi:
            raise TerminalHatasi(
                "Engelli cihaza komut gönderilemez."
            )

        if not kaynak.bagli_mi:
            raise TerminalHatasi(
                "Kaynak cihaz bağlı değil."
            )

        if (
            kaynak.tanim.yetki_seviyesi
            is YetkiSeviyesi.IZLEYICI
        ):
            raise TerminalHatasi(
                "İzleyici yetkisi komut gönderemez."
            )

        kritik_komutlar = {
            KomutTuru.MASAUSTUNU_KAPAT,
            KomutTuru.MASAUSTUNU_UYANDIR,
            KomutTuru.CALISMA_SISTEMINI_DURDUR,
        }

        if komut_turu in kritik_komutlar:
            if (
                kaynak.tanim.yetki_seviyesi
                not in {
                    YetkiSeviyesi.BILGE_KAAN,
                    YetkiSeviyesi.KURUCU_KAAN,
                }
            ):
                raise TerminalHatasi(
                    "Bu komut için Bilge Kaan "
                    "veya Kurucu Kaan yetkisi gerekir."
                )

            if not onaylayan:
                raise TerminalHatasi(
                    "Kritik komut için insan onayı gerekir."
                )

    def _komutu_reddet(
        self,
        komut: TerminalKomutu,
        gerekce: str,
    ) -> TerminalKomutu:
        komut.durum = KomutDurumu.REDDEDILDI
        komut.tamamlanma_zamani = (
            self._saat()
        )
        komut.hata = gerekce

        hedef = self.cihaz_getir(
            komut.hedef_cihaz_kimligi
        )
        hedef.reddedilen_komut_sayisi += 1

        self._olay_yayinla(
            konu="terminal.komut.reddedildi",
            icerik={
                "komut_kimliği": (
                    komut.komut_kimligi
                ),
                "gerekçe": gerekce,
            },
        )

        return komut

    def _olay_yayinla(
        self,
        *,
        konu: str,
        icerik: dict[str, Any],
    ) -> None:
        self.olay_hatti.publish(
            RuntimeEvent(
                topic=konu,
                source="çalışma_terminali",
                payload=icerik,
            )
        )
