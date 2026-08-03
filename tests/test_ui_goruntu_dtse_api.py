from fastapi import FastAPI
from fastapi.testclient import TestClient

from syk_simulasyon.syk_ui_runtime.goruntu_dtse_routes import (
    router,
)


def test_goruntu_supheli_bolgesi_dtse_olayi_uretir():
    app = FastAPI()

    app.include_router(
        router,
        prefix="/api/syk-ui",
    )

    client = TestClient(app)

    created = client.post(
        "/api/syk-ui/goruntu/kayitlar",
        json={
            "veri_kimligi": "CANLI-001",
            "veri_turu": "Canlı Akış",
            "kaynak": "kamera",
            "kare_genisligi": 1920,
            "kare_yuksekligi": 1080,
            "kare_numarasi": 12,
            "zaman_ms": 400,
        },
    )

    assert created.status_code == 200

    marked = client.post(
        (
            "/api/syk-ui/goruntu/kayitlar/"
            "CANLI-001/supheli-bolgeler"
        ),
        json={
            "x": 420,
            "y": 240,
            "genislik": 500,
            "yukseklik": 360,
            "aciklama": (
                "Oyuk ve kanal benzeri geometri"
            ),
            "guven": 91.6,
        },
    )

    assert marked.status_code == 200

    payload = marked.json()

    assert payload["dtse"][
        "created_count"
    ] == 1

    event = payload["dtse"]["events"][0]

    assert event["media_id"] == "CANLI-001"
    assert event["source_kind"] == "live"
    assert event["signal"]["kind"] == "geometry"
    assert event["signal"]["confidence"] == 91.6
    assert len(event["event_sha256"]) == 64