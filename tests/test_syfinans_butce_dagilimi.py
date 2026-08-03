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


def aday(
    sembol: str,
    *,
    guc: float,
    risk: float,
    agirlik: float = 0.0,
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
            aciklama="Doğrulanmış deneme kanıtı",
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
        mevcut_portfoyde=(
            agirlik > 0
        ),
        mevcut_agirlik=agirlik,
    )


def test_butce_secili_varliklara_dagitilir():
    plan = ButceDagilimMotoru.dagit(
        toplam_butce=100_000,
        secilenler=[
            aday(
                "ASELS",
                guc=90,
                risk=25,
            ),
            aday(
                "THYAO",
                guc=80,
                risk=35,
            ),
            aday(
                "FROTO",
                guc=75,
                risk=40,
            ),
        ],
        nakit_guvenlik_orani=10,
    )

    assert (
        plan.toplam_butce
        == Decimal("100000.00")
    )

    assert (
        plan.nakit_guvenlik_payi
        == Decimal("10000.00")
    )

    assert len(
        plan.paylar
    ) == 3

    assert (
        plan.kullanilan_tutar
        <= plan.yatirima_ayrilan_butce
    )

    assert len(
        plan.dagitim_sha256
    ) == 64


def test_guveni_yuksek_riski_dusuk_varlik_daha_fazla_pay_alir():
    plan = ButceDagilimMotoru.dagit(
        toplam_butce=50_000,
        secilenler=[
            aday(
                "GUCLU",
                guc=95,
                risk=15,
            ),
            aday(
                "ZAYIF",
                guc=60,
                risk=70,
            ),
        ],
        nakit_guvenlik_orani=0,
    )

    paylar = {
        pay.sembol: pay
        for pay in plan.paylar
    }

    assert (
        paylar["GUCLU"].ayrilan_tutar
        > paylar["ZAYIF"].ayrilan_tutar
    )


def test_kullanici_katsayisi_dagilimi_degistirir():
    normal = ButceDagilimMotoru.dagit(
        toplam_butce=40_000,
        secilenler=[
            aday(
                "A",
                guc=80,
                risk=30,
            ),
            aday(
                "B",
                guc=80,
                risk=30,
            ),
        ],
        nakit_guvenlik_orani=0,
    )

    tercihli = ButceDagilimMotoru.dagit(
        toplam_butce=40_000,
        secilenler=[
            aday(
                "A",
                guc=80,
                risk=30,
            ),
            aday(
                "B",
                guc=80,
                risk=30,
            ),
        ],
        nakit_guvenlik_orani=0,
        kullanici_katsayilari={
            "A": 2.0,
            "B": 1.0,
        },
    )

    normal_pay = {
        pay.sembol: pay.ayrilan_tutar
        for pay in normal.paylar
    }

    tercihli_pay = {
        pay.sembol: pay.ayrilan_tutar
        for pay in tercihli.paylar
    }

    assert (
        normal_pay["A"]
        == normal_pay["B"]
    )

    assert (
        tercihli_pay["A"]
        > tercihli_pay["B"]
    )


def test_yuksek_mevcut_agirlik_dagilimda_ceza_alir():
    plan = ButceDagilimMotoru.dagit(
        toplam_butce=60_000,
        secilenler=[
            aday(
                "NORMAL",
                guc=85,
                risk=25,
            ),
            aday(
                "YOGUN",
                guc=85,
                risk=25,
                agirlik=45,
            ),
        ],
        nakit_guvenlik_orani=0,
    )

    paylar = {
        pay.sembol: pay
        for pay in plan.paylar
    }

    assert (
        paylar["NORMAL"].ayrilan_tutar
        > paylar["YOGUN"].ayrilan_tutar
    )


def test_en_fazla_yedi_varlik_kabul_edilir():
    with pytest.raises(
        ValueError,
        match="En fazla 7",
    ):
        ButceDagilimMotoru.dagit(
            toplam_butce=100_000,
            secilenler=[
                aday(
                    f"VAR{sira}",
                    guc=80,
                    risk=30,
                )
                for sira in range(
                    8
                )
            ],
        )


def test_butce_asgari_tutari_karsilamazsa_reddedilir():
    with pytest.raises(
        ValueError,
        match="asgari tutar",
    ):
        ButceDagilimMotoru.dagit(
            toplam_butce=200,
            secilenler=[
                aday(
                    "A",
                    guc=80,
                    risk=30,
                ),
                aday(
                    "B",
                    guc=80,
                    risk=30,
                ),
            ],
            nakit_guvenlik_orani=50,
            minimum_varlik_tutari=100,
        )


def test_nihai_karar_kullaniciya_birakilir():
    plan = ButceDagilimMotoru.dagit(
        toplam_butce=10_000,
        secilenler=[
            aday(
                "ASELS",
                guc=85,
                risk=25,
            )
        ],
    )

    assert (
        plan.as_dict()["karar_yetkisi"]
        == "Nihai karar kullanıcıya aittir."
    )