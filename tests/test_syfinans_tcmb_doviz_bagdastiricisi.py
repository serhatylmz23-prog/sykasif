from decimal import Decimal

import pytest

from syk_finans_otagi.modeller import (
    VarlikTuru,
    VeriAkisDurumu,
)
from syk_finans_otagi.tcmb_doviz_bagdastiricisi import (
    TcmbDovizBagdastiricisi,
    TcmbXmlCozumleyici,
)


XML_ORNEGI = """<?xml version="1.0" encoding="UTF-8"?>
<Tarih_Date Tarih="03.08.2026" Date="08/03/2026">
    <Currency CrossOrder="0" Kod="USD" CurrencyCode="USD">
        <Unit>1</Unit>
        <Isim>ABD DOLARI</Isim>
        <CurrencyName>US DOLLAR</CurrencyName>
        <ForexBuying>40.0000</ForexBuying>
        <ForexSelling>40.2000</ForexSelling>
    </Currency>
    <Currency CrossOrder="1" Kod="EUR" CurrencyCode="EUR">
        <Unit>1</Unit>
        <Isim>EURO</Isim>
        <CurrencyName>EURO</CurrencyName>
        <ForexBuying>45.0000</ForexBuying>
        <ForexSelling>45.3000</ForexSelling>
    </Currency>
    <Currency CrossOrder="2" Kod="JPY" CurrencyCode="JPY">
        <Unit>100</Unit>
        <Isim>JAPON YENİ</Isim>
        <CurrencyName>JAPENESE YEN</CurrencyName>
        <ForexBuying>26.0000</ForexBuying>
        <ForexSelling>26.4000</ForexSelling>
    </Currency>
</Tarih_Date>
""".encode("utf-8")


def test_tcmb_xml_doviz_kayitlarina_donusur():
    sonuc = TcmbXmlCozumleyici.coz(
        XML_ORNEGI,
        istek_zamani=(
            "2026-08-03T15:30:00+03:00"
        ),
    )

    assert len(
        sonuc.kayitlar
    ) == 3

    usd = sonuc.sembol_getir(
        "USDTRY"
    )

    assert (
        usd.alis_fiyati
        == Decimal("40.0000")
    )

    assert (
        usd.satis_fiyati
        == Decimal("40.2000")
    )

    assert (
        usd.orta_fiyat
        == Decimal("40.1000")
    )

    assert len(
        sonuc.yanit_sha256
    ) == 64


def test_birim_degeri_fiyata_uygulanir():
    sonuc = TcmbXmlCozumleyici.coz(
        XML_ORNEGI,
        istek_zamani=(
            "2026-08-03T15:30:00+03:00"
        ),
    )

    jpy = sonuc.sembol_getir(
        "JPYTRY"
    )

    assert (
        jpy.alis_fiyati
        == Decimal("0.2600")
    )

    assert (
        jpy.satis_fiyati
        == Decimal("0.2640")
    )


def test_bagdastirici_ortak_piyasa_verisi_uretir():
    kaynak = TcmbDovizBagdastiricisi(
        tasiyici=(
            lambda adres, zaman_asimi:
            XML_ORNEGI
        )
    )

    sonuc = kaynak.piyasa_verisi_getir(
        sembol="USDTRY"
    )

    assert (
        sonuc.veri.varlik_turu
        == VarlikTuru.DOVIZ
    )

    assert (
        sonuc.veri.veri_durumu
        == VeriAkisDurumu.GECIKMELI
    )

    assert (
        sonuc.veri.fiyat
        == Decimal("40.1000")
    )

    assert (
        sonuc.guven_profili.resmi
    )

    assert len(
        sonuc.veri.veri_sha256
    ) == 64


def test_gecersiz_xml_reddedilir():
    with pytest.raises(
        ValueError,
        match="çözülemedi",
    ):
        TcmbXmlCozumleyici.coz(
            b"<bozuk>",
        )


def test_kur_bulunamazsa_acik_hata_uretilir():
    sonuc = TcmbXmlCozumleyici.coz(
        XML_ORNEGI,
    )

    with pytest.raises(
        KeyError,
        match="bulunamadı",
    ):
        sonuc.sembol_getir(
            "GBPTRY"
        )


def test_bos_kur_listesi_reddedilir():
    with pytest.raises(
        ValueError,
        match="kullanılabilir",
    ):
        TcmbXmlCozumleyici.coz(
            b"<Tarih_Date></Tarih_Date>"
        )