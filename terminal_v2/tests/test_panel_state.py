from fastapi.testclient import TestClient

from terminal_v2.app.main import app


client = TestClient(app)


def setup_function():
    response = client.delete(
        "/api/v2/panel/state"
    )

    assert response.status_code == 200


def test_panel_state_initial_snapshot():
    response = client.get(
        "/api/v2/panel/state"
    )

    assert response.status_code == 200

    body = response.json()

    assert body["revision"] == 0
    assert (
        body["state"]["active_module"]
        == "dashboard"
    )


def test_panel_state_shared_update():
    response = client.post(
        "/api/v2/panel/state",
        json={
            "patch": {
                "active_module": "analysis",
                "panels": {
                    "tablet": True,
                },
                "modules": {
                    "analysis": {
                        "status": "RUNNING",
                    },
                },
            },
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["revision"] == 1
    assert (
        body["state"]["active_module"]
        == "analysis"
    )
    assert body["state"]["panels"]["tablet"] is True
    assert (
        body["state"]["panels"]["desktop"]
        is True
    )


def test_panel_event_updates_revision():
    response = client.post(
        "/api/v2/panel/event",
        json={
            "event_type": "NEW_EVIDENCE",
            "source": "tablet",
            "payload": {
                "evidence_id": "KANIT-001",
            },
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["revision"] == 1
    assert (
        body["event"]["type"]
        == "NEW_EVIDENCE"
    )
    assert (
        body["state"]["last_event"]["source"]
        == "tablet"
    )


def test_panel_routes_exist_in_openapi():
    paths = set(
        app.openapi().get("paths", {})
    )

    required = {
        "/api/v2/panel/state",
        "/api/v2/panel/event",
    }

    assert required.issubset(paths)
