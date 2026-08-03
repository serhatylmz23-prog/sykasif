import pytest

from syk_core.goruntu.frame.frame_ingestion import (
    FrameIngestionEngine,
)
from syk_core.goruntu.frame.frame_models import (
    FramePacket,
)


@pytest.mark.parametrize(
    "source_kind",
    [
        "image",
        "video",
        "live",
    ],
)
def test_fotograf_video_ve_canli_kare_alinir(
    source_kind: str,
):
    engine = FrameIngestionEngine()

    result = engine.ingest(
        FramePacket(
            media_id=f"MEDIA-{source_kind}",
            source_kind=source_kind,
            frame_index=2,
            timestamp_ms=80,
            frame_width=1920,
            frame_height=1080,
            payload=(
                f"frame-{source_kind}"
            ).encode("utf-8"),
        ),
        status="preview",
    )

    record = result.record

    assert not result.duplicate

    assert (
        record.source_kind.value
        == source_kind
    )

    assert record.status.value == "preview"
    assert len(record.frame_sha256) == 64
    assert len(record.source_sha256) == 64


def test_kare_kaydi_dijital_kapsamla_sinirlanir():
    engine = FrameIngestionEngine()

    result = engine.ingest(
        FramePacket(
            media_id="IMG-SCOPE-001",
            source_kind="image",
            frame_index=0,
            timestamp_ms=0,
            frame_width=640,
            frame_height=480,
            payload=b"scope-frame",
        )
    )

    payload = result.record.as_dict()

    assert (
        payload["analysis_scope"]
        == "digital_frame_candidate"
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


def test_gecersiz_kare_reddedilir():
    with pytest.raises(
        ValueError,
        match="boyutları",
    ):
        FramePacket(
            media_id="BAD-001",
            source_kind="image",
            frame_index=0,
            timestamp_ms=0,
            frame_width=0,
            frame_height=480,
            payload=b"invalid",
        )