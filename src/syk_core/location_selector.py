"""Konum merkezli katman seçimi."""

from __future__ import annotations

from dataclasses import dataclass

from .enums import ResearchCategory
from .layer import LayerRecord
from .layer_recommender import (
    LayerRecommendation,
    LayerRecommendationEngine,
)
from .location import ResearchArea


@dataclass(slots=True, frozen=True)
class LayerSelectionResult:
    """Konum için seçilen katmanlar ve öneriler."""

    area: ResearchArea
    selected_layers: tuple[LayerRecord, ...]
    recommendations: tuple[LayerRecommendation, ...]
    automatic_layer_ids: tuple[str, ...]

    @property
    def layer_count(self) -> int:
        return len(self.selected_layers)


class LocationLayerSelector:
    """Araştırma alanına göre katman kayıtları üretir."""

    def __init__(
        self,
        recommendation_engine: LayerRecommendationEngine,
    ) -> None:
        self._recommendation_engine = recommendation_engine

    def select(
        self,
        *,
        area: ResearchArea,
        research_category: ResearchCategory,
        online_available: bool,
        device_data_available: bool,
        recommendation_limit: int = 12,
    ) -> LayerSelectionResult:
        """Konum ve araştırma türü için katmanları oluşturur."""

        recommendations = self._recommendation_engine.recommend(
            research_category,
            online_available=online_available,
            device_data_available=device_data_available,
            limit=recommendation_limit,
        )

        records: list[LayerRecord] = []
        automatic_layer_ids: list[str] = []

        for recommendation in recommendations:
            record = recommendation.definition.create_record(
                metadata={
                    "selection_center": area.center.to_dict(),
                    "selection_radius_m": area.radius_m,
                    "recommendation_score": recommendation.score,
                    "recommendation_reason": recommendation.reason,
                    "automatic": recommendation.automatic,
                }
            )

            if recommendation.automatic:
                record.activate()
                automatic_layer_ids.append(
                    record.identity.syk_id or ""
                )

            records.append(record)

        return LayerSelectionResult(
            area=area,
            selected_layers=tuple(records),
            recommendations=recommendations,
            automatic_layer_ids=tuple(automatic_layer_ids),
        )
