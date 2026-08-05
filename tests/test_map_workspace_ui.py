from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from syk_simulasyon.syk_ui_runtime.integration import install_ui


def test_map_workspace_visual_assets() -> None:
    app = FastAPI()
    install_ui(app)

    client = TestClient(app)

    screen = client.get("/syk-ui-screen")

    assert screen.status_code == 200

    assert (
        "/syk-ui/css/map_workspace_view.css"
        in screen.text
    )

    assert (
        "/syk-ui/js/map_workspace_view.js"
        in screen.text
    )

    css = client.get(
        "/syk-ui/css/map_workspace_view.css"
    )

    assert css.status_code == 200
    assert ".syk-map-workspace-panel" in css.text
    assert ".syk-map-sonar-sweep" in css.text

    javascript = client.get(
        "/syk-ui/js/map_workspace_view.js"
    )

    assert javascript.status_code == 200
    assert "SyKMapWorkspaceView" in javascript.text
    assert "garmin-sonar" in javascript.text
    assert "0–2 m kıyı tarama bölgesi" in javascript.text