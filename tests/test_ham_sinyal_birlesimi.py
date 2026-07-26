import math
import pytest

from syk_simulasyon.ham_sinyal_birlesimi import (
    HamSinyalBirlesimMotoru,
    SimulasyonKimligiUretici,
    SinyalBileseni,
    ZamanEsleyici,
)


TEMEL = dict(
    arastirma_kimligi="AK-X7F2",
    deney_numarasi="DN-K9M4",
    ftsu_surumu="1.4.0",
    rastgele_tohum=42,
    parametre_ozeti={"derinlik_m": 1.2, "frekans_hz": 1000.0},
    olusturma_zamani_utc="2026-07-26T12:00:00+00:00",
)


def test_ayni_hizdaki_bilesenler_toplanir():
    sonuc = HamSinyalBirlesimMotoru().birlestir(
        [
            SinyalBileseni("ana", (1.0, 2.0, 3.0), 10.0),
            SinyalBileseni("yansima", (0.5, -0.5, 1.0), 10.0),
        ],
        **TEMEL,
    )
    assert sonuc.genlik == pytest.approx((1.5, 1.5, 4.0))
    assert sonuc.zaman_s == pytest.approx((0.0, 0.1, 0.2))


def test_farkli_ornekleme_hizlari_dogrusal_eslenir():
    sonuc = HamSinyalBirlesimMotoru().birlestir(
        [
            SinyalBileseni("yavas", (0.0, 2.0), 1.0),
            SinyalBileseni("hizli", (0.0, 0.0, 0.0), 2.0),
        ],
        hedef_ornekleme_hz=2.0,
        **TEMEL,
    )
    assert sonuc.genlik == pytest.approx((0.0, 1.0, 2.0))


def test_baslangic_zamani_farkli_bilesenler_hizalanir():
    sonuc = HamSinyalBirlesimMotoru().birlestir(
        [
            SinyalBileseni("a", (1.0, 1.0), 1.0, baslangic_s=0.0),
            SinyalBileseni("b", (2.0, 2.0), 1.0, baslangic_s=1.0),
        ],
        **TEMEL,
    )
    assert sonuc.zaman_s == pytest.approx((0.0, 1.0, 2.0))
    assert sonuc.genlik == pytest.approx((1.0, 3.0, 2.0))


def test_kirpma_siniri_uygulanir():
    sonuc = HamSinyalBirlesimMotoru().birlestir(
        [SinyalBileseni("a", (2.0, -3.0), 1.0)],
        kirpma_siniri=1.0,
        **TEMEL,
    )
    assert sonuc.genlik == (1.0, -1.0)


def test_ust_veri_eksiksizdir():
    sonuc = HamSinyalBirlesimMotoru().birlestir(
        [SinyalBileseni("a", (1.0, 2.0), 1.0)],
        **TEMEL,
    )
    assert sonuc.ust_veri.arastirma_kimligi == TEMEL["arastirma_kimligi"]
    assert sonuc.ust_veri.deney_numarasi == TEMEL["deney_numarasi"]
    assert sonuc.ust_veri.ftsu_surumu == "1.4.0"
    assert sonuc.ust_veri.rastgele_tohum == 42
    assert sonuc.ust_veri.simulasyon_kimligi.startswith("SIM-")


def test_ayni_girdi_ayni_simulasyon_kimligi_verir():
    a = SimulasyonKimligiUretici.uret(
        arastirma_kimligi="AK-A",
        deney_numarasi="DN-1",
        ftsu_surumu="1.4.0",
        rastgele_tohum=7,
        parametre_ozeti={"x": 1},
    )
    b = SimulasyonKimligiUretici.uret(
        arastirma_kimligi="AK-A",
        deney_numarasi="DN-1",
        ftsu_surumu="1.4.0",
        rastgele_tohum=7,
        parametre_ozeti={"x": 1},
    )
    assert a == b


def test_farkli_tohum_farkli_simulasyon_kimligi_verir():
    a = SimulasyonKimligiUretici.uret(
        arastirma_kimligi="AK-A", deney_numarasi="DN-1",
        ftsu_surumu="1.4.0", rastgele_tohum=1, parametre_ozeti={"x": 1},
    )
    b = SimulasyonKimligiUretici.uret(
        arastirma_kimligi="AK-A", deney_numarasi="DN-1",
        ftsu_surumu="1.4.0", rastgele_tohum=2, parametre_ozeti={"x": 1},
    )
    assert a != b


def test_zaman_ekseni_kesin_artandir():
    sonuc = HamSinyalBirlesimMotoru().birlestir(
        [SinyalBileseni("a", (1.0, 2.0, 3.0), 4.0)],
        **TEMEL,
    )
    assert all(b > a for a, b in zip(sonuc.zaman_s, sonuc.zaman_s[1:]))


def test_bos_bilesen_listesi_reddedilir():
    with pytest.raises(ValueError):
        HamSinyalBirlesimMotoru().birlestir([], **TEMEL)


def test_ayni_adli_bilesenler_reddedilir():
    with pytest.raises(ValueError):
        HamSinyalBirlesimMotoru().birlestir(
            [SinyalBileseni("a", (1.0,), 1.0), SinyalBileseni("a", (2.0,), 1.0)],
            **TEMEL,
        )


@pytest.mark.parametrize("dizi", [(), (math.nan,), (math.inf,)])
def test_gecersiz_sinyal_reddedilir(dizi):
    with pytest.raises(ValueError):
        SinyalBileseni("a", dizi, 1.0)


def test_gecersiz_ornekleme_hizi_reddedilir():
    with pytest.raises(ValueError):
        SinyalBileseni("a", (1.0,), 0.0)


def test_gecersiz_kirpma_siniri_reddedilir():
    with pytest.raises(ValueError):
        HamSinyalBirlesimMotoru().birlestir(
            [SinyalBileseni("a", (1.0,), 1.0)],
            kirpma_siniri=0.0,
            **TEMEL,
        )


def test_zaman_esleyici_aralik_disina_sifir_yazar():
    sonuc = ZamanEsleyici.yeniden_ornekle(
        SinyalBileseni("a", (1.0, 2.0), 1.0, baslangic_s=1.0),
        hedef_ornekleme_hz=1.0,
        hedef_baslangic_s=0.0,
        hedef_ornek_sayisi=4,
    )
    assert sonuc == (0.0, 1.0, 2.0, 0.0)


def test_tum_cikti_sonludur():
    sonuc = HamSinyalBirlesimMotoru().birlestir(
        [SinyalBileseni("a", (0.1, -0.2, 0.3), 10.0)],
        **TEMEL,
    )
    assert all(math.isfinite(x) for x in sonuc.genlik)
