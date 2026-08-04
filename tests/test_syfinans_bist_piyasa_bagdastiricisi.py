import json
from decimal import Decimal

import pytest

from syk_finans_otagi.baglanti_calisma_katmani import (
    SonGuvenilirYanitDeposu,
    YanitKaynagi,
)
from syk_finans_otagi.bist_piyasa_bagdastiricisi import (
    BistJsonCozumleyici,
    BistPiyasaBagdastiricisi,
)
from syk_finans_otagi.modeller import (
    VarlikTuru,
    VeriAkisDurumu,
)


ORNEK = {
    "data": [
        {
            "symbol": "ASELS",
            "last_price": "300.1250",
            "bid": "300.1000",
            "ask": "300.1500",
            "volume": "250000000",
            "change_percent": "1.25",
            "timestamp": (
                "2026-08-04T10:30:00+03:00"
            ),
            "currency": "TRY",
        },
        {
            "symbol": "THYAO",
            "last_price": "410.5000",
            "bid": "410.2500",
            "ask": "410.7500",
            "volume": "180000000",
            "change_percent": "-0.40",
            "timestamp": (
                "2026-08-04T10:30:00+03:00"
            ),
            "currency": "TRY",
        },
    ]
}


def ham() -> bytes:
    return json.dumps(
        ORNEK,
        ensure_ascii=False,
    ).encode("utf-8")


def test_bist_json_ortak_kayda_donusur():
    kayitlar = (
        BistJsonCozumleyici
        .coz(
            ham()
        )
    )

    assert len(
        kayitlar
    ) == 2

    asels = next(
        kayit
        for kayit in kayitlar
        if kayit.sembol == "ASELS"
    )

    assert (
        asels.son_fiyat
        == Decimal("300.1250")
    )

    assert (
        asels.alis_fiyati
        == Decimal("300.1000")
    )

    assert (
        asels.satis_fiyati
        == Decimal("300.1500")
    )


def test_hacim_ve_degisimin_orani_korunur():
    asels = (
        BistJsonCozumleyici
        .coz(
            ham()
        )[0]
    )

    assert (
        asels.hacim
        == Decimal(
            "250000000.0000"
        )
    )

    assert (
        asels.degisim_orani
        == 1.25
    )


def test_canli_bist_verisi_depolanir():
    depo = SonGuvenilirYanitDeposu()

    kaynak = BistPiyasaBagdastiricisi(
        adres=(
            "https://ornek.invalid/bist"
        ),
        depo=depo,
        tasiyici=(
            lambda adres, basliklar, sure:
            ham()
        ),
    )

    sonuc = (
        kaynak
        .piyasa_kayitlarini_guvenli_getir()
    )

    assert (
        sonuc.yanit_kaynagi
        == YanitKaynagi.CANLI
    )

    assert not sonuc.cevrimdisi

    assert len(
        sonuc.kayitlar
    ) == 2


def test_baglanti_kesilince_son_guvenilir_bist_kaydi_kullanilir():
    depo = SonGuvenilirYanitDeposu()

    canli = BistPiyasaBagdastiricisi(
        adres=(
            "https://ornek.invalid/bist"
        ),
        depo=depo,
        tasiyici=(
            lambda adres, basliklar, sure:
            ham()
        ),
    )

    canli.piyasa_kayitlarini_guvenli_getir(
        sembol="ASELS"
    )

    kesik = BistPiyasaBagdastiricisi(
        adres=(
            "https://ornek.invalid/bist"
        ),
        depo=depo,
        tasiyici=lambda *args: (
            (_ for _ in ())
            .throw(
                TimeoutError(
                    "Bağlantı yok"
                )
            )
        ),
    )

    sonuc = (
        kesik
        .piyasa_kayitlarini_guvenli_getir(
            sembol="ASELS"
        )
    )

    assert sonuc.cevrimdisi

    assert (
        sonuc.yanit_kaynagi
        == YanitKaynagi
        .SON_GUVENILIR
    )


def test_anlik_hisse_ortak_piyasa_verisine_donusur():
    kaynak = BistPiyasaBagdastiricisi(
        adres=(
            "https://ornek.invalid/bist"
        ),
        tasiyici=(
            lambda adres, basliklar, sure:
            ham()
        ),
        veri_gecikmesi_saniyesi=0,
    )

    sonuc = kaynak.piyasa_verisi_getir(
        sembol="ASELS"
    )

    assert (
        sonuc.veri.varlik_turu
        == VarlikTuru.HISSE
    )

    assert (
        sonuc.veri.veri_durumu
        == VeriAkisDurumu.ANLIK
    )

    assert (
        sonuc.veri.fiyat
        == Decimal("300.1250")
    )

    assert len(
        sonuc.veri.veri_sha256
    ) == 64


def test_gecikmeli_veri_acikca_isaretlenir():
    kaynak = BistPiyasaBagdastiricisi(
        adres=(
            "https://ornek.invalid/bist"
        ),
        tasiyici=(
            lambda adres, basliklar, sure:
            ham()
        ),
        veri_gecikmesi_saniyesi=900,
    )

    sonuc = kaynak.piyasa_verisi_getir(
        sembol="ASELS"
    )

    assert (
        sonuc.veri.veri_durumu
        == VeriAkisDurumu.GECIKMELI
    )

    assert (
        sonuc.veri.gecikme_saniyesi
        == 900
    )


def test_adres_yoksa_acik_hata_uretilir(
    monkeypatch,
):
    monkeypatch.delenv(
        "SYFINANS_BIST_API_ADRESI",
        raising=False,
    )

    kaynak = (
        BistPiyasaBagdastiricisi()
    )

    with pytest.raises(
        ConnectionError,
        match="son güvenilir",
    ):
        (
            kaynak
            .piyasa_kayitlarini_guvenli_getir()
        )


def test_bos_bist_listesi_reddedilir():
    with pytest.raises(
        ValueError,
        match="kullanılabilir",
    ):
        BistJsonCozumleyici.coz(
            {
                "data": []
            }
        )


def test_bilinmeyen_sembol_acik_hata_uretir():
    sonuc = BistPiyasaBagdastiricisi(
        adres=(
            "https://ornek.invalid/bist"
        ),
        tasiyici=(
            lambda adres, basliklar, sure:
            ham()
        ),
    ).piyasa_kayitlarini_guvenli_getir()

    with pytest.raises(
        KeyError,
        match="bulunamadı",
    ):
        sonuc.sembol_getir(
            "BILINMEYEN"
        )