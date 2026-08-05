from fastapi.testclient import TestClient

from terminal_v2.app.main import app


client = TestClient(app)


def test_tablet_validation_session_creation():
    response = client.post(
        "/api/v2/tablet-validation/session",
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data["token"]) >= 16
    assert data["status"] == "WAITING"
    assert data["validation_path"].startswith(
        "/tablet-validation/"
    )


def test_tablet_validation_acknowledgement():
    created = client.post(
        "/api/v2/tablet-validation/session",
    ).json()

    token = created["token"]

    response = client.post(
        "/api/v2/tablet-validation/ack",
        json={
            "token": token,
            "viewport_width": 1280,
            "viewport_height": 800,
            "touch_supported": True,
            "event_source_supported": True,
            "sse_connected": True,
        },
        headers={
            "user-agent": "Android SM-X920 Tablet",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["acknowledged"] is True
    assert data["touch_supported"] is True
    assert data["sse_connected"] is True
    assert data["digital_checks_passed"] is True


def test_tablet_validation_page():
    created = client.post(
        "/api/v2/tablet-validation/session",
    ).json()

    response = client.get(
        created["validation_path"],
    )

    assert response.status_code == 200
    assert "Tablet / LAN Doğrulaması" in response.text
    assert "EventSource" in response.text
    assert created["token"] in response.text


def test_unknown_tablet_validation_session():
    response = client.get(
        "/api/v2/tablet-validation/session/unknown-token",
    )

    assert response.status_code == 404
