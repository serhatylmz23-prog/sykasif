from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
import json
import os
from pathlib import Path
from typing import Any, Callable, Mapping
from urllib.parse import urlencode
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
    FonKaydi,
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


def _simdi() -> str:
    return datetime.now(
        UTC
    ).isoformat()


def _metin(
    kayit: Mapping[str, Any],
    *anahtarlar: str,
    varsayilan: str = "",
) -> str:
    for anahtar in anahtarlar:
        deger = kayit.get(
            anahtar
        )

        if deger is None:
            continue

        sonuc = str(
            deger
        ).strip()

        if sonuc:
            return sonuc

    return varsayilan


def _ondalik(
    deger: Any,
) -> Decimal:
    metin = str(
        deger
    ).strip()

    if not metin:
        raise ValueError(
            "Sayısal değer boş olamaz."
        )

    metin = (
        metin
        .replace(" ", "")
        .replace(",", ".")
    )

    return Decimal(
        metin
    ).quantize(
        Decimal("0.000000")
    )


def _istege_bagli_ondalik(
    deger: Any,
) -> Decimal | None:
    if deger in {
        None,
        "",
    }:
        return None

    return _ondalik(
        deger
    )


def _istege_bagli_tamsayi(
    deger: Any,
) -> int | None:
    if deger in {
        None,
        "",
    }:
        return None

    return int(
        Decimal(
            str(deger)
            .replace(" ", "")
            .replace(",", ".")
        )
    )


def _kayit_listesi(
    ham: Any,
) -> list[Mapping[str, Any]]:
    if isinstance(
        ham,
        list,
    ):
        return [
            kayit
            for kayit in ham
            if isinstance(
                kayit,
                Mapping,
            )
        ]

    if isinstance(
        ham,
        Mapping,
    ):
        for anahtar in (
            "data",
            "items",
            "results",
            "fonlar",
            "funds",
        ):
            aday = ham.get(
                anahtar
            )

            if isinstance(
                aday,
                list,
            ):
                return [
                    kayit
                    for kayit in aday
                    if isinstance(
                        kayit,
                        Mapping,
                    )
                ]

    raise ValueError(
        "Fon yanıtında kayıt listesi bulunamadı."
    )


def _dagilim_coz(
    kayit: Mapping[str, Any],
) -> dict[str, float]:
    ham = (
        kayit.get(
            "portfoy_dagilimi"
        )
        or kayit.get(
            "portfolio_distribution"
        )
        or kayit.get(
            "distribution"
        )
        or {}
    )

    if not isinstance(
        ham,
        Mapping,
    ):
        return {}

    sonuc: dict[str, float] = {}

    for anahtar, deger in ham.items():
        try:
            oran = float(
                str(deger)
                .replace(",", ".")
            )
        except (
            TypeError,
            ValueError,
        ):
            continue

        if oran < 0:
            continue

        sonuc[
            str(anahtar).strip()
        ] = oran

    return sonuc


@dataclass(frozen=True, slots=True)
class TefasGuvenliSonuc:
    fonlar: tuple[
        FonKaydi,
        ...
    ]
    yanit_kaynagi: YanitKaynagi
    cevrimdisi: bool
    hata: str | None
    veri_zamani: str
    kullanici_aciklamasi: str

    def fon_getir(
        self,
        fon_kodu: str,
    ) -> FonKaydi:
        aranan = str(
            fon_kodu
        ).strip().upper()

        for fon in self.fonlar:
            if (
                fon.fon_kodu
                .strip()
                .upper()
                == aranan
            ):
                return fon

        raise KeyError(
            "Fon kaydı bulunamadı: "
            f"{aranan}"
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "fonlar": [
                fon.as_dict()
                for fon in self.fonlar
            ],
            "fon_sayisi": len(
                self.fonlar
            ),
            "yanit_kaynagi": (
                self.yanit_kaynagi.value
            ),
            "cevrimdisi": (
                self.cevrimdisi
            ),
            "hata": self.hata,
            "veri_zamani": (
                self.veri_zamani
            ),
            "kullanici_aciklamasi": (
                self.kullanici_aciklamasi
            ),
        }


class TefasJsonCozumleyici:
    @classmethod
    def coz(
        cls,
        ham_yanit: (
            bytes
            | str
            | Mapping[str, Any]
            | list[Any]
        ),
        *,
        varsayilan_zaman: (
            str | None
        ) = None,
    ) -> tuple[
        FonKaydi,
        ...
    ]:
        if isinstance(
            ham_yanit,
            bytes,
        ):
            ham = json.loads(
                ham_yanit.decode(
                    "utf-8"
                )
            )

        elif isinstance(
            ham_yanit,
            str,
        ):
            ham = json.loads(
                ham_yanit
            )

        else:
            ham = ham_yanit

        kayitlar = _kayit_listesi(
            ham
        )

        fonlar: list[
            FonKaydi
        ] = []

        for kayit in kayitlar:
            fon_kodu = _metin(
                kayit,
                "fon_kodu",
                "fund_code",
                "code",
                "FONKODU",
                "FonKodu",
            ).upper()

            fon_adi = _metin(
                kayit,
                "fon_adi",
                "fund_name",
                "name",
                "FONUNVAN",
                "FonUnvan",
            )

            fiyat_metni = _metin(
                kayit,
                "birim_fiyat",
                "price",
                "unit_price",
                "FIYAT",
                "FonFiyat",
            )

            zaman_damgasi = _metin(
                kayit,
                "zaman_damgasi",
                "date",
                "record_date",
                "TARIH",
                "Tarih",
                varsayilan=(
                    varsayilan_zaman
                    or _simdi()
                ),
            )

            if not fon_kodu:
                continue

            if not fon_adi:
                continue

            if not fiyat_metni:
                continue

            toplam_deger = (
                kayit.get(
                    "toplam_deger"
                )
                or kayit.get(
                    "total_value"
                )
                or kayit.get(
                    "PORTFOYBUYUKLUK"
                )
            )

            yatirimci_sayisi = (
                kayit.get(
                    "yatirimci_sayisi"
                )
                or kayit.get(
                    "investor_count"
                )
                or kayit.get(
                    "KISISAYISI"
                )
            )

            fonlar.append(
                FonKaydi(
                    fon_kodu=fon_kodu,
                    fon_adi=fon_adi,
                    birim_fiyat=_ondalik(
                        fiyat_metni
                    ),
                    toplam_deger=(
                        _istege_bagli_ondalik(
                            toplam_deger
                        )
                    ),
                    yatirimci_sayisi=(
                        _istege_bagli_tamsayi(
                            yatirimci_sayisi
                        )
                    ),
                    portfoy_dagilimi=(
                        _dagilim_coz(
                            kayit
                        )
                    ),
                    zaman_damgasi=(
                        zaman_damgasi
                    ),
                    para_birimi="TRY",
                )
            )

        if not fonlar:
            raise ValueError(
                "Fon yanıtında kullanılabilir "
                "kayıt bulunamadı."
            )

        benzersiz = {
            fon.fon_kodu: fon
            for fon in fonlar
        }

        return tuple(
            sorted(
                benzersiz.values(),
                key=lambda fon: (
                    fon.fon_kodu
                ),
            )
        )


class TefasFonBagdastiricisi(
    PiyasaKaynakBagdastiricisi
):
    SAGLAYICI_ID = "tefas-fon"
    DEPO_ANAHTARI = "TEFAS-FON"

    def __init__(
        self,
        *,
        adres: str | None = None,
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
                [
                    str,
                    Mapping[str, str],
                    float,
                ],
                bytes,
            ]
            | None
        ) = None,
    ) -> None:
        self.adres = (
            adres
            or os.getenv(
                "SYFINANS_TEFAS_API_ADRESI",
                "",
            )
        ).strip()

        self.zaman_asimi_saniyesi = float(
            zaman_asimi_saniyesi
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

        self._son_sonuc: (
            TefasGuvenliSonuc | None
        ) = None

    @staticmethod
    def _gercek_tasiyici(
        adres: str,
        basliklar: Mapping[str, str],
        zaman_asimi: float,
    ) -> bytes:
        istek = Request(
            adres,
            headers=dict(
                basliklar
            ),
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
        return FinansKaynakSinifi.FON

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
            temel_guven_puani=94,
            guncellik_puani=82,
            gecmis_tutarlilik_puani=92,
            kesinti_dayanim_puani=80,
            lisansli=True,
            resmi=True,
            aciklama=(
                "Fon verileri resmî kaynak "
                "sözleşmesine göre işlenir; "
                "işlem fiyatı garantisi değildir."
            ),
        )

    def _adres_olustur(
        self,
        *,
        fon_kodu: str | None,
        limit: int,
    ) -> str:
        if not self.adres:
            raise RuntimeError(
                "TEFAS veri adresi tanımlanmadı. "
                "SYFINANS_TEFAS_API_ADRESI "
                "ortam değişkenini ayarlayın."
            )

        sorgu: dict[str, Any] = {
            "limit": max(
                1,
                min(
                    int(limit),
                    1000,
                ),
            )
        }

        if fon_kodu:
            sorgu["code"] = (
                fon_kodu
                .strip()
                .upper()
            )

        ayirici = (
            "&"
            if "?" in self.adres
            else "?"
        )

        return (
            self.adres
            + ayirici
            + urlencode(
                sorgu
            )
        )

    @staticmethod
    def _basliklar() -> dict[str, str]:
        return {
            "Accept": (
                "application/json"
            ),
            "User-Agent": (
                "SyFinansOtigi/1.0"
            ),
        }

    def fonlari_guvenli_getir(
        self,
        *,
        fon_kodu: str | None = None,
        limit: int = 500,
    ) -> TefasGuvenliSonuc:
        veri_zamani = _simdi()

        depo_anahtari = (
            self.DEPO_ANAHTARI
            + ":"
            + (
                fon_kodu
                .strip()
                .upper()
                if fon_kodu
                else "TUMU"
            )
        )

        try:
            adres = self._adres_olustur(
                fon_kodu=fon_kodu,
                limit=limit,
            )

            ham = self.tasiyici(
                adres,
                self._basliklar(),
                self.zaman_asimi_saniyesi,
            )

            fonlar = (
                TefasJsonCozumleyici
                .coz(
                    ham,
                    varsayilan_zaman=(
                        veri_zamani
                    ),
                )
            )

            self.depo.kaydet(
                anahtar=depo_anahtari,
                veri={
                    "ham": ham.decode(
                        "utf-8"
                    ),
                    "kayit_zamani": (
                        veri_zamani
                    ),
                },
            )

            sonuc = TefasGuvenliSonuc(
                fonlar=fonlar,
                yanit_kaynagi=(
                    YanitKaynagi.CANLI
                ),
                cevrimdisi=False,
                hata=None,
                veri_zamani=(
                    veri_zamani
                ),
                kullanici_aciklamasi=(
                    "Fon verileri canlı "
                    "bağlantıdan alındı. "
                    "Fon fiyatları kaynakta "
                    "yayımlanan son kayıtları "
                    "temsil eder."
                ),
            )

        except Exception as error:
            if not self.depo.var_mi(
                anahtar=depo_anahtari
            ):
                raise ConnectionError(
                    "Fon veri bağlantısı "
                    "kurulamadı ve son güvenilir "
                    "fon kaydı bulunamadı."
                ) from error

            onceki = self.depo.getir(
                anahtar=depo_anahtari
            )

            kayit_zamani = (
                onceki.get(
                    "kayit_zamani"
                )
                or veri_zamani
            )

            fonlar = (
                TefasJsonCozumleyici
                .coz(
                    onceki["ham"],
                    varsayilan_zaman=(
                        kayit_zamani
                    ),
                )
            )

            sonuc = TefasGuvenliSonuc(
                fonlar=fonlar,
                yanit_kaynagi=(
                    YanitKaynagi
                    .SON_GUVENILIR
                ),
                cevrimdisi=True,
                hata=str(error),
                veri_zamani=(
                    kayit_zamani
                ),
                kullanici_aciklamasi=(
                    "Fon veri bağlantısı yok. "
                    "Son güvenilir fon kayıtları "
                    "gösteriliyor."
                ),
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
            or self.fonlari_guvenli_getir(
                fon_kodu=sembol,
                limit=1,
            )
        )

        fon = sonuc.fon_getir(
            sembol
        )

        veri = PiyasaVerisi(
            sembol=(
                fon.fon_kodu
            ),
            varlik_turu=(
                VarlikTuru.FON
            ),
            fiyat=(
                fon.birim_fiyat
            ),
            para_birimi=(
                fon.para_birimi
            ),
            zaman_damgasi=(
                fon.zaman_damgasi
            ),
            kaynak=(
                "Türkiye Elektronik "
                "Fon Alım Satım Platformu"
            ),
            saglayici_id=(
                self.saglayici_id
            ),
            veri_durumu=(
                VeriAkisDurumu.CEVRIMDISI
                if sonuc.cevrimdisi
                else VeriAkisDurumu.GECIKMELI
            ),
            gecikme_saniyesi=(
                0
                if sonuc.cevrimdisi
                else 60
            ),
            hacim=(
                fon.toplam_deger
            ),
            dogrulandi=True,
        )

        muhurlu = (
            VeriDogruLamaMotoru
            .muhurle(
                veri
            )
        )

        return KaynakliPiyasaVerisi(
            veri=muhurlu,
            guven_profili=(
                self.guven_profili
            ),
        )