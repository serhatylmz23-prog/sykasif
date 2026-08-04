from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from hashlib import sha256
import json
from typing import Any, Callable
from urllib.request import Request, urlopen
from xml.etree import ElementTree

from .capraz_dogrulama import (
    KaynakGuvenProfili,
    KaynakliPiyasaVerisi,
    KaynakTuru,
)
from .gercek_kaynak_sozlesmeleri import (
    DovizKaydi,
    FinansKaynakSinifi,
    PiyasaKaynakBagdastiricisi,
)
from .modeller import (
    VarlikTuru,
    VeriAkisDurumu,
)
from .veri_saglayicilari import (
    PiyasaVerisi,
    VeriDogruLamaMotoru,
)


def _ondalik(
    deger: str | Decimal | int | float,
) -> Decimal:
    metin = str(deger).strip().replace(
        ",",
        ".",
    )

    if not metin:
        raise ValueError(
            "Döviz değeri boş olamaz."
        )

    return Decimal(
        metin
    ).quantize(
        Decimal("0.0001")
    )


def _zaman() -> str:
    return datetime.now(
        UTC
    ).isoformat()


@dataclass(frozen=True, slots=True)
class TcmbDovizSonucu:
    kayitlar: tuple[DovizKaydi, ...]
    veri_tarihi: str
    kaynak: str
    yanit_sha256: str

    def sembol_getir(
        self,
        sembol: str,
    ) -> DovizKaydi:
        aranan = str(
            sembol
        ).strip().upper()

        for kayit in self.kayitlar:
            if kayit.kod == aranan:
                return kayit

        raise KeyError(
            f"TCMB döviz kaydı bulunamadı: {aranan}"
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "veri_tarihi": self.veri_tarihi,
            "kaynak": self.kaynak,
            "kayitlar": [
                kayit.as_dict()
                for kayit in self.kayitlar
            ],
            "yanit_sha256": (
                self.yanit_sha256
            ),
        }


class TcmbXmlCozumleyici:
    @classmethod
    def coz(
        cls,
        xml_verisi: bytes | str,
        *,
        istek_zamani: str | None = None,
    ) -> TcmbDovizSonucu:
        if isinstance(
            xml_verisi,
            bytes,
        ):
            ham = xml_verisi
        else:
            ham = str(
                xml_verisi
            ).encode("utf-8")

        try:
            kok = ElementTree.fromstring(
                ham
            )
        except ElementTree.ParseError as error:
            raise ValueError(
                "TCMB XML yanıtı çözülemedi."
            ) from error

        tarih = (
            kok.attrib.get("Date")
            or kok.attrib.get("Tarih")
            or istek_zamani
            or _zaman()
        )

        zaman_damgasi = (
            istek_zamani
            or _zaman()
        )

        kayitlar: list[
            DovizKaydi
        ] = []

        for para in kok.findall(
            ".//Currency"
        ):
            kod = (
                para.attrib.get(
                    "CurrencyCode"
                )
                or para.attrib.get(
                    "Kod"
                )
                or ""
            ).strip().upper()

            if not kod:
                continue

            alis_metni = (
                para.findtext(
                    "ForexBuying"
                )
                or para.findtext(
                    "BanknoteBuying"
                )
                or ""
            ).strip()

            satis_metni = (
                para.findtext(
                    "ForexSelling"
                )
                or para.findtext(
                    "BanknoteSelling"
                )
                or ""
            ).strip()

            if (
                not alis_metni
                or not satis_metni
            ):
                continue

            birim_metni = (
                para.findtext("Unit")
                or "1"
            ).strip()

            birim = Decimal(
                birim_metni
            )

            if birim <= 0:
                continue

            alis = (
                _ondalik(
                    alis_metni
                )
                / birim
            ).quantize(
                Decimal("0.0001")
            )

            satis = (
                _ondalik(
                    satis_metni
                )
                / birim
            ).quantize(
                Decimal("0.0001")
            )

            kayitlar.append(
                DovizKaydi(
                    kod=f"{kod}TRY",
                    alis_fiyati=alis,
                    satis_fiyati=satis,
                    zaman_damgasi=(
                        zaman_damgasi
                    ),
                    kaynak_turu=(
                        "TCMB gösterge kuru"
                    ),
                    para_birimi="TRY",
                )
            )

        if not kayitlar:
            raise ValueError(
                "TCMB yanıtında kullanılabilir "
                "döviz kaydı bulunamadı."
            )

        kayitlar = sorted(
            kayitlar,
            key=lambda kayit: kayit.kod,
        )

        kanit = {
            "veri_tarihi": tarih,
            "kayitlar": [
                kayit.as_dict()
                for kayit in kayitlar
            ],
            "kaynak": "TCMB",
        }

        kodlu = json.dumps(
            kanit,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")

        return TcmbDovizSonucu(
            kayitlar=tuple(
                kayitlar
            ),
            veri_tarihi=str(
                tarih
            ),
            kaynak="TCMB",
            yanit_sha256=sha256(
                kodlu
            ).hexdigest(),
        )


class TcmbDovizBagdastiricisi(
    PiyasaKaynakBagdastiricisi
):
    SAGLAYICI_ID = "tcmb-doviz"

    def __init__(
        self,
        *,
        adres: str = (
            "https://www.tcmb.gov.tr/"
            "kurlar/today.xml"
        ),
        zaman_asimi_saniyesi: float = 10.0,
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

        self.tasiyici = (
            tasiyici
            or self._gercek_tasiyici
        )

        self._son_sonuc: (
            TcmbDovizSonucu | None
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
            kesinti_dayanim_puani=85,
            lisansli=True,
            resmi=True,
            aciklama=(
                "TCMB tarafından yayımlanan "
                "gösterge niteliğindeki kurlar."
            ),
        )

    def tum_kurlari_getir(
        self,
    ) -> TcmbDovizSonucu:
        ham = self.tasiyici(
            self.adres,
            self.zaman_asimi_saniyesi,
        )

        sonuc = TcmbXmlCozumleyici.coz(
            ham,
            istek_zamani=_zaman(),
        )

        self._son_sonuc = sonuc

        return sonuc

    def piyasa_verisi_getir(
        self,
        *,
        sembol: str,
    ) -> KaynakliPiyasaVerisi:
        sonuc = (
            self._son_sonuc
            or self.tum_kurlari_getir()
        )

        kayit = sonuc.sembol_getir(
            sembol
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
            veri_durumu=(
                VeriAkisDurumu.GECIKMELI
            ),
            gecikme_saniyesi=60,
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