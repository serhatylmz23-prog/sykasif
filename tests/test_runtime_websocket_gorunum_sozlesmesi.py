from dataclasses import dataclass

import pytest

from syk_simulasyon.runtime_websocket import (
    RuntimeWebSocketYayincisi,
)


@dataclass
class _AnlikGorunum:
    durum: str
    aktif_modul: str
    ilerleme_yuzdesi: float
    olay_sayisi: int


class _GorunumSaglayici:
    def gorunum(self) -> _AnlikGorunum:
        return _AnlikGorunum(
            durum="çalışıyor",
            aktif_modul="Canlı Modül",
            ilerleme_yuzdesi=62.5,
            olay_sayisi=4,
        )


class _OlusturSaglayici:
    def olustur(self) -> dict[str, object]:
        return {
            "durum": "hazır",
            "aktif_modul": "Eski Sözleşme",
            "ilerleme_yuzdesi": 25.0,
            "olay_sayisi": 1,
        }


class _GecersizSaglayici:
    def gorunum(self) -> object:
        return object()


def test_websocket_gorunum_metodunu_okur():
    yayinci = RuntimeWebSocketYayincisi(
        _GorunumSaglayici()
    )

    mesaj = yayinci.guncelleme_mesaji()

    assert mesaj["gorunum"]["durum"] == "çalışıyor"
    assert mesaj["gorunum"]["aktif_modul"] == "Canlı Modül"
    assert mesaj["gorunum"]["ilerleme_yuzdesi"] == 62.5
    assert mesaj["gorunum"]["olay_sayisi"] == 4


def test_websocket_eski_olustur_sozlesmesini_korur():
    yayinci = RuntimeWebSocketYayincisi(
        _OlusturSaglayici()
    )

    mesaj = yayinci.baglanti_mesaji()

    assert mesaj["gorunum"]["aktif_modul"] == "Eski Sözleşme"
    assert mesaj["gorunum"]["ilerleme_yuzdesi"] == 25.0


def test_websocket_gecersiz_gorunumu_reddeder():
    yayinci = RuntimeWebSocketYayincisi(
        _GecersizSaglayici()
    )

    with pytest.raises(
        TypeError,
        match="sözlüğe dönüştürülebilir",
    ):
        yayinci.guncelleme_mesaji()

def test_websocket_sistem_hazirligini_ayri_alanda_yayinlar():
    hazirlik = {
        "terminal_arayuzu": 100,
        "veri_akisi": 90,
        "kayit_zinciri": 80,
        "test_durumu": 70,
        "disa_aktarim_hazirligi": 60,
        "genel_uretime_hazirlik": 80,
    }

    yayinci = RuntimeWebSocketYayincisi(
        _GorunumSaglayici(),
        lambda: hazirlik,
    )

    mesaj = yayinci.guncelleme_mesaji()

    assert mesaj["gorunum"]["aktif_modul"] == "Canlı Modül"
    assert mesaj["sistem_hazirlik"] == hazirlik


def test_websocket_hazirlik_kaynagi_yokken_bos_sozluk_yayinlar():
    yayinci = RuntimeWebSocketYayincisi(
        _GorunumSaglayici()
    )

    mesaj = yayinci.baglanti_mesaji()

    assert mesaj["sistem_hazirlik"] == {}
