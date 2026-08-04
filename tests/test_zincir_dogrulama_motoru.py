from syk_core.entegrasyon.zincir_dogrulama_motoru import (
    ZincirDogrulamaMotoru,
)



def test_zincir_tam_dogrulama():


    sistem = ZincirDogrulamaMotoru()


    kayitlar = [

        "SHA-001",

        "SHA-002",

        "SHA-003",

    ]


    sonuc = sistem.kontrol_et(

        kayitlar,

        lambda x: True,

    )


    assert (
        sonuc.durum
        ==
        "zincir_dogrulandi"
    )


    assert (
        sonuc.toplam_kayit
        ==
        3
    )


    assert (
        sonuc.dogrulanan_kayit
        ==
        3
    )



def test_zincir_hata_tespiti():


    sistem = ZincirDogrulamaMotoru()


    kayitlar = [

        "SHA-001",

        "SHA-BOZUK",

        "SHA-003",

    ]


    sonuc = sistem.kontrol_et(

        kayitlar,

        lambda x: x != "SHA-BOZUK",

    )


    assert (
        sonuc.durum
        ==
        "zincir_hatasi_var"
    )


    assert (
        sonuc.hatali_kayit
        ==
        1
    )
