from syk_core.entegrasyon.teslim_muhur_zinciri import (
    TeslimMuhurZinciri,
)



def test_teslim_muhur_zinciri():


    sistem = TeslimMuhurZinciri()



    sonuc = sistem.teslim_olustur(

        "OLAY-048",

        "KANIT-HASH",

        "RAPOR-HASH",

        "MANIFEST-HASH",

    )



    assert len(
        sonuc.teslim_kimligi
    ) == 64



    assert (
        sonuc.durum
        ==
        "teslim_muhurlendi"
    )



    assert sistem.dogrula(
        "OLAY-048"
    ) is True
