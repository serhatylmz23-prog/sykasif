from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import json
import os
from pathlib import Path
import unicodedata
from typing import Any, Callable, Iterable, Mapping
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .baglanti_calisma_katmani import (
    SonGuvenilirYanitDeposu,
    YanitKaynagi,
)
from .gercek_kaynak_sozlesmeleri import (
    BildirimOnemi,
    FinansKaynakSinifi,
    KapBildirimi,
    KapBildirimDogrulamaMotoru,
    KapKaynakBagdastiricisi,
)


def _simdi() -> str:
    return datetime.now(
        UTC
    ).isoformat()


def _metin(
    veri: Mapping[str, Any],
    *anahtarlar: str,
    varsayilan: str = "",
) -> str:
    for anahtar in anahtarlar:
        deger = veri.get(
            anahtar
        )

        if deger is not None:
            sonuc = str(
                deger
            ).strip()

            if sonuc:
                return sonuc

    return varsayilan


def _liste(
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
            "items",
            "data",
            "results",
            "notifications",
            "bildirimler",
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
        "KAP yanıtında bildirim listesi "
        "bulunamadı."
    )


# SYF_KAP_TURKCE_METIN_NORMALLESTIRME
def _arama_metni(
    deger: str,
) -> str:
    metin = unicodedata.normalize(
        "NFKD",
        str(
            deger
        ).casefold(),
    )

    metin = "".join(
        karakter
        for karakter in metin
        if not unicodedata.combining(
            karakter
        )
    )

    ceviri = str.maketrans(
        {
            "ı": "i",
            "ş": "s",
            "ğ": "g",
            "ü": "u",
            "ö": "o",
            "ç": "c",
        }
    )

    return (
        metin
        .translate(
            ceviri
        )
        .strip()
    )


def _onem_belirle(
    *,
    baslik: str,
    bildirim_turu: str,
    ozet: str,
) -> BildirimOnemi:
    metin = _arama_metni(
        " ".join(
            (
                baslik,
                bildirim_turu,
                ozet,
            )
        )
    )

    kritik_ifadeler = (
        "iflas",
        "konkordato",
        "faaliyet durdur",
        "islem sirasi kapat",
        "temerrut",
        "tasfiye",
    )

    onemli_ifadeler = (
        "yeni is iliskisi",
        "ihale",
        "sermaye artir",
        "temettu",
        "pay geri alim",
        "birlesme",
        "devralma",
        "yatirim",
        "finansal rapor",
    )

    dikkat_ifadeleri = (
        "yonetim kurulu",
        "genel kurul",
        "ozel durum",
        "sozlesme",
        "kredi",
    )

    if any(
        ifade in metin
        for ifade in kritik_ifadeler
    ):
        return BildirimOnemi.KRITIK

    if any(
        ifade in metin
        for ifade in onemli_ifadeler
    ):
        return BildirimOnemi.ONEMLI

    if any(
        ifade in metin
        for ifade in dikkat_ifadeleri
    ):
        return BildirimOnemi.DIKKAT

    return BildirimOnemi.BILGI


@dataclass(frozen=True, slots=True)
class KapGuvenliSonuc:
    bildirimler: tuple[
        KapBildirimi,
        ...
    ]
    yanit_kaynagi: YanitKaynagi
    cevrimdisi: bool
    hata: str | None
    kullanici_aciklamasi: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "bildirimler": [
                bildirim.as_dict()
                for bildirim
                in self.bildirimler
            ],
            "bildirim_sayisi": len(
                self.bildirimler
            ),
            "yanit_kaynagi": (
                self.yanit_kaynagi.value
            ),
            "cevrimdisi": (
                self.cevrimdisi
            ),
            "hata": self.hata,
            "kullanici_aciklamasi": (
                self.kullanici_aciklamasi
            ),
        }


class KapJsonCozumleyici:
    @classmethod
    def coz(
        cls,
        ham_yanit: (
            bytes
            | str
            | Mapping[str, Any]
            | list[Any]
        ),
    ) -> tuple[
        KapBildirimi,
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

        kayitlar = _liste(
            ham
        )

        bildirimler: list[
            KapBildirimi
        ] = []

        for kayit in kayitlar:
            bildirim_id = _metin(
                kayit,
                "bildirim_id",
                "notification_id",
                "disclosure_id",
                "id",
            )

            sembol = _metin(
                kayit,
                "sembol",
                "symbol",
                "stock_code",
                "company_code",
            ).upper()

            baslik = _metin(
                kayit,
                "baslik",
                "title",
                "subject",
            )

            yayin_zamani = _metin(
                kayit,
                "yayin_zamani",
                "published_at",
                "publish_date",
                "date",
            )

            bildirim_turu = _metin(
                kayit,
                "bildirim_turu",
                "notification_type",
                "type",
                "category",
                varsayilan=(
                    "KAP bildirimi"
                ),
            )

            ozet = _metin(
                kayit,
                "ozet",
                "summary",
                "description",
                "content",
            )

            kaynak_adresi = _metin(
                kayit,
                "kaynak_adresi",
                "url",
                "link",
            )

            if not bildirim_id:
                continue

            if not sembol:
                continue

            if not baslik:
                continue

            if not yayin_zamani:
                continue

            onem = _onem_belirle(
                baslik=baslik,
                bildirim_turu=(
                    bildirim_turu
                ),
                ozet=ozet,
            )

            bildirim = KapBildirimi(
                bildirim_id=(
                    bildirim_id
                ),
                sembol=sembol,
                baslik=baslik,
                yayin_zamani=(
                    yayin_zamani
                ),
                bildirim_turu=(
                    bildirim_turu
                ),
                ozet=ozet,
                kaynak_adresi=(
                    kaynak_adresi
                ),
                onem=onem,
            )

            bildirimler.append(
                KapBildirimDogrulamaMotoru
                .muhurle(
                    bildirim
                )
            )

        if not bildirimler:
            raise ValueError(
                "KAP yanıtında kullanılabilir "
                "bildirim bulunamadı."
            )

        benzersiz = {
            bildirim.bildirim_id: bildirim
            for bildirim in bildirimler
        }

        return tuple(
            sorted(
                benzersiz.values(),
                key=lambda bildirim: (
                    bildirim.yayin_zamani,
                    bildirim.bildirim_id,
                ),
                reverse=True,
            )
        )


class KapBildirimBagdastiricisi(
    KapKaynakBagdastiricisi
):
    SAGLAYICI_ID = "kap-resmi"
    DEPO_ANAHTARI = "KAP-BILDIRIMLER"

    def __init__(
        self,
        *,
        adres: str | None = None,
        api_anahtari: str | None = None,
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
                "SYFINANS_KAP_API_ADRESI",
                "",
            )
        ).strip()

        self.api_anahtari = (
            api_anahtari
            or os.getenv(
                "SYFINANS_KAP_API_ANAHTARI",
                "",
            )
        ).strip()

        self.zaman_asimi_saniyesi = float(
            zaman_asimi_saniyesi
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
            KapGuvenliSonuc | None
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
        return FinansKaynakSinifi.KAP

    @property
    def guven_profili(
        self,
    ) -> dict[str, Any]:
        return {
            "saglayici_id": (
                self.saglayici_id
            ),
            "kaynak": (
                "Kamuyu Aydınlatma Platformu"
            ),
            "resmi": True,
            "veri_turu": (
                "şirket ve fon bildirimleri"
            ),
        }

    def _adres_olustur(
        self,
        *,
        sembol: str | None,
        limit: int,
    ) -> str:
        if not self.adres:
            raise RuntimeError(
                "KAP resmî API adresi "
                "tanımlanmadı. "
                "SYFINANS_KAP_API_ADRESI "
                "ortam değişkenini ayarlayın."
            )

        sorgu = {
            "limit": max(
                1,
                min(
                    int(limit),
                    500,
                ),
            )
        }

        if sembol:
            sorgu["symbol"] = (
                sembol.strip().upper()
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

    def bildirimleri_guvenli_getir(
        self,
        *,
        sembol: str | None = None,
        limit: int = 50,
    ) -> KapGuvenliSonuc:
        depo_anahtari = (
            self.DEPO_ANAHTARI
            + ":"
            + (
                sembol.strip().upper()
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

            bildirimler = (
                KapJsonCozumleyici
                .coz(ham)
            )

            self.depo.kaydet(
                anahtar=depo_anahtari,
                veri={
                    "ham": ham.decode(
                        "utf-8"
                    ),
                    "kayit_zamani": (
                        _simdi()
                    ),
                },
            )

            sonuc = KapGuvenliSonuc(
                bildirimler=bildirimler,
                yanit_kaynagi=(
                    YanitKaynagi.CANLI
                ),
                cevrimdisi=False,
                hata=None,
                kullanici_aciklamasi=(
                    "KAP bildirimleri resmî "
                    "bağlantıdan alındı."
                ),
            )

        except Exception as error:
            if not self.depo.var_mi(
                anahtar=depo_anahtari
            ):
                raise ConnectionError(
                    "KAP bağlantısı kurulamadı "
                    "ve son güvenilir bildirim "
                    "kaydı bulunamadı."
                ) from error

            onceki = self.depo.getir(
                anahtar=depo_anahtari
            )

            bildirimler = (
                KapJsonCozumleyici
                .coz(
                    onceki["ham"]
                )
            )

            sonuc = KapGuvenliSonuc(
                bildirimler=bildirimler,
                yanit_kaynagi=(
                    YanitKaynagi
                    .SON_GUVENILIR
                ),
                cevrimdisi=True,
                hata=str(error),
                kullanici_aciklamasi=(
                    "KAP bağlantısı kullanılamıyor. "
                    "Son güvenilir bildirimler "
                    "gösteriliyor."
                ),
            )

        self._son_sonuc = sonuc

        return sonuc

    def bildirimleri_getir(
        self,
        *,
        sembol: str | None = None,
        limit: int = 50,
    ) -> tuple[
        KapBildirimi,
        ...
    ]:
        return (
            self.bildirimleri_guvenli_getir(
                sembol=sembol,
                limit=limit,
            )
            .bildirimler
        )