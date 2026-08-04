from __future__ import annotations

import json

from syk_core import (
    AccuracySource,
    EntityStatus,
    EvidenceKind,
    EvidenceRecord,
    GeoLocation,
    LayerCategory,
    LayerRecord,
    ResearchCategory,
    ResearchPoint,
)


def test_research_point_payload_is_json_serializable() -> None:
    point = ResearchPoint(
        title="JSON Uyum Testi",
        location=GeoLocation(
            latitude=38.9637,
            longitude=35.2433,
            horizontal_accuracy_m=4.5,
            accuracy_source=AccuracySource.DEVICE_GPS,
        ),
        category=ResearchCategory.MULTIDISCIPLINARY,
    )

    point.add_layer(
        LayerRecord(
            name="Topografya",
            category=LayerCategory.TOPOGRAPHY,
            visible=True,
            opacity=0.75,
        )
    )

    point.add_evidence(
        EvidenceRecord(
            title="Koordinat Kanıtı",
            kind=EvidenceKind.GPS,
        )
    )

    point.transition_to(EntityStatus.ACTIVE)

    serialized = json.dumps(
        point.to_dict(),
        ensure_ascii=False,
        sort_keys=True,
    )

    assert "JSON Uyum Testi" in serialized
    assert "topography" in serialized
    assert "coordinate_system" in serialized
