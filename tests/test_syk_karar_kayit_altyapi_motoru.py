from syk_core.entegrasyon.syk_karar_kayit_altyapi_motoru import (
    SYKKararKayitAltyapiMotoru,
)



def test_syk_karar_kaydi():

    sistem = SYKKararKayitAltyapiMotoru()


    sonuc = sistem.karar_kaydet(

        "SYK-MIMARI-001",

        "Rol Ayrimi ve Yetki Zinciri",

        "MIMARI",

        "KASIF nihai karar sahibidir. BILGE KAAN teknik rapor ve ?neri haz?rlar.",

        "v1.0",

        "KASIF_KURUCU",

        "BILGE_KAAN",

    )


    assert (
        sonuc.durum
        ==
        "MUHURLENDI"
    )


    assert (
        sonuc.onay_durumu
        ==
        "ONAYLANDI"
    )


    assert (
        sonuc.karar_sahibi
        ==
        "KASIF_KURUCU"
    )


    assert (
        len(
            sonuc.sha256
        )
        ==
        64
    )


    assert sistem.dogrula(
        sonuc
    ) is True
