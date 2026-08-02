import pytest

from syk_simulasyon.syk_ui_runtime.scientific_runtime import (
    ScientificRuntime,
)


def test_bilimsel_runtime_ortak_veri_sozlesmesi():
    runtime = ScientificRuntime()

    assert len(runtime.module_ids()) == 16
    assert runtime.exists("geology")
    assert runtime.exists("gpr")
    assert runtime.exists("water")
    assert not runtime.exists("unknown")

    geology = runtime.get("geology")

    assert geology["definition"]["id"] == "geology"
    assert geology["definition"]["title"] == "JEOLOJİ"
    assert len(geology["definition"]["metrics"]) == 4
    assert len(geology["definition"]["layers"]) == 4
    assert geology["state"]["source"] == "digital_preview"
    assert geology["state"]["sequence"] == 1
    assert geology["state"]["confidence"] == 82.0
    assert "gerçek saha sonucu değildir" in geology["warning"]

    with pytest.raises(KeyError):
        runtime.get("unknown")


def test_bilimsel_runtime_guncelleme():
    runtime = ScientificRuntime()

    before = runtime.get("thermal")

    updated = runtime.update(
        "thermal",
        live_value=26.4,
        confidence=94.7,
        status="verified",
        source="verified_adapter",
    )

    assert updated["state"]["live_value"] == 26.4
    assert updated["state"]["confidence"] == 94.7
    assert updated["state"]["status"] == "verified"
    assert updated["state"]["source"] == "verified_adapter"
    assert (
        updated["state"]["sequence"]
        == before["state"]["sequence"] + 1
    )

    clamped = runtime.update(
        "thermal",
        confidence=150,
    )

    assert clamped["state"]["confidence"] == 99.9