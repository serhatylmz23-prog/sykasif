from syk_core.entegrasyon.gercek_core_nesne_fabrikasi import (
    GercekCoreNesneFabrikasi,
)



class KanitUzmani:


    def incele(
        self,
        veri,
    ):
        return veri



class GoruntuUzmani:


    def incele(
        self,
        veri,
    ):
        return veri



class MateryalUzmani:


    def incele(
        self,
        veri,
    ):
        return veri



class KonsensusMotoru:


    def hesapla(
        self,
        veri,
    ):
        return veri



def test_gercek_core_nesne_fabrikasi():

    fabrika = GercekCoreNesneFabrikasi(
        KanitUzmani,
        GoruntuUzmani,
        MateryalUzmani,
        KonsensusMotoru,
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
