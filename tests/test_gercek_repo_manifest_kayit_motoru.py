from pathlib import Path

from syk_core.entegrasyon.gercek_repo_manifest_kayit_motoru import (
    GercekRepoManifestKayitMotoru,
)



def test_manifest_kalici_kayit():

    sistem = GercekRepoManifestKayitMotoru()


    sonuc = sistem.manifest_uret(

        "SYK-CORE-001",

        [
            {
                "dosya":
                    "ornek.py",

                "sha256":
                    "a" * 64,

            }

        ],

        "test_manifest/manifest.json",

    )


    assert (
        sonuc.durum
        ==
        "kalici_manifest_uretildi"
    )


    assert (
        len(
            sonuc.manifest_sha256
        )
        ==
        64
    )


    assert sistem.dogrula(
        sonuc
    ) is True



    Path(
        "test_manifest/manifest.json"
    ).unlink()


    Path(
        "test_manifest"
    ).rmdir()
