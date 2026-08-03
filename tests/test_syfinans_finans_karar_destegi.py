from decimal import Decimal

import pytest

from syk_finans_otagi.finans_karar_destegi import (
    KademeTuru,
    KararYonelimi,
    SyFinansKararDestekMotoru,
    VarlikAdayi,
    YatirimSecimTuru,
)
from syk_finans_otagi.modeller import (
    VarlikTuru,
)


def aday(
    sembol: str,
    *,
    fiyat: str = "300",
    guven: float = 85,
    kanit: float = 88,
    risk: float = 30,
    davranis: float = 80,
    trend: float = 82,
    secildi: bool = False,
) -> VarlikAdayi:
    return VarlikAdayi(
        sembol=sembol,
        varlik_turu=(
            VarlikTuru.HISSE
        ),
        guncel_fiyat=Decimal(
            fiyat
        ),
        guven_puani=guven,
        kanit_gucu=kanit,
        risk_puani=risk,
        piyasa_davranis_puani=(
            davranis
        ),
        kap_etki_puani=75,
        trend_puani=trend,
        kullanici_secimi=secildi,
    )


def test_karar_puani_ve_yonelim_hesaplanir():
    sonuc = aday(
        "ASELS"
    )

    assert (
        sonuc.karar_puani
        >= 80
    )

    assert (
        sonuc.yonelim
        == KararYonelimi.GUCLU_ADAY
    )


def test_adaylar_en_fazla_yedi_olarak_siralanir():
    motor = (
        SyFinansKararDestekMotoru()
    )

    adaylar = [
        aday(
            f"HISSE-{sira}",
            guven=70 + sira,
        )
        for sira in range(10)
    ]

    sonuc = motor.adaylari_sirala(
        adaylar=adaylar,
        secim_turu=(
            YatirimSecimTuru.SERBEST
        ),
        en_fazla_aday=7,
    )

    assert len(
        sonuc
    ) == 7

    assert (
        sonuc[0].karar_puani
        >= sonuc[-1].karar_puani
    )


def test_kullanici_secimi_filtrelenir():
    motor = (
        SyFinansKararDestekMotoru()
    )

    sonuc = motor.adaylari_sirala(
        adaylar=[
            aday(
                "ASELS",
                secildi=True,
            ),
            aday(
                "THYAO",
                secildi=False,
            ),
        ],
        secim_turu=(
            YatirimSecimTuru
            .KULLANICI_SECIMI
        ),
    )

    assert [
        kayit.sembol
        for kayit in sonuc
    ] == [
        "ASELS"
    ]


def test_butce_karar_puanina_gore_dagitilir():
    motor = (
        SyFinansKararDestekMotoru()
    )

    plan = motor.butce_dagit(
        toplam_butce=100000,
        adaylar=[
            aday(
                "ASELS",
                fiyat="300",
            ),
            aday(
                "THYAO",
                fiyat="400",
                guven=78,
                kanit=80,
                risk=40,
            ),
        ],
        secim_turu=(
            YatirimSecimTuru.SERBEST
        ),
    )

    assert len(
        plan.kayitlar
    ) == 2

    assert (
        plan.kayitlar[0]
        .ayrilan_butce
        >= plan.kayitlar[1]
        .ayrilan_butce
    )

    assert len(
        plan.plan_sha256
    ) == 64


def test_kademeli_alim_plani_uretilir():
    motor = (
        SyFinansKararDestekMotoru()
    )

    plan = motor.kademe_plani_olustur(
        plan_id="PLAN-001",
        sembol="ASELS",
        kademe_turu=(
            KademeTuru.ALIM
        ),
        fiyatlar=[
            300,
            297,
            293,
            288,
        ],
        toplam_butce=80000,
    )

    assert len(
        plan.kademeler
    ) == 4

    assert (
        plan.kademeler[0]
        .ayrilan_tutar
        == Decimal("20000.0000")
    )

    assert (
        plan.ortalama_maliyet
        is None
    )


def test_gerceklesen_kademeler_ortalama_maliyeti_degistirir():
    motor = (
        SyFinansKararDestekMotoru()
    )

    plan = motor.kademe_plani_olustur(
        plan_id="PLAN-002",
        sembol="ASELS",
        kademe_turu=(
            KademeTuru.ALIM
        ),
        fiyatlar=[
            300,
            297,
            293,
            288,
        ],
        toplam_butce=80000,
        gerceklesen_siralar=[
            1,
            2,
        ],
    )

    assert (
        plan.gerceklesen_adet
        > 0
    )

    assert (
        plan.ortalama_maliyet
        is not None
    )

    assert (
        plan.gerceklesme_orani
        == 50.0
    )

    assert len(
        plan.plan_sha256
    ) == 64


def test_kasif_finans_yorumu_kanitli_uretilir():
    motor = (
        SyFinansKararDestekMotoru()
    )

    yorum = motor.kasif_yorumu_uret(
        aday=aday(
            "ASELS"
        )
    )

    assert (
        yorum.yonelim
        == KararYonelimi.GUCLU_ADAY
    )

    assert len(
        yorum.kanit_ozeti
    ) == 5

    assert (
        "Nihai karar kullanıcıya aittir"
        in yorum.kesinlik_uyarisi
    )

    assert len(
        yorum.yorum_sha256
    ) == 64


def test_gecersiz_aday_sayisi_reddedilir():
    motor = (
        SyFinansKararDestekMotoru()
    )

    with pytest.raises(
        ValueError,
        match="1–7",
    ):
        motor.adaylari_sirala(
            adaylar=[
                aday("ASELS")
            ],
            secim_turu=(
                YatirimSecimTuru.SERBEST
            ),
            en_fazla_aday=8,
        )