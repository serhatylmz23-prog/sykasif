from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from syk_simulasyon.syk_ui import install_ui


def test_sonar_session_visual_assets() -> None:
    app = FastAPI()
    install_ui(app)

    client = TestClient(app)

    screen = client.get("/syk-ui-screen")

    assert screen.status_code == 200

    assert (
        "/syk-ui/css/sonar_session_panel.css"
        in screen.text
    )

    assert (
        "/syk-ui/js/sonar_session_panel.js"
        in screen.text
    )

    css = client.get(
        "/syk-ui/css/sonar_session_panel.css"
    )

    assert css.status_code == 200
    assert ".syk-sonar-session-panel" in css.text
    assert ".syk-sonar-fish-target" in css.text
    assert ".syk-sonar-timeline-bar" in css.text

    javascript = client.get(
        "/syk-ui/js/sonar_session_panel.js"
    )

    assert javascript.status_code == 200
    assert "SyKSonarSessionPanel" in javascript.text
    assert "0–2 m kıyı profili" in javascript.text
    assert "fish_target_count" in javascript.text