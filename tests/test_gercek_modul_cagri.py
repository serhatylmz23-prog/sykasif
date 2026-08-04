from syk_core.entegrasyon.gercek_modul_cagri import (
    GercekModulCagri,
)



def test_gercek_modul_akisi():

    sistem = GercekModulCagri(
        kanit=lambda x: "KANIT-" + x,
        goruntu=lambda x: "GOR-" + x,
        materyal=lambda x: "MAT-" + x,
        konsensus=lambda x: "KON-" + x,
    )


    sonuc = sistem.tum_akis(
        "001"
    )


    assert (
        sonuc["kanit"]
        ==
        "KANIT-001"
    )


    assert (
        sonuc["goruntu"]
        ==
        "GOR-001"
    )


    assert (
        sonuc["materyal"]
        ==
        "MAT-001"
    )


    assert (
        sonuc["konsensus"]
        ==
        "KON-001"
    )
