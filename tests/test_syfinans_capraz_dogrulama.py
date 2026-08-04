from dataclasses import replace
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from syk_finans_otagi.capraz_dogrulama import (
    CaprazDogrulamaMotoru,
    DogrulamaDurumu,
    KaynakGuvenProfili,
    KaynakliPiyasaVerisi,
    KaynakTuru,
)
from syk_finans_otagi.modeller import (
    VarlikTuru,
    VeriAkisDurumu,
)
from syk_finans_otagi.veri_saglayicilari import (
    PiyasaVerisi,
    VeriDogruLamaMotoru,
)


ZAMAN = datetime.now(
    UTC
).isoformat()


def guven_profili(
    saglayici_id: str,
    *,
    guven: float = 90,
) -> KaynakGuvenProfili:
    return KaynakGuvenProfili(
        saglayici_id=saglayici_id,
        kaynak_turu=(
            KaynakTuru.LISANSLI_PIYASA
        ),
        temel_guven_puani=guven,
        guncellik_puani=guven,
        gecmis_tutarlilik_puani=guven,
        kesinti_dayanim_puani=80,
        lisansli=True,
        resmi=False,
    )


def piyasa_verisi(
    saglayici_id: str,
    fiyat: float,
    *,
    zaman: str = ZAMAN,
    durum: VeriAkisDurumu = (
        VeriAkisDurumu.ANLIK
    ),
) -> PiyasaVerisi:
    veri = PiyasaVerisi(
        sembol="ASELS",
        varlik_turu=(
            VarlikTuru.HISSE
        ),
        fiyat=Decimal(
            str(fiyat)
        ),
        para_birimi="TRY",
        zaman_damgasi=zaman,
        kaynak=(
            f"{saglayici_id} kaynağı"
        ),
        saglayici_id=saglayici_id,
        veri_durumu=durum,
        dogrulandi=True,
    )

    return (
        VeriDogruLamaMotoru
        .muhurle(veri)
    )


def kaynakli(
    saglayici_id: str,
    fiyat: float,
    *,
    guven: float = 90,
    durum: VeriAkisDurumu = (
        VeriAkisDurumu.ANLIK
    ),
) -> KaynakliPiyasaVerisi:
    return KaynakliPiyasaVerisi(
        veri=piyasa_verisi(
            saglayici_id,
            fiyat,
            durum=durum,
        ),
        guven_profili=(
            guven_profili(
                saglayici_id,
                guven=guven,
            )
        ),
    )


def test_yakin_fiyatlar_capraz_dogrulanir():
    sonuc = (
        CaprazDogrulamaMotoru
        .dogrula(
            veriler=[
                kaynakli(
                    "kaynak-a",
                    300.00,
                ),
                kaynakli(
                    "kaynak-b",
                    300.20,
                ),
                kaynakli(
                    "kaynak-c",
                    299.90,
                ),
            ],
            azami_fiyat_farki_orani=1.0,
            asgari_dogrulama_kaynagi=2,
        )
    )

    assert (
        sonuc.dogrulama_durumu
        == DogrulamaDurumu.DOGRULANDI
    )

    assert (
        sonuc.kabul_edilen_kaynak_sayisi
        == 3
    )

    assert (
        Decimal("299.90")
        <= sonuc.uzlasma_fiyati
        <= Decimal("300.20")
    )

    assert len(
        sonuc.dogrulama_sha256
    ) == 64


def test_uzak_fiyatli_kaynak_reddedilir():
    sonuc = (
        CaprazDogrulamaMotoru
        .dogrula(
            veriler=[
                kaynakli(
                    "kaynak-a",
                    300.00,
                ),
                kaynakli(
                    "kaynak-b",
                    300.10,
                ),
                kaynakli(
                    "kaynak-hatali",
                    340.00,
                ),
            ],
            azami_fiyat_farki_orani=2.0,
        )
    )

    assert (
        sonuc.kabul_edilen_kaynak_sayisi
        == 2
    )

    assert (
        sonuc.reddedilen_kaynak_sayisi
        == 1
    )

    hatali = next(
        kayit
        for kayit
        in sonuc.karsilastirmalar
        if kayit.saglayici_id
        == "kaynak-hatali"
    )

    assert not (
        hatali.kabul_edildi
    )

    assert (
        "Fiyat farkı"
        in hatali.ret_nedeni
    )


def test_guveni_dusuk_kaynak_reddedilir():
    sonuc = (
        CaprazDogrulamaMotoru
        .dogrula(
            veriler=[
                kaynakli(
                    "kaynak-a",
                    300.00,
                ),
                kaynakli(
                    "kaynak-b",
                    300.10,
                    guven=20,
                ),
            ],
            asgari_kaynak_guven_puani=50,
        )
    )

    assert (
        sonuc.kabul_edilen_kaynak_sayisi
        == 1
    )

    assert (
        sonuc.dogrulama_durumu
        == DogrulamaDurumu
        .KISMEN_DOGRULANDI
    )


def test_gecikmeli_kaynak_akis_durumuna_yansir():
    sonuc = (
        CaprazDogrulamaMotoru
        .dogrula(
            veriler=[
                kaynakli(
                    "kaynak-a",
                    300,
                ),
                kaynakli(
                    "kaynak-b",
                    300.10,
                    durum=(
                        VeriAkisDurumu
                        .GECIKMELI
                    ),
                ),
            ],
        )
    )

    assert (
        sonuc.veri_akis_durumu
        == VeriAkisDurumu.GECIKMELI
    )


def test_farkli_semboller_birlikte_dogrulanamaz():
    ilk = kaynakli(
        "kaynak-a",
        300,
    )

    ikinci_veri = replace(
        piyasa_verisi(
            "kaynak-b",
            300,
        ),
        sembol="THYAO",
        veri_sha256="",
    )

    ikinci_veri = (
        VeriDogruLamaMotoru
        .muhurle(
            ikinci_veri
        )
    )

    ikinci = KaynakliPiyasaVerisi(
        veri=ikinci_veri,
        guven_profili=(
            guven_profili(
                "kaynak-b"
            )
        ),
    )

    with pytest.raises(
        ValueError,
        match="Farklı sembollere",
    ):
        (
            CaprazDogrulamaMotoru
            .dogrula(
                veriler=[
                    ilk,
                    ikinci,
                ]
            )
        )


def test_ayni_saglayici_tekrarlanamaz():
    with pytest.raises(
        ValueError,
        match="Aynı sağlayıcı",
    ):
        (
            CaprazDogrulamaMotoru
            .dogrula(
                veriler=[
                    kaynakli(
                        "kaynak-a",
                        300,
                    ),
                    kaynakli(
                        "kaynak-a",
                        300.10,
                    ),
                ]
            )
        )


def test_muhursuz_veri_kabul_edilmez():
    veri = PiyasaVerisi(
        sembol="ASELS",
        varlik_turu=(
            VarlikTuru.HISSE
        ),
        fiyat=Decimal("300"),
        para_birimi="TRY",
        zaman_damgasi=ZAMAN,
        kaynak="Deneme",
        saglayici_id="kaynak-a",
        veri_durumu=(
            VeriAkisDurumu.ANLIK
        ),
        dogrulandi=False,
    )

    with pytest.raises(
        ValueError,
        match="mühürlü",
    ):
        KaynakliPiyasaVerisi(
            veri=veri,
            guven_profili=(
                guven_profili(
                    "kaynak-a"
                )
            ),
        )


def test_kesinlik_iddiasi_yapilmaz():
    sonuc = (
        CaprazDogrulamaMotoru
        .dogrula(
            veriler=[
                kaynakli(
                    "kaynak-a",
                    300,
                ),
                kaynakli(
                    "kaynak-b",
                    300.10,
                ),
            ]
        )
    )

    assert (
        "kesinlik iddiası taşımaz"
        in sonuc.as_dict()[
            "kesinlik_uyarisi"
        ]
    )