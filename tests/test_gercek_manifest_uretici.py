from syk_core.entegrasyon.gercek_manifest_uretici import (
    GercekManifestUretici,
)



def test_gercek_manifest():

    sistem = GercekManifestUretici()


    artefaktlar = [

        {
            "dosya":
                "SYK_CORE_001.py",

            "sha256":
                "a" * 64,

            "boyut":
                100,

        },

        {
            "dosya":
                "test_core.py",

            "sha256":
                "b" * 64,

            "boyut":
                200,

        },

    ]


    sonuc = sistem.manifest_uret(

        "SYK-CORE-001",

        artefaktlar,

    )


    assert (
        sonuc.durum
        ==
        "gercek_manifest_uretildi"
    )


    assert (
        sonuc.artefakt_sayisi
        ==
        2
    )


    assert (
        len(
            sonuc.manifest_sha256
        )
        ==
        64
    )


    assert (
        sistem.dogrula(
            "SYK-CORE-001",
            artefaktlar,
        )
        is True
    )
