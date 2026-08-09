from terminal_v2.core.power_guard import (
    ES_CONTINUOUS,
    ES_DISPLAY_REQUIRED,
    ES_SYSTEM_REQUIRED,
    PowerGuard,
)


def test_power_guard_constants():
    assert ES_CONTINUOUS == 0x80000000
    assert ES_SYSTEM_REQUIRED == 0x00000001
    assert ES_DISPLAY_REQUIRED == 0x00000002


def test_power_guard_status_export():
    guard = PowerGuard(
        keep_display_on=True,
    )

    status = guard.status().export()

    assert "supported" in status
    assert status["active"] is False
    assert status["keep_display_on"] is True
    assert "platform" in status
    assert "error" in status


def test_power_guard_without_display():
    guard = PowerGuard(
        keep_display_on=False,
    )

    assert guard.keep_display_on is False
    assert guard.active is False
