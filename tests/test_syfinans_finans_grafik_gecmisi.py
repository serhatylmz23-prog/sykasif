from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from syk_finans_otagi.finans_grafik_gecmisi import (
    FinansGrafikMotoru,
    FiyatGecmisDeposu,
    GrafikDonemi,
)


def zaman(
    gun: int,
) -> str:
    return (
        datetime(
            2026,
            8,
            1,
            tzinfo=UTC,
        )
        + timedelta(
            days=gun
        )
    ).isoformat()


def depo_olustur():
    depo = FiyatGecmisDeposu()

    depo.kaydet(
        sembol="ASELS",
        fiyat="300",
        hacim="1000",
        zaman=zaman(0),
        kaynak="bist-a",
    )

    depo.kaydet(
        sembol="ASELS",
        fiyat="310",
        hacim="1200",
        zaman=zaman(1),
        kaynak="bist-a",
    )

    depo.kaydet(
        sembol="ASELS",
        fiyat="330",
        hacim="1500",
        zaman=zaman(2),
        kaynak="bist-a",
    )

    return depo


def test_fiyat_gecmisi_kaydedilir():
    depo = depo_olustur()

    kayitlar = depo.kayitlari_getir(
        sembol="ASELS"
    )

    assert len(
        kayitlar
    ) == 3

    assert (
        kayitlar[0].fiyat
        == Decimal("300.0000")
    )

    assert len(
        kayitlar[0].veri_sha256
    ) == 64


def test_grafik_serisi_uretilir():
    motor = FinansGrafikMotoru(
        depo=depo_olustur()
    )

    seri = motor.seri_uret(
        sembol="ASELS"
    )

    assert len(
        seri.noktalar
    ) == 3

    assert (
        seri.en_dusuk_fiyat
        == Decimal("300.0000")
    )

    assert (
        seri.en_yuksek_fiyat
        == Decimal("330.0000")
    )

    assert (
        seri.degisim_orani
        == 10.0
    )

    assert len(
        seri.seri_sha256
    ) == 64


def test_maliyet_ve_kar_zarar_serisi_uretilir():
    motor = FinansGrafikMotoru(
        depo=depo_olustur()
    )

    seri = motor.seri_uret(
        sembol="ASELS",
        ortalama_maliyet="305",
        miktar=100,
    )

    assert (
        seri.noktalar[0]
        .maliyet_cizgisi
        == Decimal("305.0000")
    )

    assert (
        seri.noktalar[0]
        .kar_zarar
        == Decimal("-500.0000")
    )

    assert (
        seri.noktalar[-1]
        .kar_zarar
        == Decimal("2500.0000")
    )


def test_gunluk_donem_filtrelenir():
    motor = FinansGrafikMotoru(
        depo=depo_olustur()
    )

    seri = motor.seri_uret(
        sembol="ASELS",
        donem=GrafikDonemi.GUNLUK,
    )

    assert len(
        seri.noktalar
    ) == 2

    assert (
        seri.noktalar[-1].fiyat
        == Decimal("330.0000")
    )


def test_grafik_ekran_ciktisi_uretilir():
    motor = FinansGrafikMotoru(
        depo=depo_olustur()
    )

    sonuc = motor.ekran_ciktisi(
        sembol="ASELS",
        ortalama_maliyet=305,
        miktar=100,
    )

    assert (
        sonuc["schema"]
        == "syfinans-grafik-ekrani/v1"
    )

    assert len(
        sonuc["fiyat_serisi"]
    ) == 3

    assert (
        sonuc["ozet"][
            "son_fiyat"
        ]
        == 330.0
    )

    assert len(
        sonuc["seri_sha256"]
    ) == 64


def test_gecmis_diske_yazilir(
    tmp_path,
):
    yol = (
        tmp_path
        / "fiyat_gecmisi.json"
    )

    depo = FiyatGecmisDeposu(
        dosya_yolu=yol
    )

    depo.kaydet(
        sembol="USDTRY",
        fiyat="47.50",
        zaman=zaman(0),
        kaynak="tcmb",
    )

    yeniden = FiyatGecmisDeposu(
        dosya_yolu=yol
    )

    kayit = yeniden.kayitlari_getir(
        sembol="USDTRY"
    )[0]

    assert (
        kayit.fiyat
        == Decimal("47.5000")
    )


def test_gecmis_yoksa_acik_hata_uretilir():
    motor = FinansGrafikMotoru(
        depo=FiyatGecmisDeposu()
    )

    with pytest.raises(
        ValueError,
        match="fiyat geçmişi",
    ):
        motor.seri_uret(
            sembol="YOK"
        )