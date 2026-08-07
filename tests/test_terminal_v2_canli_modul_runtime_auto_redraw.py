from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

ENGINE = (
    ROOT
    / "terminal_v2"
    / "static"
    / "js"
    / "canli_modul_gorsel_durum_motoru.js"
)

BOOT = (
    ROOT
    / "terminal_v2"
    / "static"
    / "js"
    / "canli_modul_gorsel_boot.js"
)


def source(path: Path) -> str:
    assert path.exists()
    return path.read_text(encoding="utf-8")


def test_engine_aktif_modul_eventini_dinliyor():
    text = source(ENGINE)
    assert "sykasif:aktif-modul-guncellendi" in text


def test_engine_event_handler_var():
    text = source(ENGINE)
    assert "aktifModulEventiniIsle" in text


def test_engine_event_sonrasi_gorsel_durum_uygulaniyor():
    text = source(ENGINE)
    assert "aktifModulGorselDurumunuUygula" in text


def test_engine_runtime_durum_kaynagini_okuyor():
    text = source(ENGINE)
    assert "[data-runtime-durum]" in text


def test_engine_modul_kartlarini_okuyor():
    text = source(ENGINE)
    assert "[data-modul-kodu]" in text


def test_engine_dataset_durum_yaziyor():
    text = source(ENGINE)
    assert "dataset.sykModulDurum" in text


def test_engine_dataset_secim_yaziyor():
    text = source(ENGINE)
    assert "dataset.sykModulSecim" in text


def test_engine_dataset_hareket_yaziyor():
    text = source(ENGINE)
    assert "dataset.sykModulHareket" in text


def test_boot_motoru_baslatiyor():
    text = source(BOOT)
    assert "canliModulGorsel" in text or "CanliModulGorsel" in text


def test_boot_dom_hazirligini_kullaniyor():
    text = source(BOOT)
    assert (
        "DOMContentLoaded" in text
        or "document.readyState" in text
    )
