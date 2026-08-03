from fastapi import FastAPI
from fastapi.testclient import TestClient

from syk_simulasyon.syk_ui_runtime.dtse_attention_routes import (
    router,
)


def test_dtse_dikkat_api_ve_websocket():
    app = FastAPI()
    app.include_router(
        router,
        prefix="/api/syk-ui",
    )

    client = TestClient(app)

    ingest = client.post(
        "/api/syk-ui/dtse/frames/attention",
        json={
            "media_id": "camera-001",
            "source_kind": "live",
            "frame_index": 44,
            "timestamp_ms": 1466,
            "frame_width": 1920,
            "frame_height": 1080,
            "signals": [
                {
                    "label": "Yüzey değişimi",
                    "kind": "surface",
                    "confidence": 91.8,
                    "box": {
                        "x": 0.31,
                        "y": 0.22,
                        "width": 0.28,
                        "height": 0.36,
                    },
                    "description": (
                        "Canlı akış yüzey "
                        "değişimi."
                    ),
                    "metrics": {
                        "surface_delta": 0.76,
                    },
                    "evidence_refs": [],
                }
            ],
        },
    )

    assert ingest.status_code == 200
    assert ingest.json()["created_count"] == 1

    events = client.get(
        "/api/syk-ui/dtse/events"
    )

    assert events.status_code == 200
    assert len(events.json()) >= 1

    latest = events.json()[0]

    assert latest["media_id"] == "camera-001"
    assert latest["signal"]["confidence"] == 91.8

    with client.websocket_connect(
        "/api/syk-ui/dtse/live"
    ) as websocket:
        snapshot = websocket.receive_json()

    assert snapshot["event_count"] >= 1
    assert snapshot["latest_event"] is not None