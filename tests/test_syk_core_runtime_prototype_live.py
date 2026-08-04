from __future__ import annotations

from pathlib import Path

import pytest

from syk_core.runtime_prototype import (
    PrototipBaslatmaSecenekleri,
    PrototipBaslaticisi,
    PrototipCanliDogrulayici,
    guvenlik_ayarlari_ortamdan,
    json_istegi,
    prototip_ayarlari_olustur,
)


def ortam() -> dict[str, str]:
    return {
        "SYK_ANA_MASAUSTU_ANAHTARI": (
            "MASAUSTU-ANAHTARI"
        ),
        "SYK_SAMSUNG_TABLET_ANAHTARI": (
            "TABLET-ANAHTARI"
        ),
        "SYK_IPHONE_ANAHTARI": (
            "IPHONE-ANAHTARI"
        ),
        "SYK_SAHA_ANA_GIZLI_DEGERI": (
            "SAHA-ANA-GIZLI-DEGERI"
        ),
    }


def dogrulayici_olustur(
    tmp_path: Path,
) -> PrototipCanliDogrulayici:
    ayarlar = prototip_ayarlari_olustur(
        guvenlik=(
            guvenlik_ayarlari_ortamdan(
                ortam()
            )
        ),
        secenekler=(
            PrototipBaslatmaSecenekleri(
                ana_makine="127.0.0.1",
                baglanti_noktasi=0,
                durum_dosyasi=str(
                    tmp_path
                    / "canli_durum.json"
                ),
            )
        ),
    )

    return PrototipCanliDogrulayici(
        PrototipBaslaticisi(
            ayarlar=ayarlar
        )
    )


def test_canli_terminal_yolu_dogrulanir(
    tmp_path: Path,
) -> None:
    dogrulayici = dogrulayici_olustur(
        tmp_path
    )

    sonuc = dogrulayici.dogrula()

    yollar = {
        kayit["yol"]: kayit
        for kayit in sonuc["yollar"]
    }

    assert yollar[
        "/terminal"
    ][
        "durum_kodu"
    ] == 200


def test_canli_cihaz_iletisimi_dogrulanir(
    tmp_path: Path,
) -> None:
    sonuc = dogrulayici_olustur(
        tmp_path
    ).dogrula()

    yollar = {
        kayit["yol"]: kayit
        for kayit in sonuc["yollar"]
    }

    assert yollar[
        "/cihaz-iletisimi/saglik"
    ][
        "başarılı"
    ] is True


def test_canli_saha_cihazlari_dogrulanir(
    tmp_path: Path,
) -> None:
    sonuc = dogrulayici_olustur(
        tmp_path
    ).dogrula()

    yollar = {
        kayit["yol"]: kayit
        for kayit in sonuc["yollar"]
    }

    assert yollar[
        "/saha-cihazlari/saglik"
    ][
        "başarılı"
    ] is True


def test_canli_dogrulama_sonunda_sunucu_kapanir(
    tmp_path: Path,
) -> None:
    dogrulayici = dogrulayici_olustur(
        tmp_path
    )

    sonuc = dogrulayici.dogrula()

    assert sonuc["başarılı"] is True
    assert (
        dogrulayici
        .baslatici
        .calisiyor_mu
        is False
    )


def test_gercek_islem_kapali_kalir(
    tmp_path: Path,
) -> None:
    sonuc = dogrulayici_olustur(
        tmp_path
    ).dogrula()

    assert sonuc[
        "gerçek_işlem"
    ] is False


def test_iki_kez_kapatma_guvenlidir(
    tmp_path: Path,
) -> None:
    sonuc = (
        dogrulayici_olustur(
            tmp_path
        )
        .kapanis_dayanikliligini_dogrula()
    )

    assert sonuc[
        "ilk_kapanış"
    ] is True

    assert sonuc[
        "ikinci_kapanış"
    ] is True


def test_json_istegi_canli_sunucuyu_okur(
    tmp_path: Path,
) -> None:
    dogrulayici = dogrulayici_olustur(
        tmp_path
    )

    adres = (
        dogrulayici
        .baslatici
        .baslat()
    )

    try:
        durum, veri = json_istegi(
            adres
            + "/saha-cihazlari/saglik"
        )

        assert durum == 200
        assert veri[
            "durum"
        ] == "sağlıklı"

    finally:
        dogrulayici.baslatici.durdur()
