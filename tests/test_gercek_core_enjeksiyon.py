from syk_core.entegrasyon.cekirdek_orchestrator import (
    CekirdekDegerlendirmeOrkestratoru,
)

from syk_core.entegrasyon.gercek_core_enjeksiyon import (
    GercekCoreEnjeksiyon,
)



def test_gercek_core_enjeksiyon():

    cekirdek = (
        CekirdekDegerlendirmeOrkestratoru()
    )


    cekirdek.olay_baslat(
        "CORE-027"
    )


    sistem = GercekCoreEnjeksiyon(

        cekirdek,

        lambda x:
            "KANIT-" + x,

        lambda x:
            "GOR-" + x,

        lambda x:
            "MAT-" + x,

        lambda x:
            {
                "guven": 90,
                "konsensus": 90,
            },
    )


    sonuc = sistem.degerlendir(
        "CORE-027",
        "VERI",
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
