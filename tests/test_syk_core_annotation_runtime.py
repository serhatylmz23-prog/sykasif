from __future__ import annotations

from syk_core.ovm import (
    AnnotationRuntimeEngine,
    BoundingRegion,
    NormalizedPoint,
    SurfaceFeature,
    SurfaceFeatureKind,
    SurfaceSeverity,
    VisualStatus,
)


def create_feature(
    *,
    feature_id: str,
    confidence_score: float,
    kind: SurfaceFeatureKind,
) -> SurfaceFeature:
    return SurfaceFeature(
        feature_id=feature_id,
        kind=kind,
        title=feature_id,
        region=BoundingRegion(
            top_left=NormalizedPoint(
                x=0.10,
                y=0.10,
            ),
            bottom_right=NormalizedPoint(
                x=0.40,
                y=0.40,
            ),
        ),
        confidence_score=confidence_score,
        severity=SurfaceSeverity.MEDIUM,
    )


def test_annotation_runtime_creates_dynamic_instruction() -> None:
    engine = AnnotationRuntimeEngine()

    feature = create_feature(
        feature_id="MANYETİK-ANOMALİ-001",
        confidence_score=93.0,
        kind=SurfaceFeatureKind.SPECTRAL_ANOMALY,
    )

    annotation = engine.create_feature_annotation(
        feature=feature,
        target_entity_id="SYK-OVM-TEST",
    )

    instruction = engine.render_instruction(
        annotation_id="SYK-FRAME-001",
        annotation=annotation,
    )

    payload = instruction.to_runtime_dict()

    assert payload["işaret_kimliği"] == "SYK-FRAME-001"
    assert payload["nabız"] is True
    assert payload["durum"] == "rare_anomaly"
    assert payload["ikon"] == "syk-frame-rare-anomaly"
    assert payload["üst_veri"]["dynamic"] is True


def test_manual_annotation_is_not_auto_generated() -> None:
    engine = AnnotationRuntimeEngine()

    annotation = engine.create_manual_annotation(
        title="Kullanıcı Notu",
        description="Taş yüzeyinde işaretlenen alan.",
        region=BoundingRegion(
            top_left=NormalizedPoint(
                x=0.20,
                y=0.25,
            ),
            bottom_right=NormalizedPoint(
                x=0.65,
                y=0.75,
            ),
        ),
        status=VisualStatus.REFERENCE,
    )

    assert (
        annotation.metadata["auto_generated"]
        is False
    )
    assert annotation.metadata["source"] == "SyFrame"


def test_render_many_prioritizes_critical_status() -> None:
    engine = AnnotationRuntimeEngine()

    critical = engine.create_manual_annotation(
        title="Kritik Alan",
        region=BoundingRegion(
            top_left=NormalizedPoint(0.1, 0.1),
            bottom_right=NormalizedPoint(0.2, 0.2),
        ),
        status=VisualStatus.CRITICAL,
    )

    verified = engine.create_manual_annotation(
        title="Doğrulanmış Alan",
        region=BoundingRegion(
            top_left=NormalizedPoint(0.3, 0.3),
            bottom_right=NormalizedPoint(0.4, 0.4),
        ),
        status=VisualStatus.VERIFIED,
    )

    instructions = engine.render_many(
        (
            ("FRAME-VERIFIED", verified),
            ("FRAME-CRITICAL", critical),
        )
    )

    assert (
        instructions[0].visual_status
        == VisualStatus.CRITICAL
    )
    assert (
        instructions[1].visual_status
        == VisualStatus.VERIFIED
    )
