import pytest

from syk_finans_otagi.cift_katman import (
    KullaniciKasasi,
    PiyasaEvreni,
)
from syk_finans_otagi.modeller import (
    VarlikTuru,
)
from syk_finans_otagi.piyasa_katalogu import (
    KatalogFiltresi,
    PiyasaKatalogMotoru,
)


def piyasa() -> PiyasaEvreni:
    evren = PiyasaEvreni()

    kayitlar = [
        (
            "ASELS",
            VarlikTuru.HISSE,
            "Aselsan",
            "Savunma",
        ),
        (
            "THYAO",
            VarlikTuru.HISSE,
            "Türk Hava Yolları",
            "Ulaştırma",
        ),
        (
            "FON-A",
            VarlikTuru.FON,
            "Örnek Fon",
            "Fon",
        ),
        (
            "USDTRY",
            VarlikTuru.DOVIZ,
            "Amerikan Doları",
            "Döviz",
        ),
        (
            "ALTIN",
            VarlikTuru.ALTIN,
            "Gram Altın",
            "Kıymetli Maden",
        ),
        (
            "GUMUS",
            VarlikTuru.GUMUS,
            "Gram Gümüş",
            "Kıymetli Maden",
        ),
    ]

    for sembol, tur, ad, sektor in kayitlar:
        evren.varlik_ekle(
            sembol=sembol,
            varlik_turu=tur,
            ad=ad,
            sektor=sektor,
        )

    return evren


def kasa() -> KullaniciKasasi:
    kullanici = KullaniciKasasi()

    kullanici.kayit_ekle(
        kayit_id="K-001",
        sembol="ASELS",
        varlik_turu=(
            VarlikTuru.HISSE
        ),
        miktar=10,
        birim_fiyat=250,
        islem_tarihi=(
            "2025-01-10T10:00:00+03:00"
        ),
    )

    kullanici.kayit_ekle(
        kayit_id="K-002",
        sembol="USDTRY",
        varlik_turu=(
            VarlikTuru.DOVIZ
        ),
        miktar=1000,
        birim_fiyat=30,
        islem_tarihi=(
            "2025-02-10T10:00:00+03:00"
        ),
    )

    return kullanici


def test_tum_piyasa_listelenir():
    sonuc = PiyasaKatalogMotoru.filtrele(
        piyasa=piyasa(),
        kasa=kasa(),
        filtre=KatalogFiltresi(),
    )

    assert (
        sonuc.filtrelenmis_varlik_sayisi
        == 6
    )


def test_yalniz_kasamdakiler_listelenir():
    sonuc = PiyasaKatalogMotoru.filtrele(
        piyasa=piyasa(),
        kasa=kasa(),
        filtre=KatalogFiltresi(
            yalniz_kasamdakiler=True,
        ),
    )

    assert {
        kayit.sembol
        for kayit in sonuc.kayitlar
    } == {
        "ASELS",
        "USDTRY",
    }


def test_yalniz_kasamda_olmayanlar_listelenir():
    sonuc = PiyasaKatalogMotoru.filtrele(
        piyasa=piyasa(),
        kasa=kasa(),
        filtre=KatalogFiltresi(
            yalniz_kasamda_olmayanlar=True,
        ),
    )

    assert {
        kayit.sembol
        for kayit in sonuc.kayitlar
    } == {
        "THYAO",
        "FON-A",
        "ALTIN",
        "GUMUS",
    }


def test_varlik_turune_gore_filtrelenir():
    sonuc = PiyasaKatalogMotoru.filtrele(
        piyasa=piyasa(),
        kasa=kasa(),
        filtre=KatalogFiltresi(
            varlik_turu=(
                VarlikTuru.HISSE
            ),
        ),
    )

    assert {
        kayit.sembol
        for kayit in sonuc.kayitlar
    } == {
        "ASELS",
        "THYAO",
    }


def test_sektore_gore_filtrelenir():
    sonuc = PiyasaKatalogMotoru.filtrele(
        piyasa=piyasa(),
        kasa=kasa(),
        filtre=KatalogFiltresi(
            sektor="Kıymetli Maden",
        ),
    )

    assert {
        kayit.sembol
        for kayit in sonuc.kayitlar
    } == {
        "ALTIN",
        "GUMUS",
    }


def test_ad_sembol_ve_sektorde_arama_yapilir():
    sonuc = PiyasaKatalogMotoru.filtrele(
        piyasa=piyasa(),
        kasa=kasa(),
        filtre=KatalogFiltresi(
            arama="hava",
        ),
    )

    assert [
        kayit.sembol
        for kayit in sonuc.kayitlar
    ] == [
        "THYAO",
    ]


def test_kasif_aday_havuzu_kasadakileri_dislar():
    sonuc = (
        PiyasaKatalogMotoru
        .kasif_aday_havuzu(
            piyasa=piyasa(),
            kasa=kasa(),
            varlik_turleri=[
                VarlikTuru.HISSE,
                VarlikTuru.FON,
            ],
        )
    )

    assert {
        kayit.sembol
        for kayit in sonuc.kayitlar
    } == {
        "THYAO",
        "FON-A",
    }


def test_celisik_kasa_filtresi_reddedilir():
    with pytest.raises(
        ValueError,
        match="aynı anda",
    ):
        KatalogFiltresi(
            yalniz_kasamdakiler=True,
            yalniz_kasamda_olmayanlar=True,
        )


def test_katalog_sha256_uretir():
    sonuc = PiyasaKatalogMotoru.filtrele(
        piyasa=piyasa(),
        kasa=kasa(),
        filtre=KatalogFiltresi(),
    )

    assert len(
        sonuc.katalog_sha256
    ) == 64