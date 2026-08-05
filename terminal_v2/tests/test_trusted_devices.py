from pathlib import Path

from fastapi.testclient import TestClient

from terminal_v2.app.main import app


client = TestClient(app)


def test_phone_or_tablet_device_registration(
    tmp_path: Path,
    monkeypatch,
):
    from terminal_v2.core import trusted_devices

    store = tmp_path / "trusted_devices.json"

    registry = trusted_devices.TrustedDeviceRegistry(
        store_path=store,
    )

    monkeypatch.setattr(
        trusted_devices,
        "trusted_device_registry",
        registry,
    )


def test_device_register_and_reconnect():
    register_response = client.post(
        "/api/v2/devices/register",
        json={
            "device_type": "phone",
            "device_name": "SyKaşif Telefon",
        },
        headers={
            "user-agent": "Android Mobile",
        },
    )

    assert register_response.status_code == 200

    registered = register_response.json()

    assert registered["created"] is True
    assert registered["trust_token"]
    assert (
        registered["device"]["device_type"]
        == "phone"
    )

    reconnect_response = client.post(
        "/api/v2/devices/reconnect",
        json={
            "device_id": (
                registered["device"]["device_id"]
            ),
            "trust_token": (
                registered["trust_token"]
            ),
        },
        headers={
            "user-agent": "Android Mobile",
        },
    )

    assert reconnect_response.status_code == 200

    reconnected = reconnect_response.json()

    assert (
        reconnected["status"]
        == "DEVICE_RECONNECTED"
    )


def test_invalid_device_token_is_rejected():
    register_response = client.post(
        "/api/v2/devices/register",
        json={
            "device_type": "tablet",
            "device_name": "SyKaşif Tablet",
        },
    ).json()

    response = client.post(
        "/api/v2/devices/reconnect",
        json={
            "device_id": (
                register_response["device"]["device_id"]
            ),
            "trust_token": "x" * 32,
        },
    )

    assert response.status_code == 401


def test_device_client_asset_is_available():
    response = client.get(
        "/static/js/device_client.js",
    )

    assert response.status_code == 200
    assert "localStorage" in response.text
    assert "/api/v2/devices/reconnect" in response.text


def test_index_loads_device_client():
    response = client.get("/")

    assert response.status_code == 200
    assert (
        "/static/js/device_client.js"
        in response.text
    )
