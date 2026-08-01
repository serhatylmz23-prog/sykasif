from syk_core.entegrasyon.cekirdek_orchestrator import (
    CekirdekDegerlendirmeOrkestratoru,
)


def test_tam_cekirdek_akisi():

    sistem = (
        CekirdekDegerlendirmeOrkestratoru()
    )


    sistem.olay_baslat(
        "CORE-024"
    )


    sistem.kanit_aktar(
        "CORE-024",
        "KANIT",
    )


    sistem.goruntu_aktar(
        "CORE-024",
        "GORUNTU",
    )


    sistem.materyal_aktar(
        "CORE-024",
        "MATERYAL",
    )


    sistem.puanlari_aktar(
        "CORE-024",
        90,
        90,
    )


    sonuc = sistem.tamamla(
        "CORE-024"
    )


    assert len(
        sonuc.kanitlar
    ) == 1


    assert len(
        sonuc.goruntu_sonuclari
    ) == 1


    assert len(
        sonuc.materyal_sonuclari
    ) == 1


    assert (
        sonuc.durum
        ==
        "guclu_destek"
    )
