from syk_core.uzmanlar.uzman_modeli import (
    UzmanKararYasagi,
    UzmanModeli,
)


def test_uzman_oneri_uretebilir():

    uzman = UzmanModeli(
        uzman_kimligi="JEO-001",
        uzman_adi="Jeoloji Uzman?",
        bilim_ailesi="Yer Bilimleri",
        gorev_alani="Jeolojik analiz",
    )

    sonuc = uzman.analiz_onerisi_uret(
        "zemin yap?s?"
    )

    assert sonuc["durum"] == "?neri"
    assert not sonuc["nihai_karar"]


def test_uzman_karar_veremez():

    uzman = UzmanModeli(
        uzman_kimligi="SON-001",
        uzman_adi="Sonar Uzman?",
        bilim_ailesi="Akustik",
        gorev_alani="Sonar analiz",
    )

    try:
        uzman.karar_ver(
            "alan uygun"
        )
        assert False

    except UzmanKararYasagi:
        assert True


def test_uzman_ogrenme_kaydi_tutar():

    uzman = UzmanModeli(
        uzman_kimligi="GOR-001",
        uzman_adi="G?r?nt? Uzman?",
        bilim_ailesi="G?r?nt?",
        gorev_alani="Video analiz",
    )

    uzman.ogrenme_kaydi_ekle(
        "yeni g?r?nt? y?ntemi"
    )

    assert len(
        uzman.ogrenme_kaydi
    ) == 1
