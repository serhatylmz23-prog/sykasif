from datetime import UTC, datetime

import pytest

from syk_core.goruntu.frame.candidate_engine import (
    FrameCandidateEngine,
)
from syk_core.goruntu.frame.frame_models import (
    FrameRecord,
    FrameSourceKind,
    FrameStatus,
)


def _record(
    *,
    width: int,
    height: int,
) -> FrameRecord:
    return FrameRecord(
        frame_id="FRM-CANDIDATE-001",
        media_id="IMG-CANDIDATE-001",
        source_kind=FrameSourceKind.IMAGE,
        frame_index=0,
        timestamp_ms=0,
        frame_width=width,
        frame_height=height,
        payload_size=width * height,
        frame_sha256="a" * 64,
        source_sha256="b" * 64,
        status=FrameStatus.CANDIDATE,
        created_at=datetime.now(
            UTC
        ).isoformat(),
    )


def _gray_frame_with_bright_region(
    *,
    width: int,
    height: int,
) -> bytes:
    pixels = bytearray(
        [35] * (width * height)
    )

    for y in range(
        height // 3,
        height * 2 // 3,
    ):
        for x in range(
            width // 2,
            width * 3 // 4,
        ):
            pixels[
                y * width + x
            ] = 235

    return bytes(pixels)


def test_parlak_bolge_adayi_uretilir():
    width = 64
    height = 48

    engine = FrameCandidateEngine(
        grid_columns=8,
        grid_rows=6,
        minimum_score=0.20,
    )

    result = engine.analyze(
        record=_record(
            width=width,
            height=height,
        ),
        pixels=(
            _gray_frame_with_bright_region(
                width=width,
                height=height,
            )
        ),
        channels=1,
    )

    assert result.candidates

    candidate = result.candidates[0]

    assert candidate.kind == (
        "visual_anomaly"
    )

    assert candidate.confidence <= 99.9
    assert candidate.uncertainty > 0.0

    assert (
        "luminance_contrast"
        in candidate.methods
    )

    assert (
        0.0
        <= candidate.box.x
        < 1.0
    )

    assert (
        candidate.box.x
        + candidate.box.width
        <= 1.0
    )


def test_duz_karede_yuksek_esikte_aday_uretilmez():
    width = 48
    height = 32

    engine = FrameCandidateEngine(
        minimum_score=0.50,
    )

    result = engine.analyze(
        record=_record(
            width=width,
            height=height,
        ),
        pixels=bytes(
            [110]
            * width
            * height
        ),
        channels=1,
    )

    assert result.candidates == ()


def test_rgb_kare_desteklenir():
    width = 24
    height = 16

    pixels = bytearray()

    for y in range(height):
        for x in range(width):
            if (
                x > width // 2
                and y > height // 3
            ):
                pixels.extend(
                    (245, 40, 25)
                )
            else:
                pixels.extend(
                    (25, 25, 25)
                )

    engine = FrameCandidateEngine(
        grid_columns=6,
        grid_rows=4,
        minimum_score=0.12,
    )

    result = engine.analyze(
        record=_record(
            width=width,
            height=height,
        ),
        pixels=bytes(pixels),
        channels=3,
    )

    assert result.channels == 3
    assert result.candidates


def test_rgba_kare_desteklenir():
    width = 16
    height = 12

    pixels = bytes(
        [40, 40, 40, 255]
        * width
        * height
    )

    engine = FrameCandidateEngine(
        minimum_score=0.90,
    )

    result = engine.analyze(
        record=_record(
            width=width,
            height=height,
        ),
        pixels=pixels,
        channels=4,
    )

    assert result.channels == 4


def test_piksel_boyutu_uyusmazsa_reddedilir():
    engine = FrameCandidateEngine()

    with pytest.raises(
        ValueError,
        match="Piksel uzunluğu",
    ):
        engine.analyze(
            record=_record(
                width=20,
                height=10,
            ),
            pixels=b"short",
            channels=1,
        )


def test_sonuc_dijital_aday_olarak_isaretlenir():
    width = 32
    height = 24

    engine = FrameCandidateEngine(
        minimum_score=0.15,
    )

    result = engine.analyze(
        record=_record(
            width=width,
            height=height,
        ),
        pixels=(
            _gray_frame_with_bright_region(
                width=width,
                height=height,
            )
        ),
        channels=1,
    ).as_dict()

    assert (
        result["analysis_scope"]
        == "digital_visual_candidates"
    )

    assert result[
        "field_validation_required"
    ]

    assert (
        result[
            "maximum_digital_confidence"
        ]
        == 99.9
    )