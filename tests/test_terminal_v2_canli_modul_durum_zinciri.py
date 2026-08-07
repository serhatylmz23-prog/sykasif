from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

MOTOR = (
    ROOT
    / "terminal_v2"
    / "static"
    / "js"
    / "canli_modul_gorsel_durum_motoru.js"
)

CSS = (
    ROOT
    / "terminal_v2"
    / "static"
    / "css"
    / "canli_modul_gorsel_durum.css"
)


def motor():
    return MOTOR.read_text(encoding="utf-8")


def css():
    return CSS.read_text(encoding="utf-8")


def test_bekliyor():
    assert 'BEKLIYOR: "bekliyor"' in motor()


def test_calisiyor():
    assert 'CALISIYOR: "calisiyor"' in motor()


def test_taraniyor():
    assert 'TARANIYOR: "taraniyor"' in motor()
    assert 'data-syk-modul-durum="taraniyor"' in css()


def test_dogrulaniyor():
    assert 'DOGRULANIYOR: "dogrulaniyor"' in motor()
    assert 'data-syk-modul-durum="dogrulaniyor"' in css()


def test_tamamlandi():
    assert 'TAMAMLANDI: "tamamlandi"' in motor()
    assert 'data-syk-modul-durum="tamamlandi"' in css()


def test_hata():
    assert 'HATA: "hata"' in motor()
    assert 'data-syk-modul-durum="hata"' in css()


def test_cevrimdisi():
    assert 'CEVRIMDISI: "cevrimdisi"' in motor()


def test_contract_dataset():
    assert "dataset.sykModulDurum" in motor()


def test_contract_event():
    assert "sykasif:aktif-modul-guncellendi" in motor()
