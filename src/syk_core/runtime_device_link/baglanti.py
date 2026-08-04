"""SyKaşif cihaz bağlantı yönetimi."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from threading import RLock
from typing import Any, Callable
from uuid import uuid4

from .cihaz_oturumu import (
    CihazOturumu,
    CihazOturumuHatasi,
    OturumDurumu,
)
from .guvenlik import (
    CihazGuvenlikYoneticisi,
    CihazYetkisi,
    GuvenlikHatasi,
)
from .protokol import (
    CihazMesaji,
    MesajDurumu,
    MesajTuru,
)


class CihazBaglantiYoneticisi:
    """Yetkili cihazların güvenli bağlantı oturumlarını yönetir."""

    def __init__(
        self,
        guvenlik: CihazGuvenlikYoneticisi,
        *,
        saat: Callable[[], datetime] | None = None,
        canlilik_zaman_asimi_saniye: int = 30,
        oturum_suresi_dakika: int = 480,
    ) -> None:
        if canlilik_zaman_asimi_saniye <= 0:
            raise ValueError(
                "Canlılık zaman aşımı sıfırdan büyük olmalıdır."
            )

        if oturum_suresi_dakika <= 0:
            raise ValueError(
                "Oturum süresi sıfırdan büyük olmalıdır."
            )

        self.guvenlik = guvenlik
        self._saat = saat or (
            lambda: datetime.now(UTC)
        )

        self.canlilik_zaman_asimi = timedelta(
            seconds=canlilik_zaman_asimi_saniye
        )

        self.oturum_suresi = timedelta(
            minutes=oturum_suresi_dakika
        )

        self._oturumlar: dict[
            str,
            CihazOturumu,
        ] = {}

        self._cihaz_oturumlari: dict[
            str,
            str,
        ] = {}

        self._mesajlar: dict[
            str,
            CihazMesaji,
        ] = {}

        self._kilit = RLock()

    def oturum_ac(
        self,
        *,
        cihaz_kimligi: str,
        cihaz_parmak_izi: str,
        gizli_anahtar: str,
        veri: dict[str, Any] | None = None,
    ) -> CihazOturumu:
        self.guvenlik.cihaz_dogrula(
            cihaz_kimligi=cihaz_kimligi,
            cihaz_parmak_izi=(
                cihaz_parmak_izi
            ),
            gizli_anahtar=gizli_anahtar,
        )

        mevcut = self.aktif_oturum_bul(
            cihaz_kimligi
        )

        if mevcut is not None:
            raise CihazOturumuHatasi(
                "Cihazın zaten etkin bir oturumu var."
            )

        simdi = self._saat()

        oturum = CihazOturumu(
            oturum_kimligi=(
                "SYK-CIHAZ-OTURUM-"
                + uuid4().hex.upper()
            ),
            cihaz_kimligi=cihaz_kimligi,
            baslama_zamani=simdi,
            durum=OturumDurumu.BAGLI,
            son_canlilik_zamani=simdi,
            son_mesaj_zamani=simdi,
            veri=dict(veri or {}),
        )

        with self._kilit:
            self._oturumlar[
                oturum.oturum_kimligi
            ] = oturum

            self._cihaz_oturumlari[
                cihaz_kimligi
            ] = oturum.oturum_kimligi

        return oturum

    def oturum_getir(
        self,
        oturum_kimligi: str,
    ) -> CihazOturumu:
        try:
            return self._oturumlar[
                oturum_kimligi
            ]
        except KeyError as hata:
            raise CihazOturumuHatasi(
                f"Oturum bulunamadı: {oturum_kimligi}"
            ) from hata

    def aktif_oturum_bul(
        self,
        cihaz_kimligi: str,
    ) -> CihazOturumu | None:
        oturum_kimligi = (
            self._cihaz_oturumlari.get(
                cihaz_kimligi
            )
        )

        if oturum_kimligi is None:
            return None

        oturum = self._oturumlar.get(
            oturum_kimligi
        )

        if (
            oturum is None
            or oturum.sona_erdi_mi
        ):
            return None

        return oturum

    def canlilik_bildir(
        self,
        oturum_kimligi: str,
    ) -> CihazOturumu:
        oturum = self.oturum_getir(
            oturum_kimligi
        )

        if oturum.sona_erdi_mi:
            raise CihazOturumuHatasi(
                "Sona ermiş oturuma canlılık bildirilemez."
            )

        simdi = self._saat()

        if oturum.durum in {
            OturumDurumu.CEVRIMDISI,
            OturumDurumu.BEKLIYOR,
        }:
            oturum.yeniden_baglanma_sayisi += 1

        oturum.durum = OturumDurumu.BAGLI
        oturum.son_canlilik_zamani = simdi
        oturum.son_mesaj_zamani = simdi
        oturum.son_hata = None

        return oturum

    def mesaj_olustur(
        self,
        *,
        oturum_kimligi: str,
        hedef_cihaz_kimligi: str,
        mesaj_turu: MesajTuru,
        icerik: dict[str, Any] | None = None,
    ) -> CihazMesaji:
        oturum = self.oturum_getir(
            oturum_kimligi
        )

        if not oturum.bagli_mi:
            raise CihazOturumuHatasi(
                "Mesaj göndermek için oturum bağlı olmalıdır."
            )

        self.guvenlik.cihaz_getir(
            hedef_cihaz_kimligi
        )

        mesaj = CihazMesaji.olustur(
            kaynak_cihaz_kimligi=(
                oturum.cihaz_kimligi
            ),
            hedef_cihaz_kimligi=(
                hedef_cihaz_kimligi
            ),
            mesaj_turu=mesaj_turu,
            sira_numarasi=(
                oturum.sonraki_sira_numarasi()
            ),
            icerik=dict(icerik or {}),
            oturum_kimligi=(
                oturum.oturum_kimligi
            ),
            olusturulma_zamani=(
                self._saat()
            ),
        )

        anahtar = self.guvenlik.anahtar_getir(
            oturum.cihaz_kimligi
        )

        mesaj.imzala(
            anahtar
        )

        self._mesajlar[
            mesaj.mesaj_kimligi
        ] = mesaj

        oturum.gonderilen_mesaj_sayisi += 1
        oturum.son_mesaj_zamani = (
            self._saat()
        )

        return mesaj

    def mesaj_al(
        self,
        mesaj: CihazMesaji,
    ) -> CihazMesaji:
        dogrulanan = (
            self.guvenlik.mesaji_dogrula(
                mesaj
            )
        )

        oturum = self.oturum_getir(
            mesaj.oturum_kimligi or ""
        )

        if (
            dogrulanan.durum
            is MesajDurumu.REDDEDILDI
        ):
            oturum.reddedilen_mesaj_sayisi += 1
            return dogrulanan

        dogrulanan.durum = (
            MesajDurumu.ALINDI
        )

        oturum.alinan_mesaj_sayisi += 1
        oturum.son_mesaj_zamani = (
            self._saat()
        )

        self._mesajlar[
            mesaj.mesaj_kimligi
        ] = mesaj

        return dogrulanan

    def zaman_asimlarini_kontrol_et(
        self,
    ) -> tuple[CihazOturumu, ...]:
        simdi = self._saat()

        degisenler: list[
            CihazOturumu
        ] = []

        for oturum in self._oturumlar.values():
            if oturum.sona_erdi_mi:
                continue

            if (
                simdi - oturum.baslama_zamani
                >= self.oturum_suresi
            ):
                self.oturumu_sonlandir(
                    oturum.oturum_kimligi,
                    gerekce=(
                        "Oturum süresi tamamlandı."
                    ),
                )

                degisenler.append(
                    oturum
                )
                continue

            son_canlilik = (
                oturum.son_canlilik_zamani
                or oturum.baslama_zamani
            )

            if (
                simdi - son_canlilik
                >= self.canlilik_zaman_asimi
            ):
                oturum.durum = (
                    OturumDurumu.CEVRIMDISI
                )

                oturum.son_hata = (
                    "Canlılık bildirimi zaman aşımına uğradı."
                )

                degisenler.append(
                    oturum
                )

        return tuple(
            degisenler
        )

    def oturumu_sonlandir(
        self,
        oturum_kimligi: str,
        *,
        gerekce: str,
    ) -> CihazOturumu:
        oturum = self.oturum_getir(
            oturum_kimligi
        )

        if oturum.sona_erdi_mi:
            return oturum

        oturum.durum = (
            OturumDurumu.SONA_ERDI
        )

        oturum.sona_erme_zamani = (
            self._saat()
        )

        oturum.son_hata = gerekce

        self._cihaz_oturumlari.pop(
            oturum.cihaz_kimligi,
            None,
        )

        return oturum

    def oturumlari_listele(
        self,
    ) -> tuple[CihazOturumu, ...]:
        return tuple(
            self._oturumlar[kimlik]
            for kimlik in sorted(
                self._oturumlar
            )
        )

    def mesajlari_listele(
        self,
    ) -> tuple[CihazMesaji, ...]:
        return tuple(
            self._mesajlar[kimlik]
            for kimlik in sorted(
                self._mesajlar
            )
        )

    def durum_ozeti(
        self,
    ) -> dict[str, Any]:
        oturumlar = self.oturumlari_listele()
        mesajlar = self.mesajlari_listele()

        return {
            "toplam_oturum_sayısı": len(
                oturumlar
            ),
            "bağlı_oturum_sayısı": sum(
                1
                for oturum in oturumlar
                if oturum.bagli_mi
            ),
            "çevrimdışı_oturum_sayısı": sum(
                1
                for oturum in oturumlar
                if oturum.durum
                is OturumDurumu.CEVRIMDISI
            ),
            "sona_eren_oturum_sayısı": sum(
                1
                for oturum in oturumlar
                if oturum.sona_erdi_mi
            ),
            "toplam_mesaj_sayısı": len(
                mesajlar
            ),
            "oturumlar": [
                oturum.sozluk()
                for oturum in oturumlar
            ],
            "mesajlar": [
                mesaj.sozluk()
                for mesaj in mesajlar
            ],
        }
