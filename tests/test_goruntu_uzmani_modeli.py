from syk_core.goruntu.goruntu_uzmani_modeli import (
    GoruntuKaydi,
    GoruntuUzmani,
)


def test_goruntu_kaydi():

    uzman = GoruntuUzmani()

    kayit = uzman.goruntu_kaydet(
        GoruntuKaydi(
            "VID-001",
            "Video",
            "saha kaydi",
        )
    )

    assert kayit.veri_turu == "Video"



def test_supheli_bolge_isaretlenir():

    uzman = GoruntuUzmani()

    uzman.goruntu_kaydet(
        GoruntuKaydi(
            "FOTO-001",
            "Foto?raf",
            "kullanici verisi",
        )
    )

    uzman.supheli_bolge_isaretle(
        "FOTO-001",
        10,
        20,
        100,
        80,
        "nesne benzeri alan",
    )

    assert len(
        uzman.kayitlar[
            "FOTO-001"
        ].supheli_bolgeler
    ) == 1



def test_konum_yoksa_analiz_ister():

    uzman = GoruntuUzmani()

    uzman.goruntu_kaydet(
        GoruntuKaydi(
            "IMG-001",
            "Foto?raf",
            "dis kaynak",
        )
    )

    assert uzman.konum_yoksa_uzmana_gonder(
        "IMG-001"
    )
