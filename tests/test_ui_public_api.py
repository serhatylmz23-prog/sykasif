from syk_simulasyon.syk_ui import (
    AudioManager,
    EnvironmentManager,
    IconManager,
    RuntimeManager,
    ThemeManager,
    TypographyManager,
    enabled_modules,
    mount_static,
)


def test_ui_public_api():
    assert len(enabled_modules()) == 27
    assert RuntimeManager().active.id == "dashboard"
    assert ThemeManager().current.id == "day"
    assert EnvironmentManager().current.weather == "clear"
    assert AudioManager().current.id == "system"
    assert TypographyManager().get("body").family == "Inter"
    assert IconManager().get("logo").name == "logo.svg"
    assert callable(mount_static)
