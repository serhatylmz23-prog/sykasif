from syk_core.entegrasyon.gercek_repo_artefakt_zinciri import (
    GercekRepoArtefaktZinciri,
)



def test_repo_artefakt_zinciri():

    sistem = GercekRepoArtefaktZinciri()


    sonuc = sistem.tara(
        "src"
    )


    assert (
        isinstance(
            sonuc,
            list,
        )
    )



def test_manifest_uretimi():

    sistem = GercekRepoArtefaktZinciri()

    sistem.kayitlar = []


    sonuc = sistem.zincir_olustur()


    assert (
        sonuc.durum
        ==
        "gercek_repo_zinciri_hazir"
    )


    assert (
        len(
            sonuc.manifest_sha256
        )
        ==
        64
    )
