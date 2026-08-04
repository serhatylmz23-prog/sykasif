"""SyKaşif çalışma terminali güvenli oturum yöneticisi."""

from __future__ import annotations

import hashlib
import hmac
import json
from datetime import UTC, datetime, timedelta
from secrets import token_hex
from threading import RLock
from typing import Any, Callable
from uuid import uuid4

from syk_core.runtime_kernel import (
    RuntimeEvent,
    RuntimeEventBus,
)

from .modeller import (
    CihazDurumu,
    TerminalHatasi,
)
from .oturum_modelleri import (
    MesajDurumu,
    MesajTuru,
    OturumDurumu,
    OturumHatasi,
    TerminalMesaji,
    TerminalOturumu,
)
from .terminal import CalismaTerminali


MesajIsleyici = Callable[
    [TerminalMesaji],
    dict[str, Any] | None,
]


class TerminalOturumYoneticisi:
    """Yetkili cihazlar arasındaki imzalı oturumları yönetir."""

    def __init__(
        self,
        terminal: CalismaTerminali,
        *,
        olay_hatti: RuntimeEventBus | None = None,
        saat: Callable[[], datetime] | None = None,
        canlilik_zaman_asimi_saniye: int = 30,
        oturum_suresi_dakika: int = 480,
        mesaj_gecerlilik_saniye: int = 60,
    ) -> None:
        if canlilik_zaman_asimi_saniye <= 0:
            raise ValueError(
                "Canlılık zaman aşımı sıfırdan büyük olmalıdır."
            )

        if oturum_suresi_dakika <= 0:
            raise ValueError(
                "Oturum süresi sıfırdan büyük olmalıdır."
            )

        if mesaj_gecerlilik_saniye <= 0:
            raise ValueError(
                "Mesaj geçerlilik süresi sıfırdan büyük olmalıdır."
            )

        self.terminal = terminal
        self.olay_hatti = (
            olay_hatti
            or terminal.olay_hatti
        )
        self._saat = saat or (
            lambda: datetime.now(UTC)
        )

        self.canlilik_zaman_asimi = timedelta(
            seconds=canlilik_zaman_asimi_saniye
        )
        self.oturum_suresi = timedelta(
            minutes=oturum_suresi_dakika
        )
        self.mesaj_gecerlilik_suresi = timedelta(
            seconds=mesaj_gecerlilik_saniye
        )

        self._oturumlar: dict[
            str,
            TerminalOturumu,
        ] = {}

        self._cihaz_oturumlari: dict[
            str,
            str,
        ] = {}

        self._mesajlar: dict[
            str,
            TerminalMesaji,
        ] = {}

        self._islenmis_mesajlar: set[
            str
        ] = set()

        self._son_sira_numaralari: dict[
            str,
            int,
        ] = {}

        self._mesaj_isleyicileri: dict[
            MesajTuru,
            MesajIsleyici,
        ] = {}

        self._kilit = RLock()

    def oturum_ac(
        self,
        *,
        cihaz_kimligi: str,
        cihaz_parmak_izi: str,
        oturum_kimligi: str | None = None,
        oturum_anahtari: str | None = None,
        veri: dict[str, Any] | None = None,
    ) -> TerminalOturumu:
        cihaz = self.terminal.cihaz_getir(
            cihaz_kimligi
        )

        if cihaz.engelli_mi:
            raise OturumHatasi(
                "Engelli cihaz için oturum açılamaz."
            )

        if (
            cihaz.tanim.cihaz_parmak_izi
            != cihaz_parmak_izi
        ):
            cihaz.durum = CihazDurumu.HATA
            cihaz.son_hata = (
                "Oturum açılışında cihaz kimliği doğrulanamadı."
            )

            self._olay_yayinla(
                konu=(
                    "terminal.oturum."
                    "kimlik_dogrulama_hatasi"
                ),
                icerik={
                    "cihaz_kimliği": cihaz_kimligi,
                },
            )

            raise OturumHatasi(
                "Cihaz kimliği doğrulanamadı."
            )

        mevcut_oturum = self.aktif_oturumu_bul(
            cihaz_kimligi
        )

        if mevcut_oturum is not None:
            raise OturumHatasi(
                "Cihazın zaten etkin bir oturumu var."
            )

        kimlik = (
            oturum_kimligi
            or "SYK-OTURUM-"
            + uuid4().hex.upper()
        )

        if kimlik in self._oturumlar:
            raise OturumHatasi(
                f"Oturum kimliği zaten kayıtlı: {kimlik}"
            )

        anahtar = (
            oturum_anahtari
            or token_hex(32)
        )

        simdi = self._saat()

        oturum = TerminalOturumu(
            oturum_kimligi=kimlik,
            cihaz_kimligi=cihaz_kimligi,
            oturum_anahtari=anahtar,
            olusturulma_zamani=simdi,
            durum=OturumDurumu.BAGLI,
            baglanti_zamani=simdi,
            son_canlilik_zamani=simdi,
            son_mesaj_zamani=simdi,
            veri=dict(veri or {}),
        )

        with self._kilit:
            self._oturumlar[kimlik] = oturum
            self._cihaz_oturumlari[
                cihaz_kimligi
            ] = kimlik
            self._son_sira_numaralari[
                kimlik
            ] = 0

        if not cihaz.bagli_mi:
            self.terminal.cihaz_bagla(
                cihaz_kimligi,
                cihaz_parmak_izi=(
                    cihaz_parmak_izi
                ),
            )

        self._olay_yayinla(
            konu="terminal.oturum.acildi",
            icerik={
                "oturum_kimliği": kimlik,
                "cihaz_kimliği": cihaz_kimligi,
            },
        )

        return oturum

    def oturum_getir(
        self,
        oturum_kimligi: str,
    ) -> TerminalOturumu:
        try:
            return self._oturumlar[
                oturum_kimligi
            ]
        except KeyError as hata:
            raise OturumHatasi(
                f"Oturum bulunamadı: {oturum_kimligi}"
            ) from hata

    def aktif_oturumu_bul(
        self,
        cihaz_kimligi: str,
    ) -> TerminalOturumu | None:
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

    def oturumlari_listele(
        self,
    ) -> tuple[TerminalOturumu, ...]:
        return tuple(
            self._oturumlar[kimlik]
            for kimlik in sorted(
                self._oturumlar
            )
        )

    def canlilik_bildir(
        self,
        oturum_kimligi: str,
    ) -> TerminalOturumu:
        oturum = self._etkin_oturumu_dogrula(
            oturum_kimligi
        )

        simdi = self._saat()

        oturum.son_canlilik_zamani = simdi
        oturum.son_mesaj_zamani = simdi
        oturum.son_hata = None

        if oturum.durum in {
            OturumDurumu.BEKLEMEDE,
            OturumDurumu.CEVRIMDISI,
        }:
            oturum.durum = OturumDurumu.BAGLI
            oturum.yeniden_baglanma_sayisi += 1

            cihaz = self.terminal.cihaz_getir(
                oturum.cihaz_kimligi
            )

            if not cihaz.bagli_mi:
                self.terminal.cihaz_bagla(
                    oturum.cihaz_kimligi,
                    cihaz_parmak_izi=(
                        cihaz.tanim.cihaz_parmak_izi
                    ),
                )

            self._olay_yayinla(
                konu=(
                    "terminal.oturum."
                    "yeniden_baglandi"
                ),
                icerik={
                    "oturum_kimliği": (
                        oturum.oturum_kimligi
                    ),
                    "cihaz_kimliği": (
                        oturum.cihaz_kimligi
                    ),
                    "yeniden_bağlanma_sayısı": (
                        oturum.yeniden_baglanma_sayisi
                    ),
                },
            )
        else:
            self._olay_yayinla(
                konu="terminal.oturum.canlilik",
                icerik={
                    "oturum_kimliği": (
                        oturum.oturum_kimligi
                    ),
                    "cihaz_kimliği": (
                        oturum.cihaz_kimligi
                    ),
                },
            )

        return oturum

    def zaman_asimlarini_kontrol_et(
        self,
    ) -> tuple[TerminalOturumu, ...]:
        simdi = self._saat()

        degisenler: list[
            TerminalOturumu
        ] = []

        for oturum in self._oturumlar.values():
            if oturum.sona_erdi_mi:
                continue

            if (
                simdi
                - oturum.olusturulma_zamani
                >= self.oturum_suresi
            ):
                self.oturumu_sonlandir(
                    oturum.oturum_kimligi,
                    gerekce=(
                        "Oturum süresi tamamlandı."
                    ),
                )
                degisenler.append(oturum)
                continue

            son_canlilik = (
                oturum.son_canlilik_zamani
                or oturum.baglanti_zamani
                or oturum.olusturulma_zamani
            )

            gecen_sure = (
                simdi - son_canlilik
            )

            if (
                gecen_sure
                >= self.canlilik_zaman_asimi
                and oturum.durum
                is OturumDurumu.BAGLI
            ):
                oturum.durum = (
                    OturumDurumu.CEVRIMDISI
                )
                oturum.ayrilma_zamani = simdi
                oturum.son_hata = (
                    "Canlılık bildirimi alınamadı."
                )

                cihaz = self.terminal.cihaz_getir(
                    oturum.cihaz_kimligi
                )

                if cihaz.bagli_mi:
                    self.terminal.cihaz_ayir(
                        oturum.cihaz_kimligi,
                        aciklama=(
                            "Canlılık bildirimi "
                            "zaman aşımına uğradı."
                        ),
                    )

                self._olay_yayinla(
                    konu=(
                        "terminal.oturum."
                        "zaman_asimi"
                    ),
                    icerik={
                        "oturum_kimliği": (
                            oturum.oturum_kimligi
                        ),
                        "cihaz_kimliği": (
                            oturum.cihaz_kimligi
                        ),
                    },
                )

                degisenler.append(oturum)

        return tuple(degisenler)

    def oturumu_sonlandir(
        self,
        oturum_kimligi: str,
        *,
        gerekce: str,
    ) -> TerminalOturumu:
        oturum = self.oturum_getir(
            oturum_kimligi
        )

        if oturum.sona_erdi_mi:
            return oturum

        simdi = self._saat()

        oturum.durum = (
            OturumDurumu.SONA_ERDI
        )
        oturum.sona_erme_zamani = simdi
        oturum.ayrilma_zamani = simdi
        oturum.son_hata = gerekce

        self._cihaz_oturumlari.pop(
            oturum.cihaz_kimligi,
            None,
        )

        cihaz = self.terminal.cihaz_getir(
            oturum.cihaz_kimligi
        )

        if cihaz.bagli_mi:
            self.terminal.cihaz_ayir(
                oturum.cihaz_kimligi,
                aciklama=gerekce,
            )

        self._olay_yayinla(
            konu="terminal.oturum.sonlandirildi",
            icerik={
                "oturum_kimliği": oturum_kimligi,
                "cihaz_kimliği": (
                    oturum.cihaz_kimligi
                ),
                "gerekçe": gerekce,
            },
        )

        return oturum

    def mesaj_isleyici_kaydet(
        self,
        mesaj_turu: MesajTuru,
        isleyici: MesajIsleyici,
    ) -> None:
        if not callable(isleyici):
            raise TypeError(
                "Mesaj işleyici çağrılabilir olmalıdır."
            )

        self._mesaj_isleyicileri[
            mesaj_turu
        ] = isleyici

    def mesaj_olustur(
        self,
        *,
        oturum_kimligi: str,
        hedef_cihaz_kimligi: str,
        mesaj_turu: MesajTuru,
        icerik: dict[str, Any] | None = None,
        mesaj_kimligi: str | None = None,
    ) -> TerminalMesaji:
        oturum = self._etkin_oturumu_dogrula(
            oturum_kimligi
        )

        self.terminal.cihaz_getir(
            hedef_cihaz_kimligi
        )

        sira_numarasi = (
            self._son_sira_numaralari[
                oturum_kimligi
            ]
            + 1
        )

        kimlik = (
            mesaj_kimligi
            or "SYK-MESAJ-"
            + uuid4().hex.upper()
        )

        if kimlik in self._mesajlar:
            raise OturumHatasi(
                f"Mesaj kimliği zaten kayıtlı: {kimlik}"
            )

        mesaj = TerminalMesaji(
            mesaj_kimligi=kimlik,
            oturum_kimligi=oturum_kimligi,
            kaynak_cihaz_kimligi=(
                oturum.cihaz_kimligi
            ),
            hedef_cihaz_kimligi=(
                hedef_cihaz_kimligi
            ),
            mesaj_turu=mesaj_turu,
            sira_numarasi=sira_numarasi,
            olusturulma_zamani=self._saat(),
            icerik=dict(icerik or {}),
        )

        mesaj.imza = self._mesaji_imzala(
            mesaj,
            oturum.oturum_anahtari,
        )
        mesaj.durum = MesajDurumu.IMZALANDI

        with self._kilit:
            self._mesajlar[kimlik] = mesaj
            self._son_sira_numaralari[
                oturum_kimligi
            ] = sira_numarasi

        self._olay_yayinla(
            konu="terminal.mesaj.olusturuldu",
            icerik={
                "mesaj_kimliği": kimlik,
                "oturum_kimliği": oturum_kimligi,
                "mesaj_türü": mesaj_turu.value,
                "sıra_numarası": sira_numarasi,
            },
        )

        return mesaj

    def mesaji_gonder(
        self,
        mesaj_kimligi: str,
    ) -> TerminalMesaji:
        mesaj = self.mesaj_getir(
            mesaj_kimligi
        )

        oturum = self._etkin_oturumu_dogrula(
            mesaj.oturum_kimligi
        )

        if mesaj.durum not in {
            MesajDurumu.IMZALANDI,
            MesajDurumu.OLUSTURULDU,
        }:
            raise OturumHatasi(
                "Mesaj gönderilebilir durumda değil."
            )

        simdi = self._saat()

        mesaj.durum = MesajDurumu.GONDERILDI
        mesaj.gonderilme_zamani = simdi

        oturum.gonderilen_mesaj_sayisi += 1
        oturum.son_mesaj_zamani = simdi

        self._olay_yayinla(
            konu="terminal.mesaj.gonderildi",
            icerik={
                "mesaj_kimliği": mesaj_kimligi,
                "kaynak_cihaz_kimliği": (
                    mesaj.kaynak_cihaz_kimligi
                ),
                "hedef_cihaz_kimliği": (
                    mesaj.hedef_cihaz_kimligi
                ),
            },
        )

        return mesaj

    def mesaji_al(
        self,
        mesaj: TerminalMesaji,
    ) -> TerminalMesaji:
        oturum = self._etkin_oturumu_dogrula(
            mesaj.oturum_kimligi
        )

        simdi = self._saat()

        if (
            mesaj.mesaj_kimligi
            in self._islenmis_mesajlar
        ):
            oturum.reddedilen_mesaj_sayisi += 1
            mesaj.durum = MesajDurumu.REDDEDILDI
            mesaj.hata = (
                "Aynı mesaj yeniden gönderildi."
            )

            self._olay_yayinla(
                konu=(
                    "terminal.mesaj."
                    "tekrar_reddedildi"
                ),
                icerik={
                    "mesaj_kimliği": (
                        mesaj.mesaj_kimligi
                    ),
                },
            )

            return mesaj

        gecen_sure = (
            simdi - mesaj.olusturulma_zamani
        )

        if gecen_sure > self.mesaj_gecerlilik_suresi:
            oturum.reddedilen_mesaj_sayisi += 1
            mesaj.durum = MesajDurumu.REDDEDILDI
            mesaj.hata = (
                "Mesaj geçerlilik süresini aştı."
            )

            self._olay_yayinla(
                konu=(
                    "terminal.mesaj."
                    "suresi_gecmis"
                ),
                icerik={
                    "mesaj_kimliği": (
                        mesaj.mesaj_kimligi
                    ),
                },
            )

            return mesaj

        beklenen_imza = self._mesaji_imzala(
            mesaj,
            oturum.oturum_anahtari,
        )

        if (
            mesaj.imza is None
            or not hmac.compare_digest(
                mesaj.imza,
                beklenen_imza,
            )
        ):
            oturum.reddedilen_mesaj_sayisi += 1
            mesaj.durum = MesajDurumu.REDDEDILDI
            mesaj.hata = (
                "Mesaj imzası doğrulanamadı."
            )

            self._olay_yayinla(
                konu=(
                    "terminal.mesaj."
                    "imza_hatasi"
                ),
                icerik={
                    "mesaj_kimliği": (
                        mesaj.mesaj_kimligi
                    ),
                },
            )

            return mesaj

        mesaj.durum = MesajDurumu.DOGRULANDI
        mesaj.alinma_zamani = simdi
        mesaj.dogrulanma_zamani = simdi

        oturum.alinan_mesaj_sayisi += 1
        oturum.son_mesaj_zamani = simdi

        self._islenmis_mesajlar.add(
            mesaj.mesaj_kimligi
        )

        self._olay_yayinla(
            konu="terminal.mesaj.dogrulandi",
            icerik={
                "mesaj_kimliği": (
                    mesaj.mesaj_kimligi
                ),
                "mesaj_türü": (
                    mesaj.mesaj_turu.value
                ),
            },
        )

        isleyici = self._mesaj_isleyicileri.get(
            mesaj.mesaj_turu
        )

        if isleyici is None:
            mesaj.durum = MesajDurumu.ISLENDI
            mesaj.islenme_zamani = simdi
            return mesaj

        try:
            sonuc = isleyici(mesaj)

            if sonuc:
                mesaj.icerik[
                    "işleme_sonucu"
                ] = dict(sonuc)

            mesaj.durum = MesajDurumu.ISLENDI
            mesaj.islenme_zamani = (
                self._saat()
            )

            self._olay_yayinla(
                konu="terminal.mesaj.islendi",
                icerik={
                    "mesaj_kimliği": (
                        mesaj.mesaj_kimligi
                    ),
                },
            )

            return mesaj

        except Exception as hata:
            mesaj.durum = MesajDurumu.HATA
            mesaj.hata = str(hata)
            mesaj.islenme_zamani = (
                self._saat()
            )

            self._olay_yayinla(
                konu="terminal.mesaj.hata",
                icerik={
                    "mesaj_kimliği": (
                        mesaj.mesaj_kimligi
                    ),
                    "hata": str(hata),
                },
            )

            return mesaj

    def mesaj_getir(
        self,
        mesaj_kimligi: str,
    ) -> TerminalMesaji:
        try:
            return self._mesajlar[
                mesaj_kimligi
            ]
        except KeyError as hata:
            raise OturumHatasi(
                f"Mesaj bulunamadı: {mesaj_kimligi}"
            ) from hata

    def mesajlari_listele(
        self,
    ) -> tuple[TerminalMesaji, ...]:
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
            "işlenen_mesaj_sayısı": sum(
                1
                for mesaj in mesajlar
                if mesaj.durum
                is MesajDurumu.ISLENDI
            ),
            "reddedilen_mesaj_sayısı": sum(
                1
                for mesaj in mesajlar
                if mesaj.durum
                is MesajDurumu.REDDEDILDI
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

    def _etkin_oturumu_dogrula(
        self,
        oturum_kimligi: str,
    ) -> TerminalOturumu:
        oturum = self.oturum_getir(
            oturum_kimligi
        )

        if oturum.sona_erdi_mi:
            raise OturumHatasi(
                "Sona ermiş oturum kullanılamaz."
            )

        if oturum.durum not in {
            OturumDurumu.BAGLI,
            OturumDurumu.BEKLEMEDE,
            OturumDurumu.CEVRIMDISI,
        }:
            raise OturumHatasi(
                "Oturum kullanıma hazır değil."
            )

        return oturum

    def _mesaji_imzala(
        self,
        mesaj: TerminalMesaji,
        oturum_anahtari: str,
    ) -> str:
        imza_icerigi = {
            "mesaj_kimliği": (
                mesaj.mesaj_kimligi
            ),
            "oturum_kimliği": (
                mesaj.oturum_kimligi
            ),
            "kaynak_cihaz_kimliği": (
                mesaj.kaynak_cihaz_kimligi
            ),
            "hedef_cihaz_kimliği": (
                mesaj.hedef_cihaz_kimligi
            ),
            "mesaj_türü": (
                mesaj.mesaj_turu.value
            ),
            "sıra_numarası": (
                mesaj.sira_numarasi
            ),
            "oluşturulma_zamanı": (
                mesaj.olusturulma_zamani.isoformat()
            ),
            "içerik": mesaj.icerik,
        }

        ham = json.dumps(
            imza_icerigi,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")

        return hmac.new(
            oturum_anahtari.encode("utf-8"),
            ham,
            hashlib.sha256,
        ).hexdigest()

    def _olay_yayinla(
        self,
        *,
        konu: str,
        icerik: dict[str, Any],
    ) -> None:
        self.olay_hatti.publish(
            RuntimeEvent(
                topic=konu,
                source=(
                    "terminal_oturum_yoneticisi"
                ),
                payload=icerik,
            )
        )
