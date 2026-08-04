from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable
from urllib.request import Request, urlopen

from .baglanti_calisma_katmani import (
    SonGuvenilirYanitDeposu,
    YanitKaynagi,
)
from .capraz_dogrulama import (
    KaynakGuvenProfili,
    KaynakliPiyasaVerisi,
    KaynakTuru,
)
from .gercek_kaynak_sozlesmeleri import (
    FinansKaynakSinifi,
    PiyasaKaynakBagdastiricisi,
)
from .modeller import (
    VarlikTuru,
    VeriAkisDurumu,
)
from .tcmb_doviz_bagdastiricisi import (
    TcmbDovizSonucu,
    TcmbXmlCozumleyici,
)
from .veri_saglayicilari import (
    PiyasaVerisi,
    VeriDogruLamaMotoru,
)


def _simdi() -> str:
    return datetime.now(
        UTC
    ).isoformat()


@dataclass(frozen=True, slots=True)
class TcmbGuvenliSonuc:
    sonuc: TcmbDovizSonucu
    yanit_kaynagi: YanitKaynagi
    cevrimdisi: bool
    hata: str | None
    kullanici_aciklamasi: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "sonuc": self.sonuc.as_dict(),
            "yanit_kaynagi": (
                self.yanit_kaynagi.value
            ),
            "cevrimdisi": self.cevrimdisi,
            "hata": self.hata,
            "kullanici_aciklamasi": (
                self.kullanici_aciklamasi
            ),
        }


class TcmbGuvenliBagdastiricisi(
    PiyasaKaynakBagdastiricisi
):
    SAGLAYICI_ID = "tcmb-doviz-guvenli"
    DEPO_ANAHTARI = "TCMB-TODAY-XML"

    def __init__(
        self,
        *,
        adres: str = (
            "https://www.tcmb.gov.tr/"
            "kurlar/today.xml"
        ),
        zaman_asimi_saniyesi: float = 15.0,
        depo: (
            SonGuvenilirYanitDeposu
            | None
        ) = None,
        depo_dosyasi: (
            str | Path | None
        ) = None,
        tasiyici: (
            Callable[
                [str, float],
                bytes,
            ]
            | None
        ) = None,
    ) -> None:
        self.adres = str(
            adres
        ).strip()

        self.zaman_asimi_saniyesi = float(
            zaman_asimi_saniyesi
        )

        if not self.adres:
            raise ValueError(
                "TCMB adresi boş olamaz."
            )

        if self.zaman_asimi_saniyesi <= 0:
            raise ValueError(
                "Zaman aşımı pozitif olmalıdır."
            )

        self.depo = (
            depo
            or SonGuvenilirYanitDeposu(
                dosya_yolu=depo_dosyasi
            )
        )

        self.tasiyici = (
            tasiyici
            or self._gercek_tasiyici
        )

        self._son_guvenli_sonuc: (
            TcmbGuvenliSonuc | None
        ) = None

    @staticmethod
    def _gercek_tasiyici(
        adres: str,
        zaman_asimi: float,
    ) -> bytes:
        istek = Request(
            adres,
            headers={
                "Accept": (
                    "application/xml,text/xml"
                ),
                "User-Agent": (
                    "SyFinansOtigi/1.0"
                ),
            },
            method="GET",
        )

        with urlopen(
            istek,
            timeout=zaman_asimi,
        ) as yanit:
            return yanit.read()

    @property
    def saglayici_id(self) -> str:
        return self.SAGLAYICI_ID

    @property
    def kaynak_sinifi(
        self,
    ) -> FinansKaynakSinifi:
        return FinansKaynakSinifi.DOVIZ

    @property
    def guven_profili(
        self,
    ) -> KaynakGuvenProfili:
        return KaynakGuvenProfili(
            saglayici_id=(
                self.saglayici_id
            ),
            kaynak_turu=(
                KaynakTuru.RESMI
            ),
            temel_guven_puani=96,
            guncellik_puani=85,
            gecmis_tutarlilik_puani=95,
            kesinti_dayanim_puani=92,
            lisansli=True,
            resmi=True,
            aciklama=(
                "TCMB gösterge kurları; "
                "canlı bağlantı kesilirse "
                "son güvenilir kayıt kullanılır."
            ),
        )

    def kurlari_getir(
        self,
    ) -> TcmbGuvenliSonuc:
        istek_zamani = _simdi()

        try:
            ham = self.tasiyici(
                self.adres,
                self.zaman_asimi_saniyesi,
            )

            sonuc = TcmbXmlCozumleyici.coz(
                ham,
                istek_zamani=istek_zamani,
            )

            self.depo.kaydet(
                anahtar=self.DEPO_ANAHTARI,
                veri={
                    "xml": ham.decode(
                        "utf-8"
                    ),
                    "kayit_zamani": (
                        istek_zamani
                    ),
                    "veri_tarihi": (
                        sonuc.veri_tarihi
                    ),
                },
            )

            guvenli = TcmbGuvenliSonuc(
                sonuc=sonuc,
                yanit_kaynagi=(
                    YanitKaynagi.CANLI
                ),
                cevrimdisi=False,
                hata=None,
                kullanici_aciklamasi=(
                    "TCMB verisi canlı "
                    "bağlantıdan alındı; "
                    "gösterge kuru niteliğindedir."
                ),
            )

        except Exception as error:
            if not self.depo.var_mi(
                anahtar=self.DEPO_ANAHTARI
            ):
                raise ConnectionError(
                    "TCMB canlı bağlantısı "
                    "kurulamadı ve son güvenilir "
                    "kayıt bulunamadı."
                ) from error

            onceki = self.depo.getir(
                anahtar=self.DEPO_ANAHTARI
            )

            sonuc = TcmbXmlCozumleyici.coz(
                onceki["xml"],
                istek_zamani=(
                    onceki.get(
                        "kayit_zamani"
                    )
                    or istek_zamani
                ),
            )

            guvenli = TcmbGuvenliSonuc(
                sonuc=sonuc,
                yanit_kaynagi=(
                    YanitKaynagi
                    .SON_GUVENILIR
                ),
                cevrimdisi=True,
                hata=str(error),
                kullanici_aciklamasi=(
                    "İnternet bağlantısı yok. "
                    "Son güvenilir TCMB kaydı "
                    "gösteriliyor. Veri tarihi: "
                    f"{sonuc.veri_tarihi}."
                ),
            )

        self._son_guvenli_sonuc = guvenli

        return guvenli

    def piyasa_verisi_getir(
        self,
        *,
        sembol: str,
    ) -> KaynakliPiyasaVerisi:
        guvenli = (
            self._son_guvenli_sonuc
            or self.kurlari_getir()
        )

        kayit = (
            guvenli.sonuc
            .sembol_getir(
                sembol
            )
        )

        veri_durumu = (
            VeriAkisDurumu.CEVRIMDISI
            if guvenli.cevrimdisi
            else VeriAkisDurumu.GECIKMELI
        )

        veri = PiyasaVerisi(
            sembol=kayit.kod,
            varlik_turu=(
                VarlikTuru.DOVIZ
            ),
            fiyat=kayit.orta_fiyat,
            para_birimi=(
                kayit.para_birimi
            ),
            zaman_damgasi=(
                kayit.zaman_damgasi
            ),
            kaynak=(
                "Türkiye Cumhuriyet "
                "Merkez Bankası"
            ),
            saglayici_id=(
                self.saglayici_id
            ),
            veri_durumu=veri_durumu,
            gecikme_saniyesi=(
                60
                if not guvenli.cevrimdisi
                else 0
            ),
            alis_fiyati=(
                kayit.alis_fiyati
            ),
            satis_fiyati=(
                kayit.satis_fiyati
            ),
            dogrulandi=True,
        )

        muhurlu = (
            VeriDogruLamaMotoru
            .muhurle(veri)
        )

        return KaynakliPiyasaVerisi(
            veri=muhurlu,
            guven_profili=(
                self.guven_profili
            ),
        )

    def son_durum(
        self,
    ) -> dict[str, Any]:
        if self._son_guvenli_sonuc is None:
            return {
                "durum": "veri_alinmadi",
                "cevrimdisi": False,
                "kullanici_aciklamasi": (
                    "Henüz TCMB verisi alınmadı."
                ),
            }

        return {
            "durum": (
                "cevrimdisi"
                if self._son_guvenli_sonuc
                .cevrimdisi
                else "canli"
            ),
            "cevrimdisi": (
                self._son_guvenli_sonuc
                .cevrimdisi
            ),
            "veri_tarihi": (
                self._son_guvenli_sonuc
                .sonuc
                .veri_tarihi
            ),
            "yanit_kaynagi": (
                self._son_guvenli_sonuc
                .yanit_kaynagi
                .value
            ),
            "kullanici_aciklamasi": (
                self._son_guvenli_sonuc
                .kullanici_aciklamasi
            ),
        }