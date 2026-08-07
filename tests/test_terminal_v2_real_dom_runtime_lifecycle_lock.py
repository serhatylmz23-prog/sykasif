from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MOTOR = ROOT / "terminal_v2" / "static" / "js" / "canli_modul_gorsel_durum_motoru.js"


def source():
    return MOTOR.read_text(encoding="utf-8")


def test_event_contract_locked():
    text = source()
    assert "sykasif:aktif-modul-guncellendi" in text
    assert "SYK_MODULE_VISUAL_EVENT" in text


def test_runtime_bridge_locked():
    text = source()
    assert "function runtimeEventDatasetBridge" in text
    assert "function runtimeDurumUygula" in text
    assert "function normalizeRuntimeDurum" in text


def test_real_dom_root_resolution():
    text = source()
    assert 'document.querySelector("[data-modul-kodu]")' in text
    assert "document.documentElement" in text


def test_event_detail_is_runtime_source():
    text = source()
    assert "const detail = event?.detail" in text
    assert "runtimeDurumUygula(root, detail)" in text


def test_runtime_dataset_state_transition():
    text = source()
    assert "root.dataset.sykModulDurum = durum" in text
    assert "root.dataset.sykAktifModul" in text
    assert "root.dataset.sykIlerlemeYuzdesi" in text
    assert "root.dataset.sykOlaySayisi" in text


def test_all_visual_states_are_supported():
    text = source()

    states = (
        "bekliyor",
        "calisiyor",
        "taraniyor",
        "dogrulaniyor",
        "tamamlandi",
        "hata",
        "cevrimdisi",
    )

    for state in states:
        assert state in text


def test_event_listener_is_permanent():
    text = source()

    assert "window.addEventListener(" in text
    assert "SYK_MODULE_VISUAL_EVENT" in text
    assert "runtimeEventDatasetBridge" in text


def test_runtime_bridge_rejects_invalid_payload():
    text = source()

    assert 'typeof detail !== "object"' in text
    assert 'typeof value !== "string"' in text
    assert "return false" in text


def test_lifecycle_chain_is_complete():
    text = source()

    chain = (
        "SYK_MODULE_VISUAL_EVENT",
        "runtimeEventDatasetBridge",
        "runtimeDurumUygula",
        "normalizeRuntimeDurum",
        "dataset.sykModulDurum",
    )

    positions = [text.find(item) for item in chain]

    assert all(position >= 0 for position in positions)
