from __future__ import annotations

from pathlib import Path

import pytest

from syk_core import (
    AccuracySource,
    EntityStatus,
    EvidenceKind,
    EvidenceRecord,
    EvidenceStatus,
    GeoLocation,
    InvalidCoordinateError,
    InvalidEntityStateError,
    LayerCategory,
    LayerRecord,
    LayerStatus,
    ResearchArea,
    ResearchCategory,
    ResearchPoint,
    VerificationLevel,
)


def test_geo_location_accepts_turkiye_coordinate() -> None:
    location = GeoLocation(
        latitude=37.2234,
        longitude=38.9221,
        altitude_m=742.5,
        horizontal_accuracy_m=0.02,
        accuracy_source=AccuracySource.RTK_FIXED,
    )

    assert location.latitude == pytest.approx(37.2234)
    assert location.longitude == pytest.approx(38.9221)
    assert location.altitude_m == pytest.approx(742.5)
    assert location.accuracy_source == AccuracySource.RTK_FIXED


@pytest.mark.parametrize(
    ("latitude", "longitude"),
    [
        (91.0, 30.0),
        (-91.0, 30.0),
        (40.0, 181.0),
        (40.0, -181.0),
    ],
)
def test_geo_location_rejects_invalid_coordinate(
    latitude: float,
    longitude: float,
) -> None:
    with pytest.raises(InvalidCoordinateError):
        GeoLocation(
            latitude=latitude,
            longitude=longitude,
        )


def test_location_distance_is_positive() -> None:
    first = GeoLocation(
        latitude=39.9334,
        longitude=32.8597,
    )
    second = GeoLocation(
        latitude=41.0082,
        longitude=28.9784,
    )

    distance = first.distance_to(second)

    assert distance > 300_000
    assert distance < 500_000


def test_research_area_defaults_to_radius_mode() -> None:
    center = GeoLocation(
        latitude=37.2234,
        longitude=38.9221,
    )
    area = ResearchArea(center=center)

    assert area.mode == "radius"
    assert area.radius_m == pytest.approx(100.0)


def test_polygon_requires_three_points() -> None:
    center = GeoLocation(
        latitude=37.0,
        longitude=38.0,
    )

    with pytest.raises(InvalidCoordinateError):
        ResearchArea(
            center=center,
            polygon=(
                GeoLocation(37.0, 38.0),
                GeoLocation(37.1, 38.1),
            ),
        )


def test_layer_can_be_activated_and_hidden() -> None:
    layer = LayerRecord(
        name="Jeolojik Formasyon",
        category=LayerCategory.GEOLOGY,
        status=LayerStatus.AVAILABLE,
        opacity=0.65,
        priority=90,
    )

    layer.activate()

    assert layer.visible is True
    assert layer.status == LayerStatus.ACTIVE

    layer.hide()

    assert layer.visible is False
    assert layer.status == LayerStatus.HIDDEN


def test_layer_opacity_validation() -> None:
    with pytest.raises(Exception):
        LayerRecord(
            name="Geçersiz",
            category=LayerCategory.CUSTOM,
            opacity=1.5,
        )


def test_evidence_file_hash_and_verification(
    tmp_path: Path,
) -> None:
    evidence_file = tmp_path / "kanit.txt"
    evidence_file.write_text(
        "SyKaşif kanıt bütünlüğü",
        encoding="utf-8",
    )

    evidence = EvidenceRecord(
        title="Saha Notu",
        kind=EvidenceKind.DOCUMENT,
    )

    evidence.attach_local_file(
        evidence_file,
        mime_type="text/plain",
    )

    assert evidence.sha256_digest is not None
    assert len(evidence.sha256_digest) == 64
    assert (
        evidence.verification_level
        == VerificationLevel.HASH_CONFIRMED
    )

    assert evidence.verify_local_file() is True
    assert evidence.status == EvidenceStatus.VERIFIED
    assert (
        evidence.verification_level
        == VerificationLevel.DIGITALLY_VERIFIED
    )


def test_evidence_detects_modified_file(
    tmp_path: Path,
) -> None:
    evidence_file = tmp_path / "foto.txt"
    evidence_file.write_text(
        "ilk veri",
        encoding="utf-8",
    )

    evidence = EvidenceRecord(
        title="Fotoğraf Kaydı",
        kind=EvidenceKind.PHOTO,
    )
    evidence.attach_local_file(evidence_file)

    evidence_file.write_text(
        "değiştirilmiş veri",
        encoding="utf-8",
    )

    assert evidence.verify_local_file() is False
    assert evidence.status == EvidenceStatus.REVIEW_REQUIRED


def test_research_point_full_flow(
    tmp_path: Path,
) -> None:
    location = GeoLocation(
        latitude=37.2234,
        longitude=38.9221,
        altitude_m=742.5,
        horizontal_accuracy_m=0.018,
        accuracy_source=AccuracySource.RTK_FIXED,
    )

    point = ResearchPoint(
        title="Şanlıurfa Araştırma Noktası",
        location=location,
        category=ResearchCategory.ARCHAEOLOGY,
        priority=95,
        tags={"Neolitik", "  Göbeklitepe  "},
    )

    geological_layer = LayerRecord(
        name="Jeolojik Katman",
        category=LayerCategory.GEOLOGY,
        opacity=0.70,
        priority=85,
    )
    lidar_layer = LayerRecord(
        name="Lidar Nokta Bulutu",
        category=LayerCategory.LIDAR,
        opacity=0.85,
        priority=95,
    )

    point.add_layers(
        [
            geological_layer,
            lidar_layer,
        ]
    )
    point.activate_layer(
        lidar_layer.identity.syk_id or ""
    )

    evidence_file = tmp_path / "saha_fotografi.bin"
    evidence_file.write_bytes(b"SYK-EVIDENCE-001")

    evidence = EvidenceRecord(
        title="Saha Fotoğrafı",
        kind=EvidenceKind.PHOTO,
    )
    evidence.attach_local_file(
        evidence_file,
        mime_type="image/jpeg",
    )
    assert evidence.verify_local_file() is True

    point.add_evidence(evidence)
    point.transition_to(EntityStatus.ACTIVE)
    point.transition_to(EntityStatus.PROCESSING)

    payload = point.to_dict()
    summary = point.summary()

    assert point.status == EntityStatus.PROCESSING
    assert len(point.layers) == 2
    assert len(point.visible_layers) == 1
    assert point.verified_evidence_count == 1
    assert "neolitik" in point.tags
    assert "göbeklitepe" in point.tags
    assert payload["category"] == "archaeology"
    assert summary["layer_count"] == 2
    assert summary["verified_evidence_count"] == 1


def test_invalid_status_transition_is_rejected() -> None:
    point = ResearchPoint(
        title="Durum Testi",
        location=GeoLocation(
            latitude=39.0,
            longitude=35.0,
        ),
    )

    with pytest.raises(InvalidEntityStateError):
        point.transition_to(EntityStatus.COMPLETED)
