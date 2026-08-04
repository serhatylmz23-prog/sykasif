from __future__ import annotations

from syk_core import (
    AccuracySource,
    EntityStatus,
    LayerCatalog,
    LayerRecommendationEngine,
    LocationLayerSelector,
    PinCreationRequest,
    PinSource,
    ResearchCategory,
    ResearchPinFlow,
)


def create_flow() -> ResearchPinFlow:
    catalog = LayerCatalog.create_default()
    recommender = LayerRecommendationEngine(catalog)
    selector = LocationLayerSelector(recommender)

    return ResearchPinFlow(selector)


def test_live_gps_pin_creates_active_research_point() -> None:
    flow = create_flow()

    result = flow.create(
        PinCreationRequest(
            title="Canlı GPS Araştırma Noktası",
            latitude=37.2234,
            longitude=38.9221,
            altitude_m=742.5,
            horizontal_accuracy_m=4.2,
            category=ResearchCategory.ARCHAEOLOGY,
            source=PinSource.LIVE_GPS,
            radius_m=150.0,
            online_available=True,
            device_data_available=True,
            tags=frozenset(
                {
                    "saha",
                    "arkeoloji",
                }
            ),
        )
    )

    point = result.research_point

    assert point.status == EntityStatus.ACTIVE
    assert (
        point.location.accuracy_source
        == AccuracySource.DEVICE_GPS
    )
    assert point.area is not None
    assert point.area.radius_m == 150.0
    assert len(point.layers) > 5
    assert len(result.repository) == len(point.layers)
    assert result.activated_layer_count >= 2
    assert point.metadata["pin_source"] == "live_gps"


def test_rtk_pin_uses_fixed_accuracy_source() -> None:
    flow = create_flow()

    result = flow.create(
        PinCreationRequest(
            title="RTK Noktası",
            latitude=39.0,
            longitude=35.0,
            horizontal_accuracy_m=0.018,
            category=ResearchCategory.GEOLOGY,
            source=PinSource.RTK,
            online_available=False,
            device_data_available=True,
        )
    )

    point = result.research_point

    assert (
        point.location.accuracy_source
        == AccuracySource.RTK_FIXED
    )

    layer_codes = {
        layer.metadata.get("catalog_code")
        for layer in point.layers.values()
    }

    assert "rtk" in layer_codes
    assert "geology" in layer_codes
    assert "satellite" not in layer_codes


def test_manual_map_pin_does_not_require_device_data() -> None:
    flow = create_flow()

    result = flow.create(
        PinCreationRequest(
            title="Haritada İşaretlenen Nokta",
            latitude=41.0082,
            longitude=28.9784,
            category=ResearchCategory.HISTORY,
            source=PinSource.MANUAL_MAP,
            online_available=True,
            device_data_available=False,
        )
    )

    point = result.research_point

    assert (
        point.location.accuracy_source
        == AccuracySource.MANUAL
    )

    layer_codes = {
        layer.metadata.get("catalog_code")
        for layer in point.layers.values()
    }

    assert "history" in layer_codes
    assert "temporal" in layer_codes
    assert "satellite" in layer_codes
    assert "lidar" not in layer_codes
    assert "gps" not in layer_codes


def test_automatic_layers_are_visible() -> None:
    flow = create_flow()

    result = flow.create(
        PinCreationRequest(
            title="Otomatik Katman Testi",
            latitude=38.9637,
            longitude=35.2433,
            category=ResearchCategory.GENERAL,
            source=PinSource.COORDINATE_INPUT,
            online_available=False,
            device_data_available=False,
        )
    )

    activated_ids = set(result.selection.automatic_layer_ids)
    visible_ids = {
        layer.identity.syk_id
        for layer in result.research_point.visible_layers
    }

    assert activated_ids
    assert activated_ids.issubset(visible_ids)


def test_water_research_selects_water_layers() -> None:
    flow = create_flow()

    result = flow.create(
        PinCreationRequest(
            title="Su Araştırma Noktası",
            latitude=36.8,
            longitude=34.6,
            category=ResearchCategory.WATER,
            source=PinSource.MANUAL_MAP,
            online_available=True,
            device_data_available=True,
        )
    )

    codes = {
        layer.metadata.get("catalog_code")
        for layer in result.research_point.layers.values()
    }

    assert "hydrology" in codes
    assert "hydrogeology" in codes
    assert "water" in codes
    assert "thermal" in codes
