from syk_simulasyon.syk_ui import UIRuntimeState


def test_ui_runtime_state_snapshot():
    state = UIRuntimeState()

    state.runtime.activate("sonar")
    state.theme.set("night")
    state.environment.update(
        season="winter",
        weather="snow",
        daytime="night",
        wind=12.5,
    )
    state.audio.select("analysis")
    state.brand.write("syotagi")
    state.syframe.update(
        state="verified",
        mode="evidence",
        confidence=94.2,
    )

    snapshot = state.snapshot()

    assert snapshot["active_module"]["id"] == "sonar"
    assert snapshot["theme"]["id"] == "night"
    assert snapshot["environment"]["weather"] == "snow"
    assert snapshot["audio"]["id"] == "analysis"
    assert snapshot["brand"]["title"]["text"] == "SyOta\u011f\u0131"
    assert snapshot["brand"]["visible"]
    assert snapshot["syframe"]["state"]["id"] == "verified"
    assert snapshot["syframe"]["mode"] == "evidence"
    assert snapshot["syframe"]["confidence"] == 94.2
    assert snapshot["assets"]["audio_ready"]
    assert snapshot["assets"]["images_ready"]