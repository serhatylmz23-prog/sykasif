from syk_core.entegrasyon.durum_sha_muhur_baglanti import (
    DurumSHAMuhurBaglanti,
)



def test_durum_sha_muhur():

    sistem = DurumSHAMuhurBaglanti()


    sonuc = sistem.muhurle(

        "dogrulandi",

        "muhur_adayi",

        "muhur hazirligi tamamlandi",

    )


    assert (
        sonuc.durum
        ==
        "muhurlendi"
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



def test_degisen_veri_kontrolu():

    sistem = DurumSHAMuhurBaglanti()


    sonuc = sistem.muhurle(

        "muhur_adayi",

        "bagimsiz_kontrol",

        "capraz kontrol",

    )


    sonuc.aciklama = "degistirildi"


    assert sistem.dogrula(
        sonuc
    ) is False
