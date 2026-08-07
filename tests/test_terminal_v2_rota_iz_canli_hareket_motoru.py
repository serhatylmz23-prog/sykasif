from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

JS = (
    ROOT
    / "terminal_v2"
    / "static"
    / "js"
    / "rota_iz_canli_hareket_motoru.js"
)


def source():
    assert JS.exists()
    return JS.read_text(encoding="utf-8")


def test_hareket_motoru_var():
    assert JS.exists()


def test_durum_profilleri_var():
    text = source()
    assert "normal: Object.freeze({" in text
    assert "aktif: Object.freeze({" in text
    assert "secili: Object.freeze({" in text
    assert "uyari: Object.freeze({" in text
    assert "tamamlandi: Object.freeze({" in text


def test_aktif_ve_secili_hareketli():
    text = source()
    assert "enabled: true" in text
    assert "dashOffsetSpeed" in text


def test_normal_ve_tamamlandi_sabit():
    text = source()
    assert "enabled: false" in text
    assert "speed: 0" in text


def test_motion_profile_uretici_var():
    text = source()
    assert "export function createMotionProfile" in text
    assert "speedScale" in text


def test_motion_frame_uretici_var():
    text = source()
    assert "export function createMotionFrame" in text
    assert "phase" in text
    assert "pulse" in text
    assert "dashOffset" in text


def test_gorsel_sozlesmeye_hareket_uygulaniyor():
    text = source()
    assert "export function applyMotionToVisual" in text
    assert "visual.state" in text
    assert "visual.style?.motion" in text


def test_zaman_milisaniye_olarak_isleniyor():
    text = source()
    assert "elapsedMs" in text
    assert "elapsed / 1000" in text
