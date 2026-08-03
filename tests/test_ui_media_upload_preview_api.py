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
        (100, 70),
        (30, 30, 30),
    )

    pixels = image.load()

    for y in range(20, 52):
        for x in range(45, 82):
            pixels[x, y] = (
                238,
                65,
                30,
            )

    buffer = BytesIO()

    image.save(
        buffer,
        format="PNG",
    )

    return buffer.getvalue()


def test_isaretli_goruntu_api_ile_doner(
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

        upload = client.post(
            "/api/syk-ui/media-analysis",
            files={
                "file": (
                    "preview.png",
                    _png(),
                    "image/png",
                )
            },
            data={
                "media_id": (
                    "MEDIA-PREVIEW-001"
                )
            },
        )

        assert upload.status_code == 200

        payload = upload.json()

        assert payload["preview_url"]

        preview = client.get(
            payload["preview_url"]
        )

        assert preview.status_code == 200

        assert (
            preview.headers[
                "content-type"
            ]
            == "image/png"
        )

        assert preview.content.startswith(
            b"\x89PNG"
        )

        assert len(
            payload["preview_sha256"]
        ) == 64

    finally:
        media_upload_routes.media_upload_service = (
            original
        )