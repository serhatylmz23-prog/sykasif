from terminal_v2.desktop.module_views import (
    modul_gorunumu_getir,
)


def test_harita_view_is_turkish():
    gorunum = modul_gorunumu_getir("harita")

    assert gorunum.baslik == (
        "Canl\u0131 Harita"
    )
    assert gorunum.durum == (
        "Harita \u00e7al\u0131\u015fma alan\u0131 aktif."
    )


def test_analiz_view_is_turkish():
    gorunum = modul_gorunumu_getir("analiz")

    assert gorunum.baslik == "Analiz Paneli"
    assert "bilimsel" in gorunum.aciklama


def test_report_view_exists():
    gorunum = modul_gorunumu_getir("rapor")

    assert gorunum.baslik == "Rapor Merkezi"


def test_unknown_module_has_fallback():
    gorunum = modul_gorunumu_getir(
        "yeni_modul"
    )

    assert gorunum.baslik == "Yeni Modul"
    assert gorunum.durum == (
        "Mod\u00fcl \u00e7al\u0131\u015fma alan\u0131 aktif."
    )
