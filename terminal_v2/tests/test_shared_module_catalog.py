from terminal_v2.shared.module_catalog import (
    CANLI_MODUL_KATALOGU,
    modul_bilgisi_getir,
    modul_kartlarini_getir,
)


def test_shared_catalog_contains_required_modules():
    assert {
        "dashboard",
        "harita",
        "kanit",
        "analiz",
        "gorev",
        "rapor",
        "sensorler",
    }.issubset(CANLI_MODUL_KATALOGU)


def test_shared_catalog_has_turkish_content():
    dashboard = modul_bilgisi_getir(
        "dashboard"
    )

    assert (
        dashboard["ad"]
        == "Ana \u00c7al\u0131\u015fma Alan\u0131"
    )
    assert dashboard["islemler"]


def test_unknown_module_returns_dashboard():
    modul = modul_bilgisi_getir(
        "bilinmeyen-modul"
    )

    assert modul["kod"] == "dashboard"


def test_module_catalog_returns_safe_copies():
    first = modul_bilgisi_getir(
        "harita"
    )
    second = modul_bilgisi_getir(
        "harita"
    )

    first["ad"] = "DEGISTI"

    assert second["ad"] == "Harita"


def test_module_cards_are_shared_source():
    cards = modul_kartlarini_getir()

    assert len(cards) == len(
        CANLI_MODUL_KATALOGU
    )
    assert any(
        card["kod"] == "rapor"
        for card in cards
    )
