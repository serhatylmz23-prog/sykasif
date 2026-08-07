from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MOTOR = ROOT / "terminal_v2" / "static" / "js" / "canli_modul_gorsel_durum_motoru.js"


def source():
    return MOTOR.read_text(encoding="utf-8")


def test_runtime_normalizer():
    text = source()
    assert "function normalizeRuntimeDurum" in text
    assert "SYK_RUNTIME_DURUM_MAP" in text


def test_runtime_dataset_bridge():
    text = source()
    assert "function runtimeDurumUygula" in text
    assert "root.dataset.sykModulDurum = durum" in text


def test_runtime_aktif_modul():
    assert "runtimeState.aktif_modul" in source()
    assert "dataset.sykAktifModul" in source()


def test_runtime_ilerleme():
    assert "runtimeState.ilerleme_yuzdesi" in source()
    assert "dataset.sykIlerlemeYuzdesi" in source()


def test_runtime_olay_sayisi():
    assert "runtimeState.olay_sayisi" in source()
    assert "dataset.sykOlaySayisi" in source()


def test_runtime_event_bridge():
    text = source()
    assert "function runtimeEventDatasetBridge" in text
    assert "SYK_MODULE_VISUAL_EVENT" in text
    assert "window.addEventListener" in text


def test_runtime_states():
    text = source()
    for state in (
        "bekliyor",
        "calisiyor",
        "taraniyor",
        "dogrulaniyor",
        "tamamlandi",
        "hata",
        "cevrimdisi",
    ):
        assert state in text
