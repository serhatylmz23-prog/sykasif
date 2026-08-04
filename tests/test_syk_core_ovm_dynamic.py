from __future__ import annotations

import json

from syk_core import GeoLocation, ResearchCategory
from syk_core.ovm import (
    AnnotationRecord,
    AnnotationShape,
    AnnotationStyle,
    ConfidenceLevel,
    DynamicLayerContext,
    DynamicLayerEngine,
    EntityKind,
    OvmEntity,
    OvmEntityRegistry,
    RuntimeState,
    VisualStatus,
    get_turkish_label,
)


def test_turkish_labels_are_utf8_safe() -> None:
    labels = [
        get_turkish_label(EntityKind.HISTORICAL_SITE),
        get_turkish_label(EntityKind.AI_ANALYSIS),
        get_turkish_label(RuntimeState.ANALYZING),
        get_turkish_label(VisualStatus.REVIEW_REQUIRED),
        get_turkish_label(ConfidenceLevel.VERY_HIGH),
    ]

    assert labels == [
        "Tarihî Alan",
        "Yapay Zekâ Analizi",
        "Analiz Ediliyor",
        "İncelenmeli",
        "Çok Yüksek",
    ]

    for label in labels:
        assert label.encode("utf-8").decode("utf-8") == label


def test_ovm_entity_generates_turkish_runtime_payload() -> None:
    entity = OvmEntity(
        kind=EntityKind.STATUE,
        title="Geç Hitit Dönemi Taş Heykeli",
        description="Arkeolojik alanda gözlenen insan figürü.",
        location=GeoLocation(
            latitude=37.128456,
            longitude=38.789123,
        ),
        runtime_state=RuntimeState.ANALYZING,
        visual_status=VisualStatus.ANALYZING,
        confidence_score=82.5,
        icon_code="syk-heykel",
    )

    payload = entity.to_runtime_dict()
    serialized = json.dumps(
        payload,
        ensure_ascii=False,
    )

    assert payload["tür"] == "Heykel"
    assert payload["çalışma_durumu"] == "Analiz Ediliyor"
    assert payload["güven_düzeyi"] == "Çok Yüksek"
    assert "Geç Hitit Dönemi" in serialized
    assert "\\u" not in serialized


def test_confidence_score_changes_level() -> None:
    entity = OvmEntity(
        kind=EntityKind.CRACK,
        title="Çatlak-03",
    )

    entity.set_confidence_score(18.0)
    assert entity.confidence_level == ConfidenceLevel.VERY_LOW

    entity.set_confidence_score(74.0)
    assert entity.confidence_level == ConfidenceLevel.HIGH

    entity.set_confidence_score(99.9)
    assert entity.confidence_level == ConfidenceLevel.VERIFIED


def test_registry_stores_multiple_entity_kinds() -> None:
    registry = OvmEntityRegistry()

    crack = OvmEntity(
        kind=EntityKind.CRACK,
        title="Çatlak",
    )
    fish = OvmEntity(
        kind=EntityKind.FISH_SPECIES,
        title="Sazan",
    )

    registry.add(crack)
    registry.add(fish)

    assert len(registry) == 2
    assert registry.get(crack.entity_id) is crack
    assert registry.by_kind(EntityKind.FISH_SPECIES) == (fish,)


def test_annotation_rectangle_uses_dynamic_status_style() -> None:
    annotation = AnnotationRecord(
        title="Manyetik Anomali",
        description="Nadir anomali olarak işaretlendi.",
        shape=AnnotationShape.RECTANGLE,
        points=(
            (0.20, 0.15),
            (0.72, 0.84),
        ),
        style=AnnotationStyle.from_status(
            VisualStatus.RARE_ANOMALY
        ),
    )

    payload = annotation.to_dict()

    assert payload["title"] == "Manyetik Anomali"
    assert payload["style"]["pulse"] is True
    assert payload["style"]["status"] == "rare_anomaly"
    assert payload["style"]["glow_strength"] == 0.65


def test_dynamic_layer_engine_hides_device_layer_without_data() -> None:
    entity = OvmEntity(
        kind=EntityKind.LIDAR,
        title="Lidar Nokta Bulutu",
        runtime_state=RuntimeState.ACTIVE,
    )

    engine = DynamicLayerEngine()
    context = DynamicLayerContext(
        research_category=ResearchCategory.ARCHAEOLOGY,
        gps_available=True,
        rtk_available=False,
        online_available=True,
        device_data_available=False,
    )

    result = engine.apply(
        entity,
        context,
    )

    assert result.visible is False
    assert result.runtime_state == RuntimeState.WAITING
    assert entity.icon_code == "syk-lidar"


def test_dynamic_layer_engine_marks_low_confidence() -> None:
    entity = OvmEntity(
        kind=EntityKind.CAVITY,
        title="Boşluk / Mağara",
        confidence_score=22.0,
        opacity=1.0,
    )

    engine = DynamicLayerEngine()
    context = DynamicLayerContext(
        research_category=ResearchCategory.GEOLOGY,
        gps_available=True,
        rtk_available=True,
        online_available=False,
        device_data_available=True,
    )

    result = engine.apply(
        entity,
        context,
    )

    assert result.visible is True
    assert result.visual_status == VisualStatus.LOW_CONFIDENCE
    assert result.opacity == 0.72


def test_fish_entity_is_supported_by_common_model() -> None:
    fish = OvmEntity(
        kind=EntityKind.FISH_SPECIES,
        title="Fırat Turnası",
        description="Tatlı su balık türü.",
        layer_code="fish_species",
        metadata={
            "su_türü": "Tatlı Su",
            "bölge": "Keban Baraj Gölü",
            "koruma_durumu": "İncelenmeli",
        },
    )

    assert fish.turkish_kind == "Balık Türü"
    assert fish.metadata["su_türü"] == "Tatlı Su"
    assert fish.to_runtime_dict()["başlık"] == "Fırat Turnası"
