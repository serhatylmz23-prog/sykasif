"""Dinamik bitki türü ve kamera gözlem motoru."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

from ..utils import json_safe, utc_now
from .enums import (
    ConservationState,
    EcosystemEntityType,
    ObservationSource,
    PlantCondition,
)
from .runtime_context import EcosystemRuntimeContext


@dataclass(slots=True, frozen=True)
class PlantSpeciesProfile:
    """Bitki türü ve habitat çalışma profili."""

    species_id: str
    turkish_name: str
    entity_type: EcosystemEntityType
    scientific_name: str | None = None

    supported_region_codes: frozenset[str] = frozenset()
    minimum_altitude_m: float | None = None
    maximum_altitude_m: float | None = None
    minimum_soil_moisture_percent: float | None = None
    maximum_soil_moisture_percent: float | None = None
    minimum_air_temperature_c: float | None = None
    maximum_air_temperature_c: float | None = None
    active_months: frozenset[int] = frozenset(
        range(1, 13)
    )

    water_indicator_score: float = 0.0
    disturbance_indicator_score: float = 0.0
    conservation_state: ConservationState = (
        ConservationState.UNKNOWN
    )
    icon_code: str | None = None
    source_pending: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.species_id.strip():
            raise ValueError(
                "Bitki türü kimliği boş olamaz."
            )

        if not self.turkish_name.strip():
            raise ValueError(
                "Bitki türü adı boş olamaz."
            )

        for name in (
            "water_indicator_score",
            "disturbance_indicator_score",
        ):
            value = float(getattr(self, name))

            if not 0.0 <= value <= 100.0:
                raise ValueError(
                    f"{name} 0 ile 100 arasında olmalıdır."
                )

        self._validate_range(
            self.minimum_altitude_m,
            self.maximum_altitude_m,
            "rakım",
        )
        self._validate_range(
            self.minimum_soil_moisture_percent,
            self.maximum_soil_moisture_percent,
            "toprak nemi",
        )
        self._validate_range(
            self.minimum_air_temperature_c,
            self.maximum_air_temperature_c,
            "hava sıcaklığı",
        )

    @staticmethod
    def _validate_range(
        minimum: float | None,
        maximum: float | None,
        field_name: str,
    ) -> None:
        if (
            minimum is not None
            and maximum is not None
            and minimum > maximum
        ):
            raise ValueError(
                f"{field_name} alt sınırı üst sınırdan büyük olamaz."
            )

    @property
    def resolved_icon_code(self) -> str:
        return (
            self.icon_code
            or (
                "syk-plant-"
                + self.species_id.casefold().replace(
                    "_",
                    "-",
                )
            )
        )


@dataclass(slots=True)
class PlantObservation:
    """Kamera veya fotoğraftan üretilen bitki gözlemi."""

    source: ObservationSource
    observation_id: str = field(
        default_factory=lambda: (
            f"SYK-PLANT-OBS-{uuid4().hex[:16].upper()}"
        )
    )
    detected_label: str | None = None
    model_confidence: float | None = None
    condition: PlantCondition = PlantCondition.UNKNOWN

    leaf_score: float | None = None
    flower_score: float | None = None
    bark_score: float | None = None
    fruit_score: float | None = None
    green_coverage_percent: float | None = None

    evidence_ids: set[str] = field(default_factory=set)
    observed_at: Any = field(default_factory=utc_now)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for name in (
            "model_confidence",
            "leaf_score",
            "flower_score",
            "bark_score",
            "fruit_score",
            "green_coverage_percent",
        ):
            value = getattr(self, name)

            if value is not None:
                normalized = float(value)

                if not 0.0 <= normalized <= 100.0:
                    raise ValueError(
                        f"{name} 0 ile 100 arasında olmalıdır."
                    )

                setattr(
                    self,
                    name,
                    normalized,
                )


@dataclass(slots=True, frozen=True)
class PlantMatch:
    """Tek bitki türü eşleşme sonucu."""

    species: PlantSpeciesProfile
    score: float
    matched: bool
    reasons: tuple[str, ...]
    warnings: tuple[str, ...]
    icon_code: str
    dynamic_state: str
    ecosystem_clues: tuple[str, ...]

    def to_runtime_dict(self) -> dict[str, Any]:
        return {
            "tür_kimliği": self.species.species_id,
            "türkçe_ad": self.species.turkish_name,
            "bilimsel_ad": self.species.scientific_name,
            "varlık_türü": self.species.entity_type.value,
            "eşleşme_skoru": self.score,
            "eşleşti": self.matched,
            "gerekçeler": list(self.reasons),
            "uyarılar": list(self.warnings),
            "ekosistem_ipuçları": list(
                self.ecosystem_clues
            ),
            "ikon": self.icon_code,
            "dinamik_durum": self.dynamic_state,
            "koruma_durumu": (
                self.species.conservation_state.value
            ),
            "kaynak_doğrulama_bekliyor": (
                self.species.source_pending
            ),
        }


@dataclass(slots=True, frozen=True)
class PlantLayerResult:
    """Dinamik bitki katmanı sonucu."""

    context: EcosystemRuntimeContext
    matches: tuple[PlantMatch, ...]
    water_indicator_score: float
    disturbance_indicator_score: float
    health_summary: dict[str, int]
    selected_species_ids: tuple[str, ...]
    layer_code: str = "ecosystem.plant"
    dynamic: bool = True

    def to_runtime_dict(self) -> dict[str, Any]:
        return json_safe(
            {
                "katman": self.layer_code,
                "dinamik": self.dynamic,
                "bağlam": self.context.to_dict(),
                "su_göstergesi": (
                    self.water_indicator_score
                ),
                "insan_müdahalesi_göstergesi": (
                    self.disturbance_indicator_score
                ),
                "sağlık_özeti": self.health_summary,
                "seçilen_türler": list(
                    self.selected_species_ids
                ),
                "eşleşmeler": [
                    match.to_runtime_dict()
                    for match in self.matches
                ],
            }
        )


class DynamicPlantLayerEngine:
    """Kamera, konum ve habitat verisine göre bitki türlerini sıralar."""

    def evaluate(
        self,
        *,
        context: EcosystemRuntimeContext,
        species_profiles: tuple[
            PlantSpeciesProfile,
            ...,
        ],
        observations: tuple[
            PlantObservation,
            ...,
        ] = tuple(),
        minimum_match_score: float = 45.0,
        limit: int = 12,
    ) -> PlantLayerResult:
        matches = [
            self._score_species(
                context=context,
                species=species,
                observations=observations,
                minimum_match_score=(
                    minimum_match_score
                ),
            )
            for species in species_profiles
        ]

        matches.sort(
            key=lambda item: (
                -item.score,
                item.species.turkish_name,
            )
        )

        selected = tuple(
            match
            for match in matches
            if match.matched
        )[:limit]

        water_indicator_score = self._weighted_indicator(
            selected,
            attribute="water_indicator_score",
        )

        disturbance_indicator_score = (
            self._weighted_indicator(
                selected,
                attribute=(
                    "disturbance_indicator_score"
                ),
            )
        )

        health_summary: dict[str, int] = {}

        for observation in observations:
            key = observation.condition.value
            health_summary[key] = (
                health_summary.get(key, 0) + 1
            )

        return PlantLayerResult(
            context=context,
            matches=selected,
            water_indicator_score=(
                water_indicator_score
            ),
            disturbance_indicator_score=(
                disturbance_indicator_score
            ),
            health_summary=health_summary,
            selected_species_ids=tuple(
                match.species.species_id
                for match in selected
            ),
        )

    def _score_species(
        self,
        *,
        context: EcosystemRuntimeContext,
        species: PlantSpeciesProfile,
        observations: tuple[
            PlantObservation,
            ...,
        ],
        minimum_match_score: float,
    ) -> PlantMatch:
        score = 20.0
        reasons: list[str] = []
        warnings: list[str] = []
        clues: list[str] = []

        normalized_region = (
            context.region_code.casefold()
        )

        supported_regions = {
            item.casefold()
            for item in species.supported_region_codes
        }

        if normalized_region in supported_regions:
            score += 16.0
            reasons.append(
                "Bölgesel dağılım kaydıyla eşleşti."
            )

        score += self._range_score(
            value=context.altitude_m,
            minimum=species.minimum_altitude_m,
            maximum=species.maximum_altitude_m,
            reasons=reasons,
            warnings=warnings,
            success="Rakım aralığı uyumlu.",
            failure="Rakım aralığı uyumsuz.",
            weight=8.0,
        )

        score += self._range_score(
            value=context.soil_moisture_percent,
            minimum=(
                species
                .minimum_soil_moisture_percent
            ),
            maximum=(
                species
                .maximum_soil_moisture_percent
            ),
            reasons=reasons,
            warnings=warnings,
            success="Toprak nemi uyumlu.",
            failure="Toprak nemi uyumsuz.",
            weight=8.0,
        )

        score += self._range_score(
            value=context.air_temperature_c,
            minimum=(
                species
                .minimum_air_temperature_c
            ),
            maximum=(
                species
                .maximum_air_temperature_c
            ),
            reasons=reasons,
            warnings=warnings,
            success="Hava sıcaklığı uyumlu.",
            failure="Hava sıcaklığı uyumsuz.",
            weight=6.0,
        )

        if context.month in species.active_months:
            score += 5.0
            reasons.append(
                "Mevsimsel görünürlük uyumlu."
            )
        else:
            score -= 4.0
            warnings.append(
                "Mevsimsel görünürlük aralığı dışında."
            )

        normalized_name = (
            species.turkish_name.casefold()
        )

        for observation in observations:
            detected_label = (
                observation.detected_label or ""
            ).casefold()

            if (
                detected_label
                and detected_label == normalized_name
            ):
                confidence = (
                    observation.model_confidence
                    or 0.0
                )

                score += min(
                    25.0,
                    confidence * 0.25,
                )
                reasons.append(
                    "Kamera tür tahminiyle eşleşti."
                )

            if (
                observation.green_coverage_percent
                is not None
                and observation.green_coverage_percent
                >= 50
            ):
                score += 2.0
                reasons.append(
                    "Yeşil doku oranı yeterli."
                )

        if species.water_indicator_score >= 70:
            clues.append(
                "Yakın veya geçmiş su varlığı açısından incelenmeli."
            )

        if species.disturbance_indicator_score >= 70:
            clues.append(
                "İnsan müdahalesi veya bozulmuş habitat açısından incelenmeli."
            )

        if (
            species.conservation_state
            in {
                ConservationState.RARE,
                ConservationState.PROTECTED,
            }
        ):
            clues.append(
                "Koruma durumu nedeniyle hassas kayıt oluşturulmalı."
            )

        score = round(
            min(100.0, max(0.0, score)),
            3,
        )

        matched = score >= minimum_match_score

        if score >= 80:
            dynamic_state = "yüksek_olasılık"
        elif score >= 60:
            dynamic_state = "olası"
        elif matched:
            dynamic_state = "incelenmeli"
        else:
            dynamic_state = "gizli"

        if species.source_pending:
            warnings.append(
                "Bitki profili kaynak doğrulaması bekliyor."
            )

        return PlantMatch(
            species=species,
            score=score,
            matched=matched,
            reasons=tuple(reasons),
            warnings=tuple(warnings),
            icon_code=species.resolved_icon_code,
            dynamic_state=dynamic_state,
            ecosystem_clues=tuple(clues),
        )

    @staticmethod
    def _range_score(
        *,
        value: float | None,
        minimum: float | None,
        maximum: float | None,
        reasons: list[str],
        warnings: list[str],
        success: str,
        failure: str,
        weight: float,
    ) -> float:
        if value is None:
            return 0.0

        if (
            minimum is not None
            and value < minimum
        ) or (
            maximum is not None
            and value > maximum
        ):
            warnings.append(failure)
            return -weight

        reasons.append(success)
        return weight

    @staticmethod
    def _weighted_indicator(
        matches: tuple[PlantMatch, ...],
        *,
        attribute: str,
    ) -> float:
        if not matches:
            return 0.0

        weighted_sum = 0.0
        total_weight = 0.0

        for match in matches:
            indicator = float(
                getattr(
                    match.species,
                    attribute,
                )
            )
            weight = max(
                1.0,
                match.score,
            )

            weighted_sum += indicator * weight
            total_weight += weight

        return round(
            weighted_sum / total_weight,
            3,
        )
