from syk_core.goruntu.frame.frame_hash import (
    FrameHash,
)


def test_ayni_kare_ayni_sha256_degerini_uretir():
    payload = b"sykasif-frame-data"

    first = FrameHash.payload_sha256(
        payload
    )

    second = FrameHash.payload_sha256(
        payload
    )

    assert first == second
    assert len(first) == 64


def test_farkli_kare_farkli_sha256_degeri_uretir():
    first = FrameHash.payload_sha256(
        b"frame-one"
    )

    second = FrameHash.payload_sha256(
        b"frame-two"
    )

    assert first != second


def test_frame_id_kararli_uretilir():
    arguments = {
        "media_id": "IMG-001",
        "source_kind": "image",
        "frame_index": 0,
        "timestamp_ms": 0,
        "frame_sha256": "a" * 64,
    }

    first = FrameHash.frame_id(
        **arguments
    )

    second = FrameHash.frame_id(
        **arguments
    )

    assert first == second
    assert first.startswith("FRM-")