from syk_core.kanit.kanit_arsiv_modeli import (
    KanitArsivYoneticisi,
    KanitKaydi,
)


def test_kanit_kaydedilir():

    yonetici = KanitArsivYoneticisi()

    kayit = yonetici.kanit_kaydet(
        KanitKaydi(
            "MAT-001",
            "Malzeme",
            "laboratuvar",
        )
    )

    assert kayit.veri_turu == "Malzeme"



def test_uzman_incelemesi_tutulur():

    yonetici = KanitArsivYoneticisi()

    yonetici.kanit_kaydet(
        KanitKaydi(
            "GOR-001",
            "Video",
            "saha kaydi",
        )
    )

    yonetici.uzman_incelemesi_ekle(
        "GOR-001",
        "goruntu dogrulama gerekli",
    )

    assert len(
        yonetici.kayitlar[
            "GOR-001"
        ].uzman_incelemeleri
    ) == 1



def test_gereksiz_veri_arsiv_disina_alinir():

    yonetici = KanitArsivYoneticisi()

    yonetici.kanit_kaydet(
        KanitKaydi(
            "TEST-001",
            "gecersiz veri",
            "kaynak",
        )
    )

    yonetici.gereksiz_arsivden_cikar(
        "TEST-001"
    )

    assert (
        yonetici.kayitlar[
            "TEST-001"
        ].durum
        ==
        "arsiv_disari"
    )
