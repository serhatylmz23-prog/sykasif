from syk_core.entegrasyon.gercek_sinif_adaptoru import (
    GercekSinifAdaptoru,
)



class SahteUzman:


    def incele(
        self,
        veri,
    ):

        return veri + "-incelendi"



class SahteKonsensus:


    def hesapla(
        self,
        veri,
    ):

        return veri + "-puanlandi"



def test_gercek_sinif_adaptoru():

    adaptor = GercekSinifAdaptoru(
        SahteUzman(),
        SahteUzman(),
        SahteUzman(),
        SahteKonsensus(),
    )


    assert (
        adaptor.kanit_incele(
            "KANIT"
        )
        ==
        "KANIT-incelendi"
    )


    assert (
        adaptor.goruntu_incele(
            "GOR"
        )
        ==
        "GOR-incelendi"
    )


    assert (
        adaptor.materyal_incele(
            "MAT"
        )
        ==
        "MAT-incelendi"
    )


    assert (
        adaptor.konsensus_hesapla(
            "VERI"
        )
        ==
        "VERI-puanlandi"
    )
