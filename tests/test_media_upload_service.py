from io import BytesIO
from pathlib import Path

from PIL import Image

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
            "result": {
                "events": payload[
                    "signals"
                ]
            },
        }


def _png() -> bytes:
    image = Image.new(
        "RGB",
        (96, 64),
        (30, 30, 30),
    )

    pixels = image.load()

    for y in range(18, 45):
        for x in range(48, 80):
            pixels[x, y] = (
                240,
                60,
                25,
            )

    buffer = BytesIO()
    image.save(buffer, format="PNG")

    return buffer.getvalue()


def test_yuklenen_fotograf_analiz_ve_pdf_uretir(
    tmp_path: Path,
):
    service = MediaUploadService(
        artifact_root=tmp_path,
        dtse_bridge=FakeDTSEBridge(),
    )

    result = service.analyze(
        filename="saha.png",
        content_type="image/png",
        content=_png(),
        media_id="MEDIA-UPLOAD-001",
        location="Test alanı",
    )

    assert result["candidate_count"] > 0

    assert (
        result["dtse_created_count"]
        > 0
    )

    assert result["dtse_connected"]

    assert Path(
        result["pdf_path"]
    ).is_file()

    assert Path(
        result["manifest_path"]
    ).is_file()

    assert Path(
        result["result_path"]
    ).is_file()

    assert len(
        result["report_sha256"]
    ) == 64


def test_desteklenmeyen_dosya_reddedilir(
    tmp_path: Path,
):
    service = MediaUploadService(
        artifact_root=tmp_path
    )

    try:
        service.analyze(
            filename="test.txt",
            content_type="text/plain",
            content=b"not-image",
        )
    except ValueError as error:
        assert "Yalnız JPG" in str(error)
    else:
        raise AssertionError(
            "Desteklenmeyen dosya kabul edildi."
        )