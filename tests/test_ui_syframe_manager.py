import pytest

from syk_simulasyon.syk_ui import SyFrameManager


def test_ui_syframe_manager():
    manager = SyFrameManager()

    assert manager.state.id == "analyzing"
    assert manager.mode == "focus"
    assert manager.visible
    assert manager.confidence == 0.0

    state = manager.update(
        state="verified",
        mode="evidence",
        visible=True,
        confidence=92.7,
    )

    assert state.id == "verified"
    assert manager.mode == "evidence"
    assert manager.visible
    assert manager.confidence == 92.7
    assert len(manager.available_states()) == 7

    manager.update(confidence=150)
    assert manager.confidence == 99.9

    with pytest.raises(KeyError):
        manager.update(state="unknown")

    with pytest.raises(KeyError):
        manager.update(mode="unknown")
