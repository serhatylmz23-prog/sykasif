from syk_simulasyon.syk_ui_runtime.dtse_attention_engine import (
    AttentionSignal,
    DTSEAttentionEngine,
    NormalizedBox,
)


def test_dikkat_sinyali_dtse_katmanina_donusur():
    engine = DTSEAttentionEngine(
        minimum_confidence=60.0
    )

    result = engine.ingest(
        media_id="photo-001",
        source_kind="image",
        frame_index=0,
        timestamp_ms=0,
        frame_width=1920,
        frame_height=1080,
        signals=[
            AttentionSignal(
                label="Taş yüzey anomalisi",
                kind="anomaly",
                confidence=93.7,
                box=NormalizedBox(
                    x=0.25,
                    y=0.20,
                    width=0.30,
                    height=0.40,
                ),
                description=(
                    "Yüzey dokusunda dikkat "
                    "çeken bölge."
                ),
                metrics={
                    "texture_delta": 0.82,
                },
            )
        ],
    )

    assert result["created_count"] == 1
    assert result["ignored_count"] == 0

    event = result["events"][0]

    assert event["media_id"] == "photo-001"
    assert event["source_kind"] == "image"

    assert event["syframe"]["state"] == (
        "rare_anomaly"
    )

    assert (
        event["visual_layer"]["corner_style"]
        == "crescent_curve"
    )

    assert (
        event["visual_layer"]["border_style"]
        == "dotted"
    )

    assert event["visual_layer"]["pulse"]

    assert (
        "cross_validation"
        in event["analysis"][
            "requested_modules"
        ]
    )

    assert len(event["event_sha256"]) == 64


def test_video_karelerinde_yakin_tekrar_bastirilir():
    engine = DTSEAttentionEngine(
        duplicate_window_frames=12
    )

    signal = AttentionSignal(
        label="Oyuk adayı",
        kind="geometry",
        confidence=88.0,
        box=NormalizedBox(
            x=0.10,
            y=0.12,
            width=0.20,
            height=0.18,
        ),
    )

    first = engine.ingest(
        media_id="video-001",
        source_kind="video",
        frame_index=20,
        timestamp_ms=800,
        frame_width=1280,
        frame_height=720,
        signals=[signal],
    )

    second = engine.ingest(
        media_id="video-001",
        source_kind="video",
        frame_index=25,
        timestamp_ms=1000,
        frame_width=1280,
        frame_height=720,
        signals=[signal],
    )

    assert first["created_count"] == 1
    assert second["created_count"] == 0

    assert second["ignored"][0]["reason"] == (
        "duplicate_window"
    )


def test_dusuk_guvenli_sinyal_gorsellestirilmez():
    engine = DTSEAttentionEngine(
        minimum_confidence=60.0
    )

    result = engine.ingest(
        media_id="live-001",
        source_kind="live",
        frame_index=1,
        timestamp_ms=33,
        frame_width=1920,
        frame_height=1080,
        signals=[
            AttentionSignal(
                label="Zayıf işaret",
                kind="texture",
                confidence=42.0,
                box=NormalizedBox(
                    x=0.1,
                    y=0.1,
                    width=0.2,
                    height=0.2,
                ),
            )
        ],
    )

    assert result["created_count"] == 0
    assert result["ignored_count"] == 1