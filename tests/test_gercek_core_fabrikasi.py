from syk_core.entegrasyon.cekirdek_orchestrator import (
    CekirdekDegerlendirmeOrkestratoru,
)

from syk_core.entegrasyon.gercek_core_fabrikasi import (
    GercekCoreFabrikasi,
)



def test_gercek_core_fabrikasi():

    cekirdek = (
        CekirdekDegerlendirmeOrkestratoru()
    )


    fabrika = (
        GercekCoreFabrikasi(
            cekirdek
        )
    )


    sistem = fabrika.olustur(
        lambda x: "KANIT-" + x,
        lambda x: "GOR-" + x,
        lambda x: "MAT-" + x,
        lambda x: {
            "guven": 90,
            "konsensus": 90,
        },
    )


    assert (
        sistem.kanit
        is not None
    )


    assert (
        sistem.goruntu
        is not None
    )


    assert (
        sistem.materyal
        is not None
    )


    assert (
        sistem.konsensus
        is not None
    )
