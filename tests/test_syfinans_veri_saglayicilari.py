from decimal import Decimal

import pytest

from syk_finans_otagi.modeller import (
    VarlikTuru,
    VeriAkisDurumu,
)
from syk_finans_otagi.veri_saglayicilari import (
    DenemeVeriSaglayici,
    FinansVeriKapisi,
    SonGuvenilirVeriDeposu,
    VeriDogruLamaMotoru,
)


def saglayici(
    *,
    hata_uret: bool = False,
    durum: VeriAkisDurumu = (
        VeriAkisDurumu.ANLIK
    ),
    gecikme: int = 0,
):
    return DenemeVeriSaglayici(
        veriler={
            (
                "ASELS",
                VarlikTuru.HISSE,
            ): 300.25,
            (
                "USDTRY",
                VarlikTuru.DOVIZ,
            ): 40.10,
            (
                "ALTIN",
                VarlikTuru.ALTIN,
            ): 4500,
        },
        veri_durumu=durum,
        gecikme_saniyesi=gecikme,
        hata_uret=hata_uret,
    )


def test_anlik_piyasa_verisi_alinir():
    kapi = FinansVeriKapisi(
        saglayicilar=[
            saglayici()
        ]
    )

    sonuc = kapi.veri_getir(
        sembol="ASELS",
        varlik_turu=(
            VarlikTuru.HISSE
        ),
    )

    assert (
        sonuc.veri.fiyat
        == Decimal("300.2500")
    )

    assert (
        sonuc.veri.veri_durumu
        == VeriAkisDurumu.ANLIK
    )

    assert (
        sonuc.ana_saglayici_kullanildi
    )

    assert len(
        sonuc.veri.veri_sha256
    ) == 64


def test_gecikmeli_veri_durumu_gosterilir():
    kapi = FinansVeriKapisi(
        saglayicilar=[
            saglayici(
                durum=(
                    VeriAkisDurumu
                    .GECIKMELI
                ),
                gecikme=900,
            )
        ]
    )

    sonuc = kapi.veri_getir(
        sembol="ASELS",
        varlik_turu=(
            VarlikTuru.HISSE
        ),
    )

    assert (
        sonuc.veri.veri_durumu
        == VeriAkisDurumu.GECIKMELI
    )

    assert (
        "15.0 dakika"
        in sonuc.veri.guncellik.aciklama
    )


def test_veri_muhru_dogrulanir():
    veri = saglayici().veri_getir(
        sembol="ASELS",
        varlik_turu=(
            VarlikTuru.HISSE
        ),
    )

    assert (
        VeriDogruLamaMotoru
        .dogrula(veri)
    )


def test_canli_baglanti_kesilince_son_guvenilir_veri_kullanilir():
    depo = SonGuvenilirVeriDeposu()

    ilk_kapi = FinansVeriKapisi(
        saglayicilar=[
            saglayici()
        ],
        depo=depo,
    )

    ilk_kapi.veri_getir(
        sembol="ASELS",
        varlik_turu=(
            VarlikTuru.HISSE
        ),
    )

    kesik_kapi = FinansVeriKapisi(
        saglayicilar=[
            saglayici(
                hata_uret=True
            )
        ],
        depo=depo,
    )

    sonuc = kesik_kapi.veri_getir(
        sembol="ASELS",
        varlik_turu=(
            VarlikTuru.HISSE
        ),
    )

    assert (
        sonuc
        .son_guvenilir_veri_kullanildi
    )

    assert not (
        sonuc.ana_saglayici_kullanildi
    )

    assert (
        sonuc.veri.veri_durumu
        == VeriAkisDurumu.CEVRIMDISI
    )

    assert (
        "Çevrimdışı görünüm"
        in sonuc.veri.guncellik.aciklama
    )


def test_canli_ve_yedek_veri_yoksa_hata_uretilir():
    kapi = FinansVeriKapisi(
        saglayicilar=[
            saglayici(
                hata_uret=True
            )
        ]
    )

    with pytest.raises(
        ConnectionError,
        match="son güvenilir",
    ):
        kapi.veri_getir(
            sembol="ASELS",
            varlik_turu=(
                VarlikTuru.HISSE
            ),
        )


def test_hisse_doviz_ve_altin_verisi_desteklenir():
    kapi = FinansVeriKapisi(
        saglayicilar=[
            saglayici()
        ]
    )

    for sembol, tur in (
        (
            "ASELS",
            VarlikTuru.HISSE,
        ),
        (
            "USDTRY",
            VarlikTuru.DOVIZ,
        ),
        (
            "ALTIN",
            VarlikTuru.ALTIN,
        ),
    ):
        sonuc = kapi.veri_getir(
            sembol=sembol,
            varlik_turu=tur,
        )

        assert (
            sonuc.veri.sembol
            == sembol
        )


def test_ayni_saglayici_kimligi_tekrarlanamaz():
    with pytest.raises(
        ValueError,
        match="Aynı sağlayıcı",
    ):
        FinansVeriKapisi(
            saglayicilar=[
                saglayici(),
                saglayici(),
            ]
        )