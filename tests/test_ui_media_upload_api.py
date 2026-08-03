from io import BytesIO
from pathlib import Path

from fastapi.testclient import TestClient
from PIL import Image

from syk_simulasyon.runtime_ui_sunucusu import (
    app,
)
from syk_simulasyon.syk_ui_runtime import (
    media_upload_routes,
)
from syk_simulasyon.syk_ui_runtime.media_upload_service import (
    MediaUploadService,
)


class FakeDTSEBridge:
    def dispatch(self, payload):
        return {
            "connected": True,
            "created_count": len(
                payload["signals"]
            ),
        }


def _png() -> bytes:
    image = Image.new(
        "RGB",
        (80, 60),
        (25, 25, 25),
    )

    pixels = image.load()

    for y in range(20, 42):
        for x in range(40, 68):
            pixels[x, y] = (
                235,
                70,
                35,
            )

    buffer = BytesIO()
    image.save(buffer, format="PNG")

    return buffer.getvalue()


def test_fotograf_yukleme_api_ucltan_uca(
    tmp_path: Path,
):
    original = (
        media_upload_routes
        .media_upload_service
    )

    media_upload_routes.media_upload_service = (
        MediaUploadService(
            artifact_root=tmp_path,
            dtse_bridge=FakeDTSEBridge(),
        )
    )

    try:
        client = TestClient(app)

        response = client.post(
            "/api/syk-ui/media-analysis",
            files={
                "file": (
                    "test.png",
                    _png(),
                    "image/png",
                )
            },
            data={
                "media_id": (
                    "MEDIA-API-001"
                ),
                "location": "Test alanı",
            },
        )

        assert response.status_code == 200

        payload = response.json()

        assert payload[
            "candidate_count"
        ] > 0

        assert payload[
            "dtse_created_count"
        ] > 0

        report = client.get(
            payload["download_url"]
        )

        assert report.status_code == 200

        assert report.content.startswith(
            b"%PDF-"
        )

        manifest = client.get(
            payload["manifest_url"]
        )

        assert manifest.status_code == 200

        assert (
            "manifest_sha256"
            in manifest.json()
        )

    finally:
        media_upload_routes.media_upload_service = (
            original
        )