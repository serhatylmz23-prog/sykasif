from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

MOTOR = ROOT / "terminal_v2/static/js/canli_modul_gorsel_durum_motoru.js"
CSS = ROOT / "terminal_v2/static/css/canli_modul_gorsel_durum.css"

STATES = (
    "bekliyor",
    "calisiyor",
    "taraniyor",
    "dogrulaniyor",
    "tamamlandi",
    "hata",
    "cevrimdisi",
)


def motor():
    return MOTOR.read_text(encoding="utf-8")


def css():
    return CSS.read_text(encoding="utf-8")


def test_event_contract():
    text = motor()
    assert "sykasif:aktif-modul-guncellendi" in text
    assert "runtimeEventDatasetBridge" in text


def test_runtime_to_dom_contract():
    text = motor()
    assert "runtimeDurumUygula" in text
    assert "normalizeRuntimeDurum" in text
    assert "dataset.sykModulDurum" in text


def test_dom_to_css_contract():
    text = css()
    assert "data-syk-modul-durum" in text


def test_state_symmetry():
    js = motor()
    style = css()

    for state in STATES:
        assert state in js
        assert state in style


def test_live_event_listener():
    text = motor()
    assert "addEventListener" in text
    assert "SYK_MODULE_VISUAL_EVENT" in text


def test_runtime_payload_bridge():
    text = motor()
    assert "event?.detail" in text
    assert "runtimeDurumUygula" in text


def test_complete_live_visual_chain():
    js = motor()
    style = css()

    chain = (
        "sykasif:aktif-modul-guncellendi",
        "runtimeEventDatasetBridge",
        "runtimeDurumUygula",
        "dataset.sykModulDurum",
    )

    for item in chain:
        assert item in js

    assert "data-syk-modul-durum" in style
