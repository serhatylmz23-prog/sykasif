from syk_core.entegrasyon.cekirdek_orchestrator import (
    CekirdekDegerlendirmeOrkestratoru,
)

from syk_core.entegrasyon.tek_olay_core_motoru import (
    TekOlayCoreMotoru,
)



class SahteAdaptor:


    def kanit_incele(
        self,
        veri,
    ):
        return "KANIT"



    def goruntu_incele(
        self,
        veri,
    ):
        return "GORUNTU"



    def materyal_incele(
        self,
        veri,
    ):
        return "MATERYAL"



    def konsensus_hesapla(
        self,
        veri,
    ):
        return {
            "guven": 90,
            "konsensus": 90,
        }



def test_tek_olay_core_motoru():

    cekirdek = (
        CekirdekDegerlendirmeOrkestratoru()
    )


    motor = TekOlayCoreMotoru(
        cekirdek,
        SahteAdaptor(),
    )


    sonuc = motor.degerlendir(
        "OLAY-031",
        "VERI",
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
