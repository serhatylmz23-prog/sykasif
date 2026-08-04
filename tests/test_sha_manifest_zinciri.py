from syk_core.entegrasyon.sha_manifest_zinciri import (
    SHAManifestZinciri,
)



def test_sha_manifest_zinciri():

    sistem = SHAManifestZinciri()



    ilk = sistem.yeni_versiyon_olustur(
        "KANIT-041",
        {
            "veri": "ilk"
        },
    )


    ikinci = sistem.yeni_versiyon_olustur(
        "KANIT-041",
        {
            "veri": "ikinci"
        },
    )


    assert (
        ilk.versiyon
        ==
        1
    )


    assert (
        ikinci.versiyon
        ==
        2
    )


    assert (
        ikinci.onceki_hash
        ==
        ilk.yeni_hash
    )


    assert (
        sistem.zincir_dogrula(
            "KANIT-041"
        )
        is True
    )
