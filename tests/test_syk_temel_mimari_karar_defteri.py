from syk_core.entegrasyon.syk_temel_mimari_karar_defteri import (
    SYKTemelMimariKararDefteri,
)



def test_temel_mimari_karar_defteri():

    sistem = SYKTemelMimariKararDefteri()


    sonuc = sistem.karar_ekle(

        "SYK-MIMARI-001",

        "Temel Mimari Karar Defteri",

        "MIMARI",

        "KA??F nihai karar sahibidir. B?LGE KAAN teknik rapor ve ?neri haz?rlar.",

    )


    assert (
        sonuc.durum
        ==
        "MUHURLENDI"
    )


    assert (
        sonuc.karar_sahibi
        ==
        "KASIF_KURUCU"
    )


    assert (
        sonuc.hazirlayan
        ==
        "BILGE_KAAN"
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
