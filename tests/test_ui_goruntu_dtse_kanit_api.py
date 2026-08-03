from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from syk_simulasyon.syk_ui_runtime.goruntu_dtse_routes import (
    router,
)


def test_goruntu_dtse_olayi_kanit_zinciri_uretir():
    app = FastAPI()

    app.include_router(
        router,
        prefix="/api/syk-ui",
    )

    client = TestClient(app)

    media_id = f"KANIT-API-{uuid4().hex}"

    created = client.post(
        "/api/syk-ui/goruntu/kayitlar",
        json={
            "veri_kimligi": media_id,
            "veri_turu": "Fotoğraf",
            "kaynak": "test görüntüsü",
            "kare_genisligi": 1200,
            "kare_yuksekligi": 900,
        },
    )

    assert created.status_code == 200

    marked = client.post(
        (
            "/api/syk-ui/goruntu/kayitlar/"
            f"{media_id}/supheli-bolgeler"
        ),
        json={
            "x": 120,
            "y": 180,
            "genislik": 360,
            "yukseklik": 270,
            "aciklama": (
                "Yüzey dokusu değişimi"
            ),
            "guven": 91.5,
            "sinyal_turu": "texture",
        },
    )

    assert marked.status_code == 200

    dtse = marked.json()["dtse"]

    assert dtse["created_count"] == 1
    assert len(dtse["evidence"]) == 1

    evidence = dtse["evidence"][0]

    assert evidence["chain_valid"]
    assert len(evidence["record_sha256"]) == 64
    assert len(evidence["manifest_sha256"]) == 64

    chain = client.get(
        (
            "/api/syk-ui/goruntu/kayitlar/"
            f"{media_id}/kanit-zinciri"
        )
    )

    assert chain.status_code == 200
    assert len(chain.json()["records"]) == 1
    assert chain.json()["verification"]["valid"]

    verification = client.get(
        (
            "/api/syk-ui/goruntu/kayitlar/"
            f"{media_id}/kanit-dogrula"
        )
    )

    assert verification.status_code == 200
    assert verification.json()["valid"]
    assert verification.json()["record_count"] == 1

    manifest = client.get(
        (
            "/api/syk-ui/goruntu/kayitlar/"
            f"{media_id}/kanit-manifesti"
        )
    )

    assert manifest.status_code == 200
    assert manifest.json()["record_count"] == 1
    assert len(
        manifest.json()["manifest_sha256"]
    ) == 64
    assert manifest.json()[
        "field_validation_required"
    ]
    assert (
        manifest.json()[
            "maximum_digital_confidence"
        ]
        == 99.9
    )