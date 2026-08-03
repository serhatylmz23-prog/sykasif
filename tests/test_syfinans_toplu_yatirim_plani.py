from decimal import Decimal

import pytest

from syk_finans_otagi.butce_dagilimi import (
    ButceDagilimMotoru,
)
from syk_finans_otagi.modeller import (
    VarlikTuru,
)
from syk_finans_otagi.portfoy_analizi import (
    Kanit,
    VarlikAdayi,
)
from syk_finans_otagi.toplu_yatirim_plani import (
    TopluYatirimPlaniMotoru,
)


def aday(
    sembol: str,
    *,
    guc: float = 85,
    risk: float = 30,
) -> VarlikAdayi:
    kanitlar = tuple(
        Kanit(
            kanit_id=f"{sembol}-{sira}",
            baslik=f"Kanıt {sira}",
            deger=guc,
            agirlik=1.0,
            kaynak=f"Kaynak {sira}",
            guncellik=(
                "2026-08-03T21:00:00+03:00"
            ),
            olumlu=True,
            aciklama=(
                "Doğrulanmış deneme kanıtı"
            ),
        )
        for sira in range(
            1,
            7,
        )
    )

    return VarlikAdayi(
        sembol=sembol,
        varlik_turu=VarlikTuru.HISSE,
        sektor=f"sektor-{sembol}",
        mevcut_fiyat=100,
        kanitlar=kanitlar,
        risk_puani=risk,
    )


def butce_plani():
    return ButceDagilimMotoru.dagit(
        toplam_butce=100_000,
        secilenler=[
            aday("ASELS"),
            aday(
                "THYAO",
                guc=80,
                risk=35,
            ),
        ],
        nakit_guvenlik_orani=10,
    )


def test_her_varlik_icin_kademeli_plan_uretilir():
    plan = (
        TopluYatirimPlaniMotoru
        .olustur(
            butce_dagilimi=(
                butce_plani()
            ),
            fiyat_kademeleri={
                "ASELS": [
                    300,
                    297,
                    293,
                    288,
                ],
                "THYAO": [
                    320,
                    315,
                    310,
                    304,
                ],
            },
        )
    )

    assert len(
        plan.varlik_planlari
    ) == 2

    assert all(
        len(
            varlik.kademe_plani
            .kademeler
        )
        == 4
        for varlik
        in plan.varlik_planlari
    )

    assert len(
        plan.toplu_plan_sha256
    ) == 64


def test_varlik_butcesi_asilmaz():
    dagilim = butce_plani()

    plan = (
        TopluYatirimPlaniMotoru
        .olustur(
            butce_dagilimi=dagilim,
            fiyat_kademeleri={
                "ASELS": [
                    300,
                    295,
                ],
                "THYAO": [
                    320,
                    310,
                ],
            },
        )
    )

    for varlik in plan.varlik_planlari:
        assert (
            varlik.kademe_plani
            .planlanan_tutar
            <= varlik.ayrilan_butce
        )


def test_kademe_gerceklesti_secilebilir():
    plan = (
        TopluYatirimPlaniMotoru
        .olustur(
            butce_dagilimi=(
                butce_plani()
            ),
            fiyat_kademeleri={
                "ASELS": [
                    300,
                    295,
                ],
                "THYAO": [
                    320,
                    310,
                ],
            },
        )
    )

    plan = (
        TopluYatirimPlaniMotoru
        .kademe_durumu_degistir(
            plan,
            sembol="ASELS",
            kademe_no=1,
            gerceklesti=True,
            gerceklesen_fiyat=299,
        )
    )

    asels = next(
        varlik
        for varlik
        in plan.varlik_planlari
        if varlik.sembol == "ASELS"
    )

    assert (
        asels.kademe_plani
        .kademeler[0]
        .gerceklesti
    )

    assert (
        asels.ortalama_maliyet
        == Decimal("299.00")
    )


def test_genel_gerceklesme_orani_hesaplanir():
    plan = (
        TopluYatirimPlaniMotoru
        .olustur(
            butce_dagilimi=(
                butce_plani()
            ),
            fiyat_kademeleri={
                "ASELS": [
                    300,
                    295,
                ],
                "THYAO": [
                    320,
                    310,
                ],
            },
        )
    )

    plan = (
        TopluYatirimPlaniMotoru
        .kademe_durumu_degistir(
            plan,
            sembol="ASELS",
            kademe_no=1,
            gerceklesti=True,
        )
    )

    assert (
        plan.gerceklesen_toplam_tutar
        > 0
    )

    assert (
        plan.toplam_gerceklesme_orani
        > 0
    )

    assert (
        plan.genel_basari_orani
        > 0
    )


def test_gerceklesmeyen_kademe_maliyete_girmez():
    plan = (
        TopluYatirimPlaniMotoru
        .olustur(
            butce_dagilimi=(
                butce_plani()
            ),
            fiyat_kademeleri={
                "ASELS": [
                    300,
                    290,
                ],
                "THYAO": [
                    320,
                    310,
                ],
            },
        )
    )

    plan = (
        TopluYatirimPlaniMotoru
        .kademe_durumu_degistir(
            plan,
            sembol="ASELS",
            kademe_no=1,
            gerceklesti=True,
            gerceklesen_fiyat=300,
        )
    )

    asels = next(
        varlik
        for varlik
        in plan.varlik_planlari
        if varlik.sembol == "ASELS"
    )

    assert (
        asels.ortalama_maliyet
        == Decimal("300.00")
    )


def test_eksik_fiyat_kademesi_reddedilir():
    with pytest.raises(
        KeyError,
        match="THYAO",
    ):
        (
            TopluYatirimPlaniMotoru
            .olustur(
                butce_dagilimi=(
                    butce_plani()
                ),
                fiyat_kademeleri={
                    "ASELS": [
                        300,
                        295,
                    ],
                },
            )
        )


def test_nihai_karar_kullaniciya_birakilir():
    plan = (
        TopluYatirimPlaniMotoru
        .olustur(
            butce_dagilimi=(
                butce_plani()
            ),
            fiyat_kademeleri={
                "ASELS": [
                    300,
                    295,
                ],
                "THYAO": [
                    320,
                    310,
                ],
            },
        )
    )

    assert (
        plan.as_dict()[
            "karar_yetkisi"
        ]
        == "Nihai karar kullanıcıya aittir."
    )