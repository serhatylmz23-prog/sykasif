from syk_core.entegrasyon.cekirdek_durum_makinesi import (
    CekirdekDurumMakinesi,
)



def test_durum_zinciri():

    sistem = CekirdekDurumMakinesi()


    assert sistem.mevcut_durum() == "taslak"



    assert sistem.gecis_yap(
        "test_ediliyor",
        "ilk test baslangici",
    )



    assert sistem.gecis_yap(
        "dogrulandi",
        "testler tamamlandi",
    )



    assert sistem.gecis_yap(
        "muhur_adayi",
        "muhur hazirligi",
    )



    assert sistem.mevcut_durum() == "muhur_adayi"



    assert len(
        sistem.gecmis_getir()
    ) == 3



def test_gecersiz_gecis_engeli():

    sistem = CekirdekDurumMakinesi()


    assert sistem.gecis_yap(
        "arsivlendi",
        "hatal? atlama",
    ) is False


    assert sistem.mevcut_durum() == "taslak"
