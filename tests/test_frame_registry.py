from syk_core.goruntu.frame.frame_ingestion import (
    FrameIngestionEngine,
)
from syk_core.goruntu.frame.frame_models import (
    FramePacket,
)


def _packet(
    *,
    media_id: str = "IMG-001",
    payload: bytes = b"frame-data",
    frame_index: int = 0,
) -> FramePacket:
    return FramePacket(
        media_id=media_id,
        source_kind="image",
        frame_index=frame_index,
        timestamp_ms=frame_index * 40,
        frame_width=1280,
        frame_height=720,
        payload=payload,
    )


def test_ayni_kare_ikinci_kez_kaydedilmez():
    engine = FrameIngestionEngine()

    first = engine.ingest(
        _packet()
    )

    second = engine.ingest(
        _packet(frame_index=4)
    )

    assert not first.duplicate
    assert second.duplicate
    assert (
        second.duplicate_of
        == first.record.frame_id
    )
    assert engine.registry.count() == 1


def test_farkli_kareler_ayri_kaydedilir():
    engine = FrameIngestionEngine()

    engine.ingest(
        _packet(payload=b"frame-one")
    )

    engine.ingest(
        _packet(
            payload=b"frame-two",
            frame_index=1,
        )
    )

    assert engine.registry.count() == 2

    assert len(
        engine.registry.list(
            media_id="IMG-001"
        )
    ) == 2