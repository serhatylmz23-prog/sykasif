"""SyKaşif birleşik prototip canlı HTTP doğrulaması."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .baslatici import PrototipBaslaticisi


class PrototipCanliDogrulamaHatasi(RuntimeError):
    """Birleşik prototip canlı doğrulama hatası."""


@dataclass(slots=True, frozen=True)
class CanliYolSonucu:
    yol: str
    durum_kodu: int
    basarili: bool
    veri: dict[str, Any]

    def sozluk(self) -> dict[str, Any]:
        return {
            "yol": self.yol,
            "durum_kodu": self.durum_kodu,
            "başarılı": self.basarili,
            "veri": self.veri,
        }


def json_istegi(
    adres: str,
    *,
    zaman_asimi_saniye: float = 5.0,
) -> tuple[int, dict[str, Any]]:
    istek = Request(
        adres,
        headers={
            "Accept": "application/json",
        },
        method="GET",
    )

    try:
        with urlopen(
            istek,
            timeout=zaman_asimi_saniye,
        ) as yanit:
            ham = yanit.read().decode("utf-8")

            try:
                veri = json.loads(ham)
            except json.JSONDecodeError:
                veri = {
                    "ham_yanit": ham,
                }

            return int(yanit.status), veri

    except HTTPError as hata:
        ham = hata.read().decode("utf-8")

        try:
            veri = json.loads(ham)
        except json.JSONDecodeError:
            veri = {
                "ham_yanit": ham,
            }

        return int(hata.code), veri

    except URLError as hata:
        raise PrototipCanliDogrulamaHatasi(
            f"Canlı prototipe bağlanılamadı: {hata}"
        ) from hata


class PrototipCanliDogrulayici:
    """Tek komutlu başlatıcıyı gerçek HTTP yuvasında doğrular."""

    ZORUNLU_YOLLAR = (
        "/terminal",
        "/cihaz-iletisimi/saglik",
        "/saha-cihazlari/saglik",
    )

    def __init__(
        self,
        baslatici: PrototipBaslaticisi,
    ) -> None:
        self.baslatici = baslatici

    def dogrula(
        self,
    ) -> dict[str, Any]:
        adres: str | None = None
        sonuclar: list[CanliYolSonucu] = []

        try:
            adres = self.baslatici.baslat()

            for yol in self.ZORUNLU_YOLLAR:
                durum_kodu, veri = json_istegi(
                    adres + yol
                )

                sonuc = CanliYolSonucu(
                    yol=yol,
                    durum_kodu=durum_kodu,
                    basarili=(
                        durum_kodu == 200
                    ),
                    veri=veri,
                )

                sonuclar.append(
                    sonuc
                )

                if not sonuc.basarili:
                    raise PrototipCanliDogrulamaHatasi(
                        f"Canlı yol başarısız: "
                        f"{yol} ({durum_kodu})"
                    )

            return {
                "başarılı": True,
                "ana_adres": adres,
                "çalışıyor": (
                    self.baslatici.calisiyor_mu
                ),
                "gerçek_işlem": (
                    self.baslatici
                    .prototip
                    .terminal
                    .uygulama_isletmeni
                    .gercek_isleme_izin_ver
                    if self.baslatici.prototip
                    else None
                ),
                "yollar": [
                    sonuc.sozluk()
                    for sonuc in sonuclar
                ],
            }

        finally:
            self.baslatici.durdur()

    def kapanis_dayanikliligini_dogrula(
        self,
    ) -> dict[str, Any]:
        adres = self.baslatici.baslat()

        if not self.baslatici.calisiyor_mu:
            raise PrototipCanliDogrulamaHatasi(
                "Prototip başlatıldıktan sonra çalışmıyor."
            )

        self.baslatici.durdur()

        ilk_kapanis = (
            not self.baslatici.calisiyor_mu
        )

        self.baslatici.durdur()

        ikinci_kapanis = (
            not self.baslatici.calisiyor_mu
        )

        if not (
            ilk_kapanis
            and ikinci_kapanis
        ):
            raise PrototipCanliDogrulamaHatasi(
                "Güvenli kapanış dayanıklılığı doğrulanamadı."
            )

        return {
            "başarılı": True,
            "ana_adres": adres,
            "ilk_kapanış": ilk_kapanis,
            "ikinci_kapanış": ikinci_kapanis,
            "durum": "durduruldu",
        }
