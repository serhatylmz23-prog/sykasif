from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
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
    BistPiyasaKaydi,
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


def _simdi() -> str:
    return datetime.now(
        UTC
    ).isoformat()


def _ondalik(
    deger: Any,
) -> Decimal:
    metin = (
        str(deger)
        .strip()
        .replace(" ", "")
        .replace(",", ".")
    )

    if not metin:
        raise ValueError(
            "Sayısal değer boş olamaz."
        )

    return Decimal(
        metin
    ).quantize(
        Decimal("0.0001"),
        rounding=ROUND_HALF_UP,
    )


def _istege_bagli_ondalik(
    deger: Any,
) -> Decimal | None:
    if deger is None:
        return None

    if str(deger).strip() == "":
        return None

    return _ondalik(
        deger
    )


def _istege_bagli_oran(
    deger: Any,
) -> float | None:
    if deger is None:
        return None

    metin = str(
        deger
    ).strip()

    if not metin:
        return None

    return float(
        metin.replace(
            ",",
            ".",
        )
    )


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
            "quotes",
            "stocks",
            "securities",
            "hisseler",
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

        # Tek hisse kaydı dönen sağlayıcılar.
        if any(
            anahtar in ham
            for anahtar in (
                "symbol",
                "sembol",
                "ticker",
                "code",
            )
        ):
            return [
                ham
            ]

    raise ValueError(
        "BIST yanıtında piyasa kayıt "
        "listesi bulunamadı."
    )


@dataclass(frozen=True, slots=True)
class BistGuvenliSonuc:
    kayitlar: tuple[
        BistPiyasaKaydi,
        ...
    ]
    yanit_kaynagi: YanitKaynagi
    cevrimdisi: bool
    hata: str | None
    veri_zamani: str
    kullanici_aciklamasi: str

    def sembol_getir(
        self,
        sembol: str,
    ) -> BistPiyasaKaydi:
        aranan = (
            str(sembol)
            .strip()
            .upper()
        )

        for kayit in self.kayitlar:
            if (
                kayit.sembol
                .strip()
                .upper()
                == aranan
            ):
                return kayit

        raise KeyError(
            "BIST piyasa kaydı bulunamadı: "
            f"{aranan}"
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "kayitlar": [
                kayit.as_dict()
                for kayit in self.kayitlar
            ],
            "kayit_sayisi": len(
                self.kayitlar
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


class BistJsonCozumleyici:
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
        varsayilan_zaman: str | None = None,
    ) -> tuple[
        BistPiyasaKaydi,
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

        sonuclar: list[
            BistPiyasaKaydi
        ] = []

        for kayit in kayitlar:
            sembol = _metin(
                kayit,
                "sembol",
                "symbol",
                "ticker",
                "code",
                "stock_code",
            ).upper()

            son_fiyat = _metin(
                kayit,
                "son_fiyat",
                "last",
                "last_price",
                "price",
                "close",
            )

            zaman_damgasi = _metin(
                kayit,
                "zaman_damgasi",
                "timestamp",
                "datetime",
                "date",
                "time",
                varsayilan=(
                    varsayilan_zaman
                    or _simdi()
                ),
            )

            if not sembol:
                continue

            if not son_fiyat:
                continue

            alis = (
                kayit.get("alis_fiyati")
                or kayit.get("bid")
                or kayit.get("buy")
            )

            satis = (
                kayit.get("satis_fiyati")
                or kayit.get("ask")
                or kayit.get("sell")
            )

            hacim = (
                kayit.get("hacim")
                or kayit.get("volume")
                or kayit.get("turnover")
            )

            degisim = (
                kayit.get("degisim_orani")
                or kayit.get("change_percent")
                or kayit.get("change_pct")
                or kayit.get("percent_change")
            )

            para_birimi = _metin(
                kayit,
                "para_birimi",
                "currency",
                varsayilan="TRY",
            ).upper()

            sonuclar.append(
                BistPiyasaKaydi(
                    sembol=sembol,
                    son_fiyat=_ondalik(
                        son_fiyat
                    ),
                    alis_fiyati=(
                        _istege_bagli_ondalik(
                            alis
                        )
                    ),
                    satis_fiyati=(
                        _istege_bagli_ondalik(
                            satis
                        )
                    ),
                    hacim=(
                        _istege_bagli_ondalik(
                            hacim
                        )
                    ),
                    degisim_orani=(
                        _istege_bagli_oran(
                            degisim
                        )
                    ),
                    zaman_damgasi=(
                        zaman_damgasi
                    ),
                    para_birimi=(
                        para_birimi
                    ),
                )
            )

        if not sonuclar:
            raise ValueError(
                "BIST yanıtında kullanılabilir "
                "piyasa kaydı bulunamadı."
            )

        benzersiz = {
            kayit.sembol: kayit
            for kayit in sonuclar
        }

        return tuple(
            sorted(
                benzersiz.values(),
                key=lambda kayit: (
                    kayit.sembol
                ),
            )
        )


class BistPiyasaBagdastiricisi(
    PiyasaKaynakBagdastiricisi
):
    SAGLAYICI_ID = "bist-lisansli-kaynak"
    DEPO_ANAHTARI = "BIST-PIYASA"

    def __init__(
        self,
        *,
        adres: str | None = None,
        api_anahtari: str | None = None,
        zaman_asimi_saniyesi: float = 10.0,
        veri_gecikmesi_saniyesi: int = 0,
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
                "SYFINANS_BIST_API_ADRESI",
                "",
            )
        ).strip()

        self.api_anahtari = (
            api_anahtari
            or os.getenv(
                "SYFINANS_BIST_API_ANAHTARI",
                "",
            )
        ).strip()

        self.zaman_asimi_saniyesi = float(
            zaman_asimi_saniyesi
        )

        self.veri_gecikmesi_saniyesi = max(
            0,
            int(
                veri_gecikmesi_saniyesi
            ),
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
            BistGuvenliSonuc | None
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
        return FinansKaynakSinifi.BIST

    @property
    def guven_profili(
        self,
    ) -> KaynakGuvenProfili:
        return KaynakGuvenProfili(
            saglayici_id=(
                self.saglayici_id
            ),
            kaynak_turu=(
                KaynakTuru.LISANSLI_PIYASA
            ),
            temel_guven_puani=90,
            guncellik_puani=(
                94
                if self.veri_gecikmesi_saniyesi
                == 0
                else 82
            ),
            gecmis_tutarlilik_puani=90,
            kesinti_dayanim_puani=85,
            lisansli=True,
            resmi=False,
            aciklama=(
                "BIST verisi izinli ve lisanslı "
                "sağlayıcı sözleşmesi üzerinden "
                "işlenir."
            ),
        )

    def _basliklar(
        self,
    ) -> dict[str, str]:
        basliklar = {
            "Accept": (
                "application/json"
            ),
            "User-Agent": (
                "SyFinansOtigi/1.0"
            ),
        }

        if self.api_anahtari:
            basliklar[
                "Authorization"
            ] = (
                "Bearer "
                + self.api_anahtari
            )

        return basliklar

    def _adres_olustur(
        self,
        *,
        sembol: str | None,
        limit: int,
    ) -> str:
        if not self.adres:
            raise RuntimeError(
                "BIST veri sağlayıcı adresi "
                "tanımlanmadı. "
                "SYFINANS_BIST_API_ADRESI "
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

        if sembol:
            sorgu["symbol"] = (
                sembol
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

    def piyasa_kayitlarini_guvenli_getir(
        self,
        *,
        sembol: str | None = None,
        limit: int = 500,
    ) -> BistGuvenliSonuc:
        veri_zamani = _simdi()

        depo_anahtari = (
            self.DEPO_ANAHTARI
            + ":"
            + (
                sembol
                .strip()
                .upper()
                if sembol
                else "TUMU"
            )
        )

        try:
            adres = self._adres_olustur(
                sembol=sembol,
                limit=limit,
            )

            ham = self.tasiyici(
                adres,
                self._basliklar(),
                self.zaman_asimi_saniyesi,
            )

            kayitlar = (
                BistJsonCozumleyici
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

            gecikmeli = (
                self.veri_gecikmesi_saniyesi
                > 0
            )

            sonuc = BistGuvenliSonuc(
                kayitlar=kayitlar,
                yanit_kaynagi=(
                    YanitKaynagi.CANLI
                ),
                cevrimdisi=False,
                hata=None,
                veri_zamani=veri_zamani,
                kullanici_aciklamasi=(
                    (
                        "BIST verisi canlı "
                        "bağlantıdan alındı."
                    )
                    if not gecikmeli
                    else (
                        "BIST verisi sağlayıcının "
                        f"bildirdiği yaklaşık "
                        f"{self.veri_gecikmesi_saniyesi} "
                        "saniyelik gecikmeyle alındı."
                    )
                ),
            )

        except Exception as error:
            if not self.depo.var_mi(
                anahtar=depo_anahtari
            ):
                raise ConnectionError(
                    "BIST veri bağlantısı "
                    "kurulamadı ve son güvenilir "
                    "piyasa kaydı bulunamadı."
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

            kayitlar = (
                BistJsonCozumleyici
                .coz(
                    onceki["ham"],
                    varsayilan_zaman=(
                        kayit_zamani
                    ),
                )
            )

            sonuc = BistGuvenliSonuc(
                kayitlar=kayitlar,
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
                    "BIST veri bağlantısı yok. "
                    "Son güvenilir piyasa kaydı "
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
            or self
            .piyasa_kayitlarini_guvenli_getir(
                sembol=sembol,
                limit=1,
            )
        )

        kayit = sonuc.sembol_getir(
            sembol
        )

        if sonuc.cevrimdisi:
            akis_durumu = (
                VeriAkisDurumu.CEVRIMDISI
            )

        elif (
            self.veri_gecikmesi_saniyesi
            > 0
        ):
            akis_durumu = (
                VeriAkisDurumu.GECIKMELI
            )

        else:
            akis_durumu = (
                VeriAkisDurumu.ANLIK
            )

        veri = PiyasaVerisi(
            sembol=(
                kayit.sembol
            ),
            varlik_turu=(
                VarlikTuru.HISSE
            ),
            fiyat=(
                kayit.son_fiyat
            ),
            para_birimi=(
                kayit.para_birimi
            ),
            zaman_damgasi=(
                kayit.zaman_damgasi
            ),
            kaynak=(
                "BIST lisanslı veri sağlayıcısı"
            ),
            saglayici_id=(
                self.saglayici_id
            ),
            veri_durumu=(
                akis_durumu
            ),
            gecikme_saniyesi=(
                0
                if sonuc.cevrimdisi
                else self
                .veri_gecikmesi_saniyesi
            ),
            alis_fiyati=(
                kayit.alis_fiyati
            ),
            satis_fiyati=(
                kayit.satis_fiyati
            ),
            hacim=(
                kayit.hacim
            ),
            degisim_orani=(
                kayit.degisim_orani
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