from syk_core.entegrasyon.cekirdek_orchestrator import (
    CekirdekDegerlendirmeOrkestratoru,
)

from syk_core.entegrasyon.gercek_modul_baglayici import (
    GercekModulBaglayici,
)



def test_gercek_moduller_baglanir():

    cekirdek = (
        CekirdekDegerlendirmeOrkestratoru()
    )


    cekirdek.olay_baslat(
        "SPRINT-025"
    )


    baglayici = (
        GercekModulBaglayici(
            cekirdek
        )
    )


    baglayici.kanit_modulu_bagla(
        "SPRINT-025",
        "KANIT",
    )


    baglayici.goruntu_modulu_bagla(
        "SPRINT-025",
        "GORUNTU",
    )


    baglayici.materyal_modulu_bagla(
        "SPRINT-025",
        "MATERYAL",
    )


    baglayici.guven_konsensus_bagla(
        "SPRINT-025",
        90,
        85,
    )


    sonuc = (
        baglayici.sonucu_al(
            "SPRINT-025"
        )
    )


    assert len(
        sonuc.kanitlar
    ) == 1


    assert len(
        sonuc.goruntu_sonuclari
    ) == 1


    assert (
        sonuc.durum
        ==
        "guclu_destek"
    )
