import base64

from fastapi.testclient import TestClient

from syk_simulasyon.runtime_ui_sunucusu import (
    app,
)


def test_kamera_api():
    client = TestClient(app)

    response = client.post(
        "/api/syk-ui/mobile-sensors/"
        "camera/start",
        json={
            "facing_mode": "environment",
            "width": 1280,
            "height": 720,
            "frame_rate": 24.0,
            "stream_id": "CAM-API-001",
        },
    )

    assert response.status_code == 200

    assert response.json()[
        "active"
    ]


def test_mikrofon_api():
    client = TestClient(app)

    response = client.post(
        "/api/syk-ui/mobile-sensors/"
        "microphone/start",
        json={
            "sample_rate": 16000,
            "channels": 1,
            "stream_id": "MIC-API-001",
        },
    )

    assert response.status_code == 200

    assert (
        response.json()[
            "channels"
        ]
        == 1
    )


def test_konum_api():
    client = TestClient(app)

    response = client.post(
        "/api/syk-ui/mobile-sensors/"
        "location",
        json={
            "latitude": 41.0082,
            "longitude": 28.9784,
            "accuracy_meters": 5.0,
            "altitude_meters": 35.0,
            "heading_degrees": 180.0,
            "speed_meters_per_second": 0.5,
            "source": "pytest",
        },
    )

    assert response.status_code == 200

    assert (
        response.json()[
            "longitude"
        ]
        == 28.9784
    )


def test_kamera_karesi_api():
    client = TestClient(app)

    data = base64.b64encode(
        b"fake-jpeg-content"
    ).decode("ascii")

    response = client.post(
        "/api/syk-ui/mobile-sensors/"
        "frames",
        json={
            "device_id": "PHONE-API-001",
            "data_base64": data,
            "mime_type": "image/jpeg",
            "width": 640,
            "height": 480,
            "source": "pytest",
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert (
        payload["mime_type"]
        == "image/jpeg"
    )

    assert len(
        payload["frame_sha256"]
    ) == 64