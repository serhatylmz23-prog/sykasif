from syk_core.entegrasyon.gercek_artefakt_envanteri import (
    GercekArtefaktEnvanteri,
)



def test_artefakt_envanteri():

    sistem = GercekArtefaktEnvanteri()


    sonuc = sistem.kaydet(

        "SYK_CORE_001.py",

        "kaynak_kod",

        "SPRINT-066",

    )


    assert (
        sonuc.durum
        ==
        "envantere_alindi"
    )


    assert (
        len(
            sonuc.sha256
        )
        ==
        64
    )


    assert (
        sistem.kontrol_et(
            "SYK_CORE_001.py"
        )
        is True
    )


    assert (
        sistem.toplam_getir()
        ==
        1
    )
