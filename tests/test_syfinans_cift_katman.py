from decimal import Decimal

from syk_finans_otagi.cift_katman import (
    KullaniciKasasi,
    PiyasaEvreni,
    SyFinansCiftKatman,
)
from syk_finans_otagi.modeller import (
    VarlikTuru,
)


def piyasa() -> PiyasaEvreni:
    evren = PiyasaEvreni()

    evren.varlik_ekle(
        sembol="ASELS",
        varlik_turu=(
            VarlikTuru.HISSE
        ),
        ad="Aselsan",
        sektor="Savunma",
    )

    evren.varlik_ekle(
        sembol="THYAO",
        varlik_turu=(
            VarlikTuru.HISSE
        ),
        ad="Türk Hava Yolları",
        sektor="Ulaştırma",
    )

    evren.varlik_ekle(
        sembol="USDTRY",
        varlik_turu=(
            VarlikTuru.DOVIZ
        ),
        ad="Amerikan Doları",
        sektor="Döviz",
    )

    return evren


def kasa() -> KullaniciKasasi:
    kullanici_kasasi = (
        KullaniciKasasi()
    )

    kullanici_kasasi.kayit_ekle(
        kayit_id="KASA-001",
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

    kullanici_kasasi.kayit_ekle(
        kayit_id="KASA-002",
        sembol="ASELS",
        varlik_turu=(
            VarlikTuru.HISSE
        ),
        miktar=20,
        birim_fiyat=300,
        islem_tarihi=(
            "2026-01-10T10:00:00+03:00"
        ),
    )

    return kullanici_kasasi


def test_piyasa_ve_kasa_ayri_katmanlardir():
    sistem = SyFinansCiftKatman(
        piyasa=piyasa(),
        kasa=kasa(),
    )

    sozlesme = (
        sistem.ekran_sozlesmesi()
    )

    assert [
        katman["katman_id"]
        for katman
        in sozlesme["katmanlar"]
    ] == [
        "piyasa_evreni",
        "kullanici_kasasi",
    ]

    assert (
        sozlesme[
            "katmanlar_karismaz"
        ]
    )


def test_piyasa_tum_varliklari_tutar():
    evren = piyasa()

    assert len(
        evren.listele()
    ) == 3

    assert len(
        evren.listele(
            varlik_turu=(
                VarlikTuru.HISSE
            )
        )
    ) == 2


def test_kasa_yalniz_kullanici_varliklarini_tutar():
    kullanici_kasasi = kasa()

    assert (
        kullanici_kasasi.semboller()
        == {
            (
                "ASELS",
                VarlikTuru.HISSE,
            )
        }
    )


def test_kasa_ortalama_maliyet_ve_kar_zarar_hesaplar():
    ozet = kasa().varlik_ozeti(
        sembol="ASELS",
        varlik_turu=(
            VarlikTuru.HISSE
        ),
        guncel_fiyat=350,
    )

    assert (
        ozet.toplam_miktar
        == Decimal("30")
    )

    assert (
        ozet.ortalama_maliyet
        is not None
    )

    assert (
        ozet.guncel_deger
        == Decimal("10500.00")
    )

    assert (
        ozet.kar_zarar
        > 0
    )


def test_karsilastirma_kasada_olmayanlari_bulur():
    sonuc = (
        SyFinansCiftKatman(
            piyasa=piyasa(),
            kasa=kasa(),
        )
        .karsilastir()
    )

    assert (
        sonuc.kasada_olanlar
        == ("ASELS",)
    )

    assert set(
        sonuc
        .piyasada_olup_kasada_olmayanlar
    ) == {
        "THYAO",
        "USDTRY",
    }


def test_katmanlar_ayri_sha_uretir():
    evren = piyasa()
    kullanici_kasasi = kasa()

    assert len(
        evren.snapshot()["sha256"]
    ) == 64

    assert len(
        kullanici_kasasi
        .snapshot()["sha256"]
    ) == 64


def test_karsilastirma_muhurlenir():
    sonuc = (
        SyFinansCiftKatman(
            piyasa=piyasa(),
            kasa=kasa(),
        )
        .karsilastir()
    )

    assert len(
        sonuc.degerlendirme_sha256
    ) == 64

    assert (
        sonuc.as_dict()[
            "karar_yetkisi"
        ]
        == "Nihai karar kullanıcıya aittir."
    )