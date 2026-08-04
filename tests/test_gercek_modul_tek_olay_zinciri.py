from syk_core.entegrasyon.gercek_modul_tek_olay_zinciri import (
    GercekModulTekOlayZinciri,
)

from syk_core.entegrasyon.cekirdek_orchestrator import (
    CekirdekDegerlendirmeOrkestratoru,
)

from syk_core.entegrasyon.tek_olay_core_motoru import (
    TekOlayCoreMotoru,
)



class Uzman:


    def incele(
        self,
        veri,
    ):
        return veri



class Konsensus:


    def hesapla(
        self,
        veri,
    ):
        return {
            "guven": 90,
            "konsensus": 90,
        }



class Fabrika:


    def olustur(
        self,
    ):

        from syk_core.entegrasyon.gercek_sinif_adaptoru import (
            GercekSinifAdaptoru,
        )

        return GercekSinifAdaptoru(
            Uzman(),
            Uzman(),
            Uzman(),
            Konsensus(),
        )



def test_gercek_modul_tek_olay_zinciri():

    cekirdek = (
        CekirdekDegerlendirmeOrkestratoru()
    )


    motor = TekOlayCoreMotoru(
        cekirdek,
        None,
    )


    zincir = GercekModulTekOlayZinciri(
        Fabrika(),
        motor,
    )


    sonuc = zincir.calistir(
        "OLAY-034",
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
