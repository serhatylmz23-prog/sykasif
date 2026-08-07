from terminal_v2.desktop.module_views import (
    ModulGorunumu,
    modul_gorunumu_getir,
)
from terminal_v2.shared.module_catalog import (
    modul_bilgisi_getir,
)


def test_desktop_view_uses_shared_catalog():
    ortak = modul_bilgisi_getir(
        "harita"
    )
    masaustu = modul_gorunumu_getir(
        "harita"
    )

    assert isinstance(
        masaustu,
        ModulGorunumu,
    )
    assert masaustu.kod == ortak["kod"]
    assert masaustu.baslik == ortak["baslik"]
    assert masaustu.aciklama == ortak["aciklama"]
    assert masaustu.islemler == tuple(
        ortak["islemler"]
    )


def test_desktop_view_has_turkish_status():
    gorunum = modul_gorunumu_getir(
        "analiz"
    )

    assert (
        gorunum.durum
        == "Analiz \u00e7al\u0131\u015fma alan\u0131 aktif."
    )


def test_desktop_view_builds_action_text():
    gorunum = modul_gorunumu_getir(
        "rapor"
    )

    assert gorunum.islem_metni
    assert "\u2022 Yeni rapor olu\u015ftur" in (
        gorunum.islem_metni
    )


def test_unknown_desktop_module_uses_dashboard():
    gorunum = modul_gorunumu_getir(
        "bilinmeyen"
    )

    assert gorunum.kod == "dashboard"
    assert gorunum.baslik == "Bilinmeyen"
    assert (
        gorunum.durum
        == "Mod\u00fcl \u00e7al\u0131\u015fma alan\u0131 aktif."
    )
