"""Dinamik balık türü ve sonar modelleri."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

from ..utils import json_safe, utc_now
from .enums import (
    ConservationState,
    ObservationSource,
    SalinityType,
    SonarTargetState,
    WaterBodyType,
)
from .runtime_context import EcosystemRuntimeContext


@dataclass(slots=True, frozen=True)
class FishSpeciesProfile:
    """Balık türü çalışma profili."""

    species_id: str
    turkish_name: str
    scientific_name: str | None = None

    supported_region_codes: frozenset[str] = frozenset()
    supported_water_body_names: frozenset[str] = frozenset()
    salinity_types: frozenset[SalinityType] = frozenset(
        {
            SalinityType.FRESHWATER,
        }
    )
    water_body_types: frozenset[WaterBodyType] = frozenset()

    minimum_depth_m: float | None = None
    maximum_depth_m: float | None = None
    minimum_temperature_c: float | None = None
    maximum_temperature_c: float | None = None
    minimum_oxygen_mg_l: float | None = None
    maximum_oxygen_mg_l: float | None = None

    active_months: frozenset[int] = frozenset(
        range(1, 13)
    )
    conservation_state: ConservationState = (
        ConservationState.UNKNOWN
    )
    icon_code: str | None = None
    source_pending: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.species_id.strip():
            raise ValueError(
                "Balık türü kimliği boş olamaz."
            )

        if not self.turkish_name.strip():
            raise ValueError(
                "Balık türü adı boş olamaz."
            )

        if not self.active_months:
            raise ValueError(
                "Balık türü için en az bir etkin ay bulunmalıdır."
            )

        if any(
            month < 1 or month > 12
            for month in self.active_months
        ):
            raise ValueError(
                "Etkin ay değerleri 1 ile 12 arasında olmalıdır."
            )

        self._validate_range(
            self.minimum_depth_m,
            self.maximum_depth_m,
            "derinlik",
        )
        self._validate_range(
            self.minimum_temperature_c,
            self.maximum_temperature_c,
            "sıcaklık",
        )
        self._validate_range(
            self.minimum_oxygen_mg_l,
            self.maximum_oxygen_mg_l,
            "oksijen",
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
                "syk-fish-"
                + self.species_id.casefold().replace(
                    "_",
                    "-",
                )
            )
        )


@dataclass(slots=True, frozen=True)
class SonarTarget:
    """Sonar ekranındaki dinamik hedef."""

    target_id: str
    depth_m: float
    relative_x: float
    strength_percent: float
    estimated_length_cm: float | None = None
    estimated_speed_m_s: float | None = None
    state: SonarTargetState = SonarTargetState.NEW
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.target_id.strip():
            raise ValueError(
                "Sonar hedef kimliği boş olamaz."
            )

        if self.depth_m < 0:
            raise ValueError(
                "Sonar hedef derinliği negatif olamaz."
            )

        if not 0.0 <= self.relative_x <= 1.0:
            raise ValueError(
                "Sonar yatay konumu 0.0 ile 1.0 arasında olmalıdır."
            )

        if not 0.0 <= self.strength_percent <= 100.0:
            raise ValueError(
                "Sonar sinyal gücü 0 ile 100 arasında olmalıdır."
            )


@dataclass(slots=True)
class FishObservation:
    """Kamera, fotoğraf veya sonar balık gözlemi."""

    source: ObservationSource
    observation_id: str = field(
        default_factory=lambda: (
            f"SYK-FISH-OBS-{uuid4().hex[:16].upper()}"
        )
    )
    detected_label: str | None = None
    model_confidence: float | None = None
    sonar_target: SonarTarget | None = None
    visual_feature_scores: dict[str, float] = field(
        default_factory=dict
    )
    evidence_ids: set[str] = field(default_factory=set)
    observed_at: Any = field(default_factory=utc_now)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.model_confidence is not None:
            self.model_confidence = float(
                self.model_confidence
            )

            if not 0.0 <= self.model_confidence <= 100.0:
                raise ValueError(
                    "Model güveni 0 ile 100 arasında olmalıdır."
                )

        for key, value in self.visual_feature_scores.items():
            if not 0.0 <= float(value) <= 100.0:
                raise ValueError(
                    f"Görsel özellik skoru geçersiz: {key}"
                )


@dataclass(slots=True, frozen=True)
class FishMatch:
    """Tek balık türü eşleşme sonucu."""

    species: FishSpeciesProfile
    score: float
    matched: bool
    reasons: tuple[str, ...]
    warnings: tuple[str, ...]
    icon_code: str
    dynamic_state: str

    def to_runtime_dict(self) -> dict[str, Any]:
        return {
            "tür_kimliği": self.species.species_id,
            "türkçe_ad": self.species.turkish_name,
            "bilimsel_ad": self.species.scientific_name,
            "eşleşme_skoru": self.score,
            "eşleşti": self.matched,
            "gerekçeler": list(self.reasons),
            "uyarılar": list(self.warnings),
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
class FishLayerResult:
    """Dinamik balık katmanı sonucu."""

    context: EcosystemRuntimeContext
    matches: tuple[FishMatch, ...]
    sonar_target_count: int
    selected_species_ids: tuple[str, ...]
    layer_code: str = "ecosystem.fish"
    dynamic: bool = True

    def to_runtime_dict(self) -> dict[str, Any]:
        return json_safe(
            {
                "katman": self.layer_code,
                "dinamik": self.dynamic,
                "bağlam": self.context.to_dict(),
                "sonar_hedef_sayısı": (
                    self.sonar_target_count
                ),
                "seçilen_türler": list(
                    self.selected_species_ids
                ),
                "eşleşmeler": [
                    match.to_runtime_dict()
                    for match in self.matches
                ],
            }
        )


class DynamicFishLayerEngine:
    """Konum, su ve gözlem verisine göre balık türlerini sıralar."""

    def evaluate(
        self,
        *,
        context: EcosystemRuntimeContext,
        species_profiles: tuple[
            FishSpeciesProfile,
            ...,
        ],
        observations: tuple[
            FishObservation,
            ...,
        ] = tuple(),
        minimum_match_score: float = 45.0,
        limit: int = 12,
    ) -> FishLayerResult:
        if limit < 1:
            raise ValueError(
                "Balık eşleşme limiti en az 1 olmalıdır."
            )

        sonar_target_count = sum(
            1
            for observation in observations
            if observation.sonar_target is not None
        )

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

        return FishLayerResult(
            context=context,
            matches=selected,
            sonar_target_count=sonar_target_count,
            selected_species_ids=tuple(
                match.species.species_id
                for match in selected
            ),
        )

    def _score_species(
        self,
        *,
        context: EcosystemRuntimeContext,
        species: FishSpeciesProfile,
        observations: tuple[
            FishObservation,
            ...,
        ],
        minimum_match_score: float,
    ) -> FishMatch:
        score = 20.0
        reasons: list[str] = []
        warnings: list[str] = []

        if context.salinity in species.salinity_types:
            score += 14.0
            reasons.append(
                "Su tuzluluk türü uyumlu."
            )
        elif (
            context.salinity
            != SalinityType.UNKNOWN
        ):
            score -= 30.0
            warnings.append(
                "Su tuzluluk türü uyumsuz."
            )

        if (
            not species.water_body_types
            or context.water_body_type
            in species.water_body_types
        ):
            score += 8.0
            reasons.append(
                "Su kütlesi türü uyumlu."
            )
        elif (
            context.water_body_type
            != WaterBodyType.UNKNOWN
        ):
            score -= 15.0
            warnings.append(
                "Su kütlesi türü uyumsuz."
            )

        normalized_region = (
            context.region_code.casefold()
        )

        supported_regions = {
            item.casefold()
            for item in species.supported_region_codes
        }

        if normalized_region in supported_regions:
            score += 14.0
            reasons.append(
                "Bölgesel kayıtla eşleşti."
            )

        water_name = (
            context.water_body_name or ""
        ).casefold()

        supported_water_names = {
            item.casefold()
            for item
            in species.supported_water_body_names
        }

        if (
            water_name
            and water_name in supported_water_names
        ):
            score += 18.0
            reasons.append(
                "Su kütlesi kaydıyla doğrudan eşleşti."
            )

        score += self._range_score(
            value=context.depth_m,
            minimum=species.minimum_depth_m,
            maximum=species.maximum_depth_m,
            success_reason="Derinlik aralığı uyumlu.",
            failure_warning="Derinlik aralığı uyumsuz.",
            reasons=reasons,
            warnings=warnings,
            weight=8.0,
        )

        score += self._range_score(
            value=context.water_temperature_c,
            minimum=species.minimum_temperature_c,
            maximum=species.maximum_temperature_c,
            success_reason="Su sıcaklığı uyumlu.",
            failure_warning="Su sıcaklığı uyumsuz.",
            reasons=reasons,
            warnings=warnings,
            weight=8.0,
        )

        score += self._range_score(
            value=context.dissolved_oxygen_mg_l,
            minimum=species.minimum_oxygen_mg_l,
            maximum=species.maximum_oxygen_mg_l,
            success_reason="Çözünmüş oksijen uyumlu.",
            failure_warning="Çözünmüş oksijen uyumsuz.",
            reasons=reasons,
            warnings=warnings,
            weight=6.0,
        )

        if context.month in species.active_months:
            score += 4.0
            reasons.append(
                "Mevsimsel etkinlik aralığı uyumlu."
            )
        else:
            score -= 4.0
            warnings.append(
                "Mevsimsel etkinlik aralığı dışında."
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
                    15.0,
                    confidence * 0.15,
                )
                reasons.append(
                    "Görsel tür tahminiyle eşleşti."
                )

            if observation.sonar_target is not None:
                target = observation.sonar_target

                if (
                    species.minimum_depth_m is None
                    or target.depth_m
                    >= species.minimum_depth_m
                ) and (
                    species.maximum_depth_m is None
                    or target.depth_m
                    <= species.maximum_depth_m
                ):
                    score += 3.0
                    reasons.append(
                        "Sonar hedef derinliğiyle uyumlu."
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
                "Tür profili kaynak doğrulaması bekliyor."
            )

        return FishMatch(
            species=species,
            score=score,
            matched=matched,
            reasons=tuple(reasons),
            warnings=tuple(warnings),
            icon_code=species.resolved_icon_code,
            dynamic_state=dynamic_state,
        )

    @staticmethod
    def _range_score(
        *,
        value: float | None,
        minimum: float | None,
        maximum: float | None,
        success_reason: str,
        failure_warning: str,
        reasons: list[str],
        warnings: list[str],
        weight: float,
    ) -> float:
        if value is None:
            return 0.0

        below = (
            minimum is not None
            and value < minimum
        )
        above = (
            maximum is not None
            and value > maximum
        )

        if below or above:
            warnings.append(failure_warning)
            return -weight

        reasons.append(success_reason)
        return weight


def create_keban_seed_profiles(
) -> tuple[FishSpeciesProfile, ...]:
    """Kullanıcı onaylı görsel listeden kaynak bekleyen başlangıç profilleri."""

    common = {
        "supported_region_codes": frozenset(
            {
                "TR-ELAZIG-KEBAN",
            }
        ),
        "supported_water_body_names": frozenset(
            {
                "keban baraj gölü",
            }
        ),
        "salinity_types": frozenset(
            {
                SalinityType.FRESHWATER,
            }
        ),
        "water_body_types": frozenset(
            {
                WaterBodyType.RESERVOIR,
                WaterBodyType.LAKE,
                WaterBodyType.RIVER,
            }
        ),
        "source_pending": True,
        "metadata": {
            "seed_source": (
                "Kullanıcı tarafından sağlanan "
                "dinamik balık ikon listesi"
            ),
        },
    }

    return (
        FishSpeciesProfile(
            species_id="sazan",
            turkish_name="Sazan",
            minimum_depth_m=0.5,
            maximum_depth_m=30.0,
            minimum_temperature_c=4.0,
            maximum_temperature_c=30.0,
            **common,
        ),
        FishSpeciesProfile(
            species_id="yayin",
            turkish_name="Yayın",
            minimum_depth_m=1.0,
            maximum_depth_m=45.0,
            minimum_temperature_c=6.0,
            maximum_temperature_c=29.0,
            **common,
        ),
        FishSpeciesProfile(
            species_id="kerevit",
            turkish_name="Kerevit",
            minimum_depth_m=0.2,
            maximum_depth_m=15.0,
            **common,
        ),
        FishSpeciesProfile(
            species_id="tatli_su_levregi",
            turkish_name="Tatlı Su Levreği",
            minimum_depth_m=0.5,
            maximum_depth_m=25.0,
            **common,
        ),
        FishSpeciesProfile(
            species_id="siraz",
            turkish_name="Siraz",
            minimum_depth_m=0.2,
            maximum_depth_m=20.0,
            **common,
        ),
        FishSpeciesProfile(
            species_id="yilan_baligi",
            turkish_name="Yılan Balığı",
            minimum_depth_m=0.2,
            maximum_depth_m=35.0,
            conservation_state=(
                ConservationState.REVIEW_REQUIRED
            ),
            **common,
        ),
        FishSpeciesProfile(
            species_id="gumus_baligi",
            turkish_name="Gümüş Balığı",
            minimum_depth_m=0.1,
            maximum_depth_m=18.0,
            **common,
        ),
    )
