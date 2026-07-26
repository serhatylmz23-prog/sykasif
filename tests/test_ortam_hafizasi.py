import pytest
from syk_simulasyon.ortam_hafizasi import (
    DeneyBilesimi, GokselZamansalBaglam, KontrolluDeneyBilesimUreticisi,
    OrtamHafizasi, OrtamKategorisi, OrtamOzelligi, OrtamProfili,
)


def ozellik(ad="nem", deger=0.2, guven=0.9, varsayim=False):
    return OrtamOzelligi(OrtamKategorisi.TOPRAK, ad, deger, "oran", "K-1", guven, varsayim)


def profil(kimlik="OP-1", konum="KON-001", ozellikler=None, baglam=None):
    return OrtamProfili(kimlik, konum, tuple(ozellikler or [ozellik()]), baglam)


def test_ortam_ozelligi_guven_araligi():
    with pytest.raises(ValueError):
        ozellik(guven=1.1)


def test_baglam_araligi():
    with pytest.raises(ValueError):
        GokselZamansalBaglam("2026-07-26T00:00:00Z", gunes_etkinligi=2)


def test_profil_guven_puani_varsayim_cezasi():
    p = profil(ozellikler=[ozellik(guven=0.9), ozellik("sicaklik", 22, 0.7, True)])
    assert p.guven_puani == 0.75


def test_profil_parmak_izi_kararli():
    p = profil()
    assert p.parmak_izi() == p.parmak_izi()


def test_hafiza_ekler_ve_gecmis_getirir():
    h = OrtamHafizasi(); p = profil()
    h.ekle(p)
    assert h.gecmis("KON-001") == (p,)
    assert h.son_profil("KON-001") == p


def test_hafiza_ayni_profili_reddeder():
    h = OrtamHafizasi(); p = profil()
    h.ekle(p)
    with pytest.raises(ValueError): h.ekle(p)


def test_deney_derinlik_siniri():
    with pytest.raises(ValueError): DeneyBilesimi("H", "O", 2.3, 5000)


def test_deney_frekans_pozitif():
    with pytest.raises(ValueError): DeneyBilesimi("H", "O", 1, 0)


def test_bilesim_ureticisi_kartesyen_uretir():
    u = KontrolluDeneyBilesimUreticisi()
    sonuc = u.uret(["H1", "H2"], ["O1"], [0.5, 1.0], [5000, 6000])
    assert len(sonuc) == 8


def test_bilesim_ureticisi_benzer_tekrari_atlar():
    u = KontrolluDeneyBilesimUreticisi()
    assert len(u.uret(["H1"], ["O1"], [1.0], [5000])) == 1
    assert len(u.uret(["H1"], ["O1"], [1.01], [5000.4])) == 0


def test_bilesim_ureticisi_sinir_korur():
    u = KontrolluDeneyBilesimUreticisi(en_fazla_senaryo=3)
    with pytest.raises(OverflowError): u.uret(["H1", "H2"], ["O1"], [1], [1,2])


def test_bos_ortam_profili_reddedilir():
    with pytest.raises(ValueError): OrtamProfili("P", "K", ())
