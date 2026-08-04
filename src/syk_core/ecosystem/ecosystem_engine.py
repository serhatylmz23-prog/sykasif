"""Balık ve bitki katmanlarını ortak ekosistem sonucunda birleştirir."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..ovm import (
    EntityKind,
    OvmEntity,
    RuntimeState,
    VisualStatus,
)
from .fish_engine import (
    DynamicFishLayerEngine,
    FishLayerResult,
    FishObservation,
    FishSpeciesProfile,
)
from .plant_engine import (
    DynamicPlantLayerEngine,
    PlantLayerResult,
    PlantObservation,
    PlantSpeciesProfile,
)
from .runtime_context import EcosystemRuntimeContext


@dataclass(slots=True, frozen=True)
class EcosystemAnalysisResult:
    """Ortak canlı ekosistem değerlendirmesi."""

    fish_result: FishLayerResult
    plant_result: PlantLayerResult
    entities: tuple[OvmEntity, ...]
    recommendations: tuple[str, ...]
    dynamic: bool = True

    def to_runtime_dict(self) -> dict[str, Any]:
        return {
            "dinamik": self.dynamic,
            "balık_katmanı": (
                self.fish_result.to_runtime_dict()
            ),
            "bitki_katmanı": (
                self.plant_result.to_runtime_dict()
            ),
            "öneriler": list(self.recommendations),
            "varlıklar": [
                entity.to_runtime_dict()
                for entity in self.entities
            ],
        }


class EcosystemRuntimeEngine:
    """Canlı ekosistem katmanlarını OVM içine bağlar."""

    def __init__(self) -> None:
        self.fish_engine = DynamicFishLayerEngine()
        self.plant_engine = DynamicPlantLayerEngine()

    def analyze(
        self,
        *,
        context: EcosystemRuntimeContext,
        fish_profiles: tuple[
            FishSpeciesProfile,
            ...,
        ],
        plant_profiles: tuple[
            PlantSpeciesProfile,
            ...,
        ],
        fish_observations: tuple[
            FishObservation,
            ...,
        ] = tuple(),
        plant_observations: tuple[
            PlantObservation,
            ...,
        ] = tuple(),
    ) -> EcosystemAnalysisResult:
        fish_result = self.fish_engine.evaluate(
            context=context,
            species_profiles=fish_profiles,
            observations=fish_observations,
        )

        plant_result = self.plant_engine.evaluate(
            context=context,
            species_profiles=plant_profiles,
            observations=plant_observations,
        )

        entities: list[OvmEntity] = []
        recommendations: list[str] = []

        for match in fish_result.matches:
            entity = OvmEntity(
                kind=EntityKind.FISH_SPECIES,
                title=match.species.turkish_name,
                description=(
                    "Dinamik balık türü eşleşmesi."
                ),
                location=context.location,
                layer_code="ecosystem.fish",
                runtime_state=RuntimeState.ANALYZING,
                visual_status=self._visual_status(
                    match.score
                ),
                confidence_score=match.score,
                icon_code=match.icon_code,
                metadata={
                    "species_id": (
                        match.species.species_id
                    ),
                    "dynamic_state": (
                        match.dynamic_state
                    ),
                    "reasons": list(match.reasons),
                    "warnings": list(match.warnings),
                    "water_body_name": (
                        context.water_body_name
                    ),
                    "dynamic": True,
                },
            )
            entities.append(entity)

        for match in plant_result.matches:
            entity = OvmEntity(
                kind=EntityKind.BOTANICAL,
                title=match.species.turkish_name,
                description=(
                    "Dinamik bitki türü eşleşmesi."
                ),
                location=context.location,
                layer_code="ecosystem.plant",
                runtime_state=RuntimeState.ANALYZING,
                visual_status=self._visual_status(
                    match.score
                ),
                confidence_score=match.score,
                icon_code=match.icon_code,
                metadata={
                    "species_id": (
                        match.species.species_id
                    ),
                    "dynamic_state": (
                        match.dynamic_state
                    ),
                    "reasons": list(match.reasons),
                    "warnings": list(match.warnings),
                    "ecosystem_clues": list(
                        match.ecosystem_clues
                    ),
                    "dynamic": True,
                },
            )
            entities.append(entity)

        if plant_result.water_indicator_score >= 65:
            recommendations.append(
                "Bitki dağılımı su varlığı açısından "
                "hidrojeoloji katmanıyla karşılaştırılmalı."
            )

        if (
            plant_result.disturbance_indicator_score
            >= 65
        ):
            recommendations.append(
                "Bitki deseni insan müdahalesi, eski yol "
                "ve yerleşim katmanlarıyla karşılaştırılmalı."
            )

        if fish_result.sonar_target_count > 0:
            recommendations.append(
                "Sonar hedefleri su sıcaklığı, oksijen ve "
                "derinlik katmanlarıyla birlikte incelenmeli."
            )

        if (
            fish_result.selected_species_ids
            and plant_result.selected_species_ids
        ):
            recommendations.append(
                "Balık ve bitki sonuçları ortak canlı "
                "ekosistem katmanında birlikte gösterilmeli."
            )

        return EcosystemAnalysisResult(
            fish_result=fish_result,
            plant_result=plant_result,
            entities=tuple(entities),
            recommendations=tuple(recommendations),
        )

    @staticmethod
    def _visual_status(
        score: float,
    ) -> VisualStatus:
        if score >= 99.9:
            return VisualStatus.VERIFIED

        if score >= 80:
            return VisualStatus.ANALYZING

        if score >= 60:
            return VisualStatus.REVIEW_REQUIRED

        return VisualStatus.LOW_CONFIDENCE
