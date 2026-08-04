from __future__ import annotations

import pytest

from syk_core.ovm import (
    BoundingRegion,
    NormalizedPoint,
    SurfaceFeature,
    SurfaceFeatureKind,
    SurfaceInput,
    SurfaceInputKind,
    SurfaceIntelligenceEngine,
    SurfaceMeasurement,
    SurfaceSeverity,
    VisualStatus,
)


def create_features() -> tuple[SurfaceFeature, ...]:
    crack = SurfaceFeature(
        feature_id="ÇATLAK-003",
        kind=SurfaceFeatureKind.CRACK,
        title="Çatlak-03",
        description="Yüzey boyunca uzanan ince çatlak.",
        region=BoundingRegion(
            top_left=NormalizedPoint(
                x=0.10,
                y=0.20,
            ),
            bottom_right=NormalizedPoint(
                x=0.44,
                y=0.62,
            ),
        ),
        confidence_score=96.1,
        severity=SurfaceSeverity.MEDIUM,
        depth_m=0.032,
        width_m=0.014,
        length_m=0.146,
    )
    crack.add_measurement(
        SurfaceMeasurement(
            name="Ortalama genişlik",
            value=1.2,
            unit="mm",
            minimum=0.0,
            maximum=5.0,
        )
    )
    crack.add_evidence(
        "SYK-EVD-FOTO-001"
    )

    cavity = SurfaceFeature(
        feature_id="OYUK-001",
        kind=SurfaceFeatureKind.CAVITY,
        title="Oyuk-01",
        description="Yüzey altında olası boşluk.",
        region=BoundingRegion(
            top_left=NormalizedPoint(
                x=0.52,
                y=0.15,
            ),
            bottom_right=NormalizedPoint(
                x=0.80,
                y=0.46,
            ),
        ),
        confidence_score=39.4,
        severity=SurfaceSeverity.HIGH,
        depth_m=0.78,
        width_m=0.234,
    )

    anomaly = SurfaceFeature(
        feature_id="SPEKTRAL-009",
        kind=SurfaceFeatureKind.SPECTRAL_ANOMALY,
        title="Spektral Anomali",
        region=BoundingRegion(
            top_left=NormalizedPoint(
                x=0.64,
                y=0.55,
            ),
            bottom_right=NormalizedPoint(
                x=0.91,
                y=0.89,
            ),
        ),
        confidence_score=93.0,
        severity=SurfaceSeverity.MEDIUM,
    )

    return (
        crack,
        cavity,
        anomaly,
    )


def test_surface_engine_creates_entities_and_annotations() -> None:
    engine = SurfaceIntelligenceEngine()

    result = engine.analyze(
        analysis_id="SYK-DTSE-TEST-001",
        inputs=(
            SurfaceInput(
                input_id="NOKTA-BULUTU-001",
                kind=SurfaceInputKind.POINT_CLOUD,
                point_count=1_200_000,
            ),
            SurfaceInput(
                input_id="ADAPTİF-AĞ-001",
                kind=SurfaceInputKind.ADAPTIVE_MESH,
                vertex_count=260_000,
            ),
        ),
        features=create_features(),
        source_research_point_id=(
            "SYK-RP-TEST-001"
        ),
    )

    assert len(result.entities) == 3
    assert len(result.annotations) == 3
    assert len(result.stages) == 7
    assert result.review_required is True
    assert result.overall_confidence == 76.167

    feature_ids = {
        entity.metadata["feature_id"]
        for entity in result.entities
    }

    assert feature_ids == {
        "ÇATLAK-003",
        "OYUK-001",
        "SPEKTRAL-009",
    }


def test_surface_engine_assigns_dynamic_visual_status() -> None:
    engine = SurfaceIntelligenceEngine()

    result = engine.analyze(
        analysis_id="SYK-DTSE-TEST-002",
        inputs=(
            SurfaceInput(
                input_id="GÖRÜNTÜ-001",
                kind=SurfaceInputKind.PHOTO,
                width_px=1920,
                height_px=1080,
            ),
        ),
        features=create_features(),
    )

    statuses = {
        entity.metadata["feature_id"]:
        entity.visual_status
        for entity in result.entities
    }

    assert (
        statuses["ÇATLAK-003"]
        == VisualStatus.ANALYZING
    )
    assert (
        statuses["OYUK-001"]
        == VisualStatus.REVIEW_REQUIRED
    )
    assert (
        statuses["SPEKTRAL-009"]
        == VisualStatus.RARE_ANOMALY
    )


def test_surface_runtime_payload_preserves_turkish() -> None:
    engine = SurfaceIntelligenceEngine()

    result = engine.analyze(
        analysis_id="SYK-DTSE-TÜRKÇE-001",
        inputs=(
            SurfaceInput(
                input_id="YÜZEY-GÖRÜNTÜSÜ-001",
                kind=SurfaceInputKind.PHOTO,
            ),
        ),
        features=create_features(),
    )

    payload = result.to_runtime_dict()

    assert payload["tespit_sayısı"] == 3
    assert "genel_güven" in payload
    assert (
        payload["tespitler"][0][
            "özellik_kimliği"
        ]
        == "ÇATLAK-003"
    )


def test_surface_measurement_limits() -> None:
    measurement = SurfaceMeasurement(
        name="Pürüzlülük",
        value=0.62,
        unit="mm",
        minimum=0.10,
        maximum=1.00,
    )

    assert measurement.within_limits is True

    measurement.value = 2.0

    assert measurement.within_limits is False


def test_bounding_region_geometry() -> None:
    region = BoundingRegion(
        top_left=NormalizedPoint(
            x=0.20,
            y=0.30,
        ),
        bottom_right=NormalizedPoint(
            x=0.70,
            y=0.80,
        ),
    )

    assert region.width == pytest.approx(0.5)
    assert region.height == pytest.approx(0.5)
    assert region.area_ratio == pytest.approx(0.25)
    assert region.center.x == pytest.approx(0.45)
    assert region.center.y == pytest.approx(0.55)

