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


def motor_source():
    assert MOTOR.exists()
    return MOTOR.read_text(encoding="utf-8")


def css_source():
    assert CSS.exists()
    return CSS.read_text(encoding="utf-8")


STATES = (
    "bekliyor",
    "calisiyor",
    "taraniyor",
    "dogrulaniyor",
    "tamamlandi",
    "hata",
    "cevrimdisi",
)


def test_runtime_event_enters_visual_chain():
    text = motor_source()
    assert "SYK_MODULE_VISUAL_EVENT" in text
    assert "sykasif:aktif-modul-guncellendi" in text
    assert "runtimeEventDatasetBridge" in text


def test_event_payload_reaches_runtime_state():
    text = motor_source()
    assert "event?.detail" in text
    assert "runtimeDurumUygula" in text
    assert "normalizeRuntimeDurum" in text


def test_runtime_state_reaches_dom_dataset():
    text = motor_source()
    assert "dataset.sykModulDurum" in text


def test_all_runtime_states_exist_in_motor():
    text = motor_source()

    for state in STATES:
        assert state in text


def test_all_runtime_states_exist_in_css():
    text = css_source()

    for state in STATES:
        assert state in text


def test_css_is_bound_to_runtime_dataset():
    text = css_source()
    assert "data-syk-modul-durum" in text


def test_runtime_event_listener_is_live():
    text = motor_source()
    assert "addEventListener" in text
    assert "SYK_MODULE_VISUAL_EVENT" in text
    assert "runtimeEventDatasetBridge" in text


def test_complete_visual_pipeline_contract():
    motor = motor_source()
    css = css_source()

    assert "sykasif:aktif-modul-guncellendi" in motor
    assert "runtimeEventDatasetBridge" in motor
    assert "runtimeDurumUygula" in motor
    assert "dataset.sykModulDurum" in motor
    assert "data-syk-modul-durum" in css


def test_visual_state_contract_is_symmetric():
    motor = motor_source()
    css = css_source()

    for state in STATES:
        assert state in motor
        assert state in css
