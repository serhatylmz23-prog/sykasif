from __future__ import annotations

from syk_core import (
    LayerCatalog,
    LayerCategory,
    LayerRecommendationEngine,
    ResearchCategory,
)


def test_archaeology_recommendations_prioritize_history() -> None:
    engine = LayerRecommendationEngine(
        LayerCatalog.create_default()
    )

    recommendations = engine.recommend(
        ResearchCategory.ARCHAEOLOGY,
        online_available=True,
        device_data_available=True,
    )

    codes = [
        recommendation.definition.code
        for recommendation in recommendations
    ]

    assert "archaeology" in codes
    assert "history" in codes
    assert "temporal" in codes
    assert "lidar" in codes
    assert "gps" in codes


def test_offline_mode_excludes_satellite() -> None:
    engine = LayerRecommendationEngine(
        LayerCatalog.create_default()
    )

    recommendations = engine.recommend(
        ResearchCategory.GENERAL,
        online_available=False,
        device_data_available=False,
    )

    codes = {
        recommendation.definition.code
        for recommendation in recommendations
    }

    assert "satellite" not in codes
    assert "gps" not in codes
    assert "rtk" not in codes
    assert "base_map" in codes


def test_no_device_data_excludes_measurement_layers() -> None:
    engine = LayerRecommendationEngine(
        LayerCatalog.create_default()
    )

    recommendations = engine.recommend(
        ResearchCategory.GEOLOGY,
        online_available=True,
        device_data_available=False,
    )

    categories = {
        recommendation.definition.category
        for recommendation in recommendations
    }

    assert LayerCategory.GEOLOGY in categories
    assert LayerCategory.MAGNETIC not in categories
    assert LayerCategory.ERT not in categories
    assert LayerCategory.SEISMIC not in categories


def test_recommendation_limit_is_applied() -> None:
    engine = LayerRecommendationEngine(
        LayerCatalog.create_default()
    )

    recommendations = engine.recommend(
        ResearchCategory.MULTIDISCIPLINARY,
        online_available=True,
        device_data_available=True,
        limit=5,
    )

    assert len(recommendations) == 5
    assert recommendations[0].score >= recommendations[-1].score
