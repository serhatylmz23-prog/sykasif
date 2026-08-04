"""Araştırma türüne göre katman önerisi."""

from __future__ import annotations

from dataclasses import dataclass

from .enums import LayerCategory, ResearchCategory
from .layer_catalog import LayerCatalog, LayerDefinition


@dataclass(slots=True, frozen=True)
class LayerRecommendation:
    """Tek bir katman önerisi."""

    definition: LayerDefinition
    score: int
    reason: str
    automatic: bool

    def __post_init__(self) -> None:
        if not 0 <= self.score <= 100:
            raise ValueError(
                "Katman öneri puanı 0 ile 100 arasında olmalıdır."
            )


class LayerRecommendationEngine:
    """Araştırma türüne göre öncelikli katmanları belirler."""

    _PRIMARY_CATEGORIES: dict[
        ResearchCategory,
        frozenset[LayerCategory],
    ] = {
        ResearchCategory.GENERAL: frozenset(
            {
                LayerCategory.BASE_MAP,
                LayerCategory.SATELLITE,
                LayerCategory.TOPOGRAPHY,
                LayerCategory.GPS,
                LayerCategory.EVIDENCE,
            }
        ),
        ResearchCategory.ARCHAEOLOGY: frozenset(
            {
                LayerCategory.ARCHAEOLOGY,
                LayerCategory.HISTORY,
                LayerCategory.TEMPORAL,
                LayerCategory.TOPOGRAPHY,
                LayerCategory.LIDAR,
                LayerCategory.GEOLOGY,
                LayerCategory.EVIDENCE,
            }
        ),
        ResearchCategory.HISTORY: frozenset(
            {
                LayerCategory.HISTORY,
                LayerCategory.TEMPORAL,
                LayerCategory.ARCHAEOLOGY,
                LayerCategory.ROADS,
                LayerCategory.EVIDENCE,
            }
        ),
        ResearchCategory.GEOLOGY: frozenset(
            {
                LayerCategory.GEOLOGY,
                LayerCategory.TOPOGRAPHY,
                LayerCategory.GRAVITY,
                LayerCategory.MAGNETIC,
                LayerCategory.ERT,
                LayerCategory.SEISMIC,
                LayerCategory.EVIDENCE,
            }
        ),
        ResearchCategory.HYDROGEOLOGY: frozenset(
            {
                LayerCategory.HYDROGEOLOGY,
                LayerCategory.HYDROLOGY,
                LayerCategory.TOPOGRAPHY,
                LayerCategory.SOIL,
                LayerCategory.THERMAL,
                LayerCategory.EVIDENCE,
            }
        ),
        ResearchCategory.BOTANY: frozenset(
            {
                LayerCategory.VEGETATION,
                LayerCategory.BOTANICAL,
                LayerCategory.SOIL,
                LayerCategory.WATER,
                LayerCategory.SPECTRAL,
                LayerCategory.EVIDENCE,
            }
        ),
        ResearchCategory.SOIL: frozenset(
            {
                LayerCategory.SOIL,
                LayerCategory.GEOLOGY,
                LayerCategory.VEGETATION,
                LayerCategory.WATER,
                LayerCategory.SPECTRAL,
                LayerCategory.EVIDENCE,
            }
        ),
        ResearchCategory.WATER: frozenset(
            {
                LayerCategory.HYDROLOGY,
                LayerCategory.HYDROGEOLOGY,
                LayerCategory.WATER,
                LayerCategory.TOPOGRAPHY,
                LayerCategory.THERMAL,
                LayerCategory.EVIDENCE,
            }
        ),
        ResearchCategory.ASTRONOMY: frozenset(
            {
                LayerCategory.TEMPORAL,
                LayerCategory.TOPOGRAPHY,
                LayerCategory.CUSTOM,
                LayerCategory.EVIDENCE,
            }
        ),
        ResearchCategory.ARCHAEOSTRONOMY: frozenset(
            {
                LayerCategory.TEMPORAL,
                LayerCategory.ARCHAEOLOGY,
                LayerCategory.HISTORY,
                LayerCategory.TOPOGRAPHY,
                LayerCategory.CUSTOM,
                LayerCategory.EVIDENCE,
            }
        ),
        ResearchCategory.ENVIRONMENT: frozenset(
            {
                LayerCategory.VEGETATION,
                LayerCategory.HYDROLOGY,
                LayerCategory.SOIL,
                LayerCategory.WATER,
                LayerCategory.THERMAL,
                LayerCategory.SPECTRAL,
                LayerCategory.EVIDENCE,
            }
        ),
        ResearchCategory.MULTIDISCIPLINARY: frozenset(
            category
            for category in LayerCategory
            if category != LayerCategory.REPORT
        ),
    }

    _AUTOMATIC_CATEGORIES = frozenset(
        {
            LayerCategory.BASE_MAP,
            LayerCategory.GPS,
            LayerCategory.RTK,
            LayerCategory.EVIDENCE,
        }
    )

    def __init__(
        self,
        catalog: LayerCatalog,
    ) -> None:
        self._catalog = catalog

    def recommend(
        self,
        research_category: ResearchCategory,
        *,
        online_available: bool,
        device_data_available: bool,
        limit: int | None = None,
    ) -> tuple[LayerRecommendation, ...]:
        """Koşullara göre katman önerilerini üretir."""

        if limit is not None and limit < 1:
            raise ValueError("Öneri limiti en az 1 olmalıdır.")

        primary = self._PRIMARY_CATEGORIES[research_category]
        recommendations: list[LayerRecommendation] = []

        for definition in self._catalog.compatible_with(
            research_category
        ):
            if (
                definition.requires_online_source
                and not online_available
            ):
                continue

            if (
                definition.requires_device_data
                and not device_data_available
            ):
                continue

            is_primary = definition.category in primary
            automatic = (
                definition.category in self._AUTOMATIC_CATEGORIES
            )

            score = definition.default_priority

            if is_primary:
                score = min(100, score + 7)

            if automatic:
                score = min(100, score + 5)

            reason_parts = [
                f"{research_category.value} araştırmasıyla uyumlu"
            ]

            if is_primary:
                reason_parts.append("ana inceleme katmanı")

            if automatic:
                reason_parts.append("otomatik yükleme adayı")

            recommendations.append(
                LayerRecommendation(
                    definition=definition,
                    score=score,
                    reason="; ".join(reason_parts),
                    automatic=automatic,
                )
            )

        recommendations.sort(
            key=lambda item: (
                -item.score,
                item.definition.code,
            )
        )

        if limit is not None:
            recommendations = recommendations[:limit]

        return tuple(recommendations)
