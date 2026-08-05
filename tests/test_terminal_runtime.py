from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from syk_simulasyon.syk_ui_runtime.terminal_routes import (
    terminal_router,
)
from syk_simulasyon.syk_ui_runtime.terminal_state import (
    default_terminal_state,
)


def test_default_terminal_state() -> None:
    state = default_terminal_state().to_dict()

    assert state["terminal_id"] == "syk-main-terminal"
    assert state["device_type"] == "desktop"
    assert state["status"] == "ready"
    assert state["connected"] is True

    module_keys = [
        item["key"]
        for item in state["modules"]
    ]

    assert module_keys == [
        "projects",
        "research",
        "kasif",
        "map",
        "evidence",
        "reports",
        "devices",
        "notifications",
        "institute",
    ]


def test_terminal_state_api() -> None:
    app = FastAPI()
    app.include_router(terminal_router)

    client = TestClient(app)
    response = client.get("/api/syk-ui/terminal/state")

    assert response.status_code == 200

    payload = response.json()

    assert payload["terminal_id"] == "syk-main-terminal"
    assert len(payload["modules"]) == 9