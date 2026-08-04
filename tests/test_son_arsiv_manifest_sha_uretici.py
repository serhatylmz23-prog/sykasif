from pathlib import Path

from syk_core.entegrasyon.son_arsiv_manifest_sha_uretici import (
    SonArsivManifestSHAUretici,
)



def test_son_arsiv_manifest_sha():

    sistem = SonArsivManifestSHAUretici()


    sonuc = sistem.olustur(

        "SYK-CORE-001",

        [

            {
                "adi":
                    "core.py",

                "icerik":
                    "SYK CORE",

            },

            {
                "adi":
                    "test.py",

                "icerik":
                    "TEST",

            },

        ],

        "test_arsiv",

    )


    assert (

        sonuc.durum

        ==

        "son_arsiv_manifest_hazir"

    )


    assert (

        sonuc.toplam_dosya

        ==

        2

    )


    assert (

        len(
            sonuc.kapanis_sha256
        )

        ==

        64

    )


    assert sistem.dogrula(
        sonuc
    ) is True



    Path(
        "test_arsiv/SHA256SUMS.txt"
    ).unlink()


    Path(
        "test_arsiv/manifest.json"
    ).unlink()


    Path(
        "test_arsiv"
    ).rmdir()
