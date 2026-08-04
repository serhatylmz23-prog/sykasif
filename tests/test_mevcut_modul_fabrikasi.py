from syk_core.entegrasyon.mevcut_modul_fabrikasi import (
    MevcutModulFabrikasi,
)



class GercekKanit:


    def incele(
        self,
        veri,
    ):
        return "KANIT"



class GercekGoruntu:


    def incele(
        self,
        veri,
    ):
        return "GORUNTU"



class GercekMateryal:


    def incele(
        self,
        veri,
    ):
        return "MATERYAL"



class GercekKonsensus:


    def hesapla(
        self,
        veri,
    ):
        return {
            "guven": 90,
            "konsensus": 90,
        }



def test_mevcut_modul_fabrikasi():

    fabrika = MevcutModulFabrikasi(
        GercekKanit,
        GercekGoruntu,
        GercekMateryal,
        GercekKonsensus,
    )


    adaptor = fabrika.olustur()


    assert (
        adaptor.kanit_uzmani
        is not None
    )


    assert (
        adaptor.goruntu_uzmani
        is not None
    )


    assert (
        adaptor.materyal_uzmani
        is not None
    )


    assert (
        adaptor.konsensus_motoru
        is not None
    )
