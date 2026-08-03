from io import BytesIO

from PIL import Image

from syk_core.goruntu.frame.media_analysis_pipeline import (
    FrameCache,
    ImageDecoder,
    MediaAnalysisPipeline,
    MotionDetector,
)


def _image_bytes(
    *,
    width: int = 96,
    height: int = 64,
    changed: bool = False,
    image_format: str = "PNG",
) -> bytes:
    image = Image.new(
        "RGB",
        (width, height),
        (35, 35, 35),
    )

    pixels = image.load()

    if changed:
        for y in range(
            height // 3,
            height * 2 // 3,
        ):
            for x in range(
                width // 2,
                width * 3 // 4,
            ):
                pixels[x, y] = (
                    240,
                    70,
                    30,
                )

    buffer = BytesIO()

    image.save(
        buffer,
        format=image_format,
    )

    return buffer.getvalue()


def test_png_cozulur():
    decoder = ImageDecoder()

    decoded = decoder.decode(
        _image_bytes()
    )

    assert decoded.width == 96
    assert decoded.height == 64
    assert decoded.channels == 3
    assert decoded.image_format == "PNG"
    assert len(
        decoded.source_sha256
    ) == 64


def test_jpeg_cozulur():
    decoder = ImageDecoder()

    decoded = decoder.decode(
        _image_bytes(
            image_format="JPEG"
        )
    )

    assert decoded.image_format == "JPEG"
    assert decoded.channels == 3


def test_gecersiz_goruntu_reddedilir():
    decoder = ImageDecoder()

    try:
        decoder.decode(
            b"not-an-image"
        )
    except ValueError as error:
        assert "çözülemedi" in str(error)
    else:
        raise AssertionError(
            "Geçersiz görüntü kabul edildi."
        )


def test_hareket_algilanir():
    detector = MotionDetector(
        pixel_threshold=0.05,
        ratio_threshold=0.01,
    )

    previous = bytes(
        [20] * 300
    )

    current = bytearray(previous)

    for index in range(60):
        current[index] = 220

    result = detector.compare(
        previous,
        bytes(current),
    )

    assert result.available
    assert result.motion_detected
    assert result.changed_ratio > 0.01


def test_frame_cache_kapasiteyi_korur():
    cache = FrameCache(
        maximum_entries=2
    )

    decoder = ImageDecoder()

    first = decoder.decode(
        _image_bytes(
            width=20,
            height=20,
        )
    )

    second = decoder.decode(
        _image_bytes(
            width=21,
            height=20,
        )
    )

    third = decoder.decode(
        _image_bytes(
            width=22,
            height=20,
        )
    )

    cache.put("FRM-1", first)
    cache.put("FRM-2", second)
    cache.put("FRM-3", third)

    assert cache.get("FRM-1") is None
    assert cache.get("FRM-2") is second
    assert cache.get("FRM-3") is third


def test_fotograf_ucltan_uca_analiz_edilir():
    dispatched = []

    pipeline = MediaAnalysisPipeline(
        dtse_dispatcher=(
            dispatched.append
        )
    )

    result = pipeline.analyze_image(
        media_id="IMG-PIPELINE-001",
        content=_image_bytes(
            changed=True
        ),
        source_kind="image",
        source_name="test.png",
    )

    assert not result.ingestion.duplicate
    assert result.candidates.candidates
    assert result.dtse_payload["signals"]
    assert result.report_payload[
        "evidences"
    ]

    assert len(dispatched) == 1

    assert (
        dispatched[0]["media_id"]
        == "IMG-PIPELINE-001"
    )

    assert result.as_dict()[
        "field_validation_required"
    ]


def test_video_karelerinde_hareket_ve_timeline():
    pipeline = MediaAnalysisPipeline()

    first = pipeline.analyze_image(
        media_id="VIDEO-001",
        content=_image_bytes(
            changed=False
        ),
        frame_index=0,
        timestamp_ms=0,
        source_kind="video",
    )

    second = pipeline.analyze_image(
        media_id="VIDEO-001",
        content=_image_bytes(
            changed=True
        ),
        frame_index=1,
        timestamp_ms=40,
        source_kind="video",
    )

    assert not first.motion.available
    assert second.motion.available
    assert second.motion.motion_detected

    timeline = pipeline.timeline.list(
        media_id="VIDEO-001"
    )

    assert len(timeline) == 2
    assert (
        timeline[1].frame_index
        == 1
    )


def test_ayni_goruntu_tekrar_kaydedilmez():
    pipeline = MediaAnalysisPipeline()

    content = _image_bytes(
        changed=True
    )

    first = pipeline.analyze_image(
        media_id="IMG-DUP-001",
        content=content,
    )

    second = pipeline.analyze_image(
        media_id="IMG-DUP-001",
        content=content,
        frame_index=8,
    )

    assert not first.ingestion.duplicate
    assert second.ingestion.duplicate

    assert len(
        pipeline.timeline.list(
            media_id="IMG-DUP-001"
        )
    ) == 1


def test_rapor_payload_dijital_kapsami_korur():
    pipeline = MediaAnalysisPipeline()

    result = pipeline.analyze_image(
        media_id="IMG-REPORT-001",
        content=_image_bytes(
            changed=True
        ),
    )

    payload = result.report_payload

    assert (
        payload["analysis_scope"]
        == "digital_analysis_only"
    )

    assert payload[
        "field_validation_required"
    ]

    assert (
        payload[
            "maximum_digital_confidence"
        ]
        == 99.9
    )