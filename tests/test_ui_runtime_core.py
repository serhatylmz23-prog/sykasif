from syk_ui.audio_manager import AudioManager
from syk_ui.environment import EnvironmentManager
from syk_ui.module_registry import enabled_modules
from syk_ui.runtime_manager import RuntimeManager
from syk_ui.theme_manager import ThemeManager
from syk_ui.typography import TypographyManager


def test_ui_runtime_core():
    modules = enabled_modules()
    assert len(modules) == 27

    runtime = RuntimeManager()
    assert runtime.active.id == "dashboard"
    assert runtime.exists("sonar")
    assert runtime.activate("sonar").id == "sonar"
    assert len(runtime.modules()) == 27

    themes = ThemeManager()
    assert themes.set("night").id == "night"
    assert len(themes.available()) == 7

    environment = EnvironmentManager()
    state = environment.update(
        season="winter",
        weather="snow",
        daytime="night",
        wind=18.5,
    )
    assert state.season == "winter"
    assert state.weather == "snow"
    assert state.daytime == "night"
    assert state.wind == 18.5

    audio = AudioManager()
    assert audio.select("jarmin").name == "jarmin.wav"
    assert len(audio.available()) == 6

    typography = TypographyManager()
    assert typography.get("sykasif").family == "SyKasif"
    assert len(typography.available()) == 4
