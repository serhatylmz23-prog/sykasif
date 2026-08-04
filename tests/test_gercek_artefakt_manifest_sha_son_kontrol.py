from syk_core.entegrasyon.gercek_artefakt_manifest_sha_son_kontrol import (
    GercekArtefaktManifestSHASonKontrol,
)



def test_birlesik_son_kontrol():

    sistem = GercekArtefaktManifestSHASonKontrol()


    sonuc = sistem.kontrol_et(

        "SYK-CORE-001",

        True,

        True,

        True,

    )


    assert (
        sonuc.durum
        ==
        "birlesik_son_kontrol_tamam"
    )


    assert (
        sonuc.toplam_kontrol
        ==
        3
    )


    assert (
        sonuc.basarili_kontrol
        ==
        3
    )


    assert (
        sonuc.hatali_kontrol
        ==
        0
    )


    assert (
        len(
            sonuc.sonuc_sha256
        )
        ==
        64
    )


    assert sistem.dogrula(
        sonuc
    ) is True



def test_risk_tespiti():

    sistem = GercekArtefaktManifestSHASonKontrol()


    sonuc = sistem.kontrol_et(

        "SYK-CORE-001",

        True,

        False,

        True,

    )


    assert (
        sonuc.durum
        ==
        "inceleme_gerekli"
    )


    assert (
        "SHA"
        in
        sonuc.riskler
    )
