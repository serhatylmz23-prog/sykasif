from syk_core.entegrasyon.rapor_paketi_sha_muhur import (
    RaporPaketiSHAMuhur,
)



def test_rapor_paketi_sha_muhur():


    sistem = RaporPaketiSHAMuhur()



    paket = {

        "kanitlar": [
            "KANIT-047"
        ],

        "uzmanlar": [
            "GORUNTU",
            "MATERYAL"
        ],

        "karar": "guclu_destek",

        "guven": 92,

    }



    sonuc = sistem.muhurle(
        "RAPOR-047",
        paket,
    )



    assert len(
        sonuc.paket_hashi
    ) == 64



    assert sistem.dogrula(
        "RAPOR-047",
        paket,
    ) is True



    assert sistem.dogrula(
        "RAPOR-047",
        {
            "karar": "degisti"
        },
    ) is False
