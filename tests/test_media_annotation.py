from io import BytesIO
from pathlib import Path

from PIL import Image

from syk_simulasyon.syk_ui_runtime.media_annotation import (
    MediaAnnotationEngine,
)


def _png() -> bytes:
    image = Image.new(
        "RGB",
        (120, 80),
        (28, 30, 32),
    )

    buffer = BytesIO()

    image.save(
        buffer,
        format="PNG",
    )

    return buffer.getvalue()


def test_isaretli_goruntu_uretilir(
    tmp_path: Path,
):
    output = (
        tmp_path
        / "annotated.png"
    )

    engine = MediaAnnotationEngine()

    result = engine.render(
        source_content=_png(),
        candidates=[
            {
                "title": (
                    "Doku değişimi adayı"
                ),
                "confidence": 88.7,
                "box": {
                    "x": 0.25,
                    "y": 0.20,
                    "width": 0.40,
                    "height": 0.45,
                },
            }
        ],
        output_path=output,
    )

    assert output.is_file()

    assert output.read_bytes().startswith(
        b"\x89PNG"
    )

    assert result.candidate_count == 1

    assert len(
        result.output_sha256
    ) == 64


def test_normalize_disindaki_kutu_sinirlanir(
    tmp_path: Path,
):
    output = (
        tmp_path
        / "bounded.png"
    )

    result = MediaAnnotationEngine().render(
        source_content=_png(),
        candidates=[
            {
                "confidence": 70.0,
                "box": {
                    "x": -0.4,
                    "y": 0.8,
                    "width": 1.9,
                    "height": 1.2,
                },
            }
        ],
        output_path=output,
    )

    assert result.width == 120
    assert result.height == 80