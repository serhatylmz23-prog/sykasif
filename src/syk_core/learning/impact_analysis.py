"""Öğrenme adayının etki analizi."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .enums import ImpactLevel, UpdateType
from .learning_candidate import LearningCandidate


@dataclass(slots=True, frozen=True)
class ImpactedComponent:
    """Güncellemeden etkilenen tek sistem bileşeni."""

    component_type: str
    component_id: str
    impact_level: ImpactLevel
    reason: str
    automatic_update_allowed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "bileşen_türü": self.component_type,
            "bileşen_kimliği": self.component_id,
            "etki_düzeyi": self.impact_level.value,
            "gerekçe": self.reason,
            "otomatik_güncelleme_izni": (
                self.automatic_update_allowed
            ),
        }


@dataclass(slots=True, frozen=True)
class ImpactAssessment:
    """Öğrenme adayının birleşik etki sonucu."""

    candidate_id: str
    overall_level: ImpactLevel
    components: tuple[ImpactedComponent, ...]
    requires_regression_test: bool
    requires_manifest_update: bool
    requires_report_regeneration: bool
    requires_human_approval: bool
    warnings: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "öğrenme_adayı": self.candidate_id,
            "genel_etki": self.overall_level.value,
            "bileşenler": [
                component.to_dict()
                for component in self.components
            ],
            "regresyon_testi_gerekli": (
                self.requires_regression_test
            ),
            "manifest_güncellemesi_gerekli": (
                self.requires_manifest_update
            ),
            "rapor_yenileme_gerekli": (
                self.requires_report_regeneration
            ),
            "insan_onayı_gerekli": (
                self.requires_human_approval
            ),
            "uyarılar": list(self.warnings),
        }


class ImpactAnalysisEngine:
    """Öğrenme adayının etkileyeceği alanları belirler."""

    _UPDATE_IMPACT: dict[UpdateType, ImpactLevel] = {
        UpdateType.NEW_INFORMATION: ImpactLevel.LOW,
        UpdateType.SOURCE_UPDATE: ImpactLevel.LOW,
        UpdateType.SEASONAL_UPDATE: ImpactLevel.MEDIUM,
        UpdateType.REGIONAL_UPDATE: ImpactLevel.MEDIUM,
        UpdateType.LAYER_UPDATE: ImpactLevel.HIGH,
        UpdateType.TAXONOMY_UPDATE: ImpactLevel.HIGH,
        UpdateType.CORRECTION: ImpactLevel.HIGH,
        UpdateType.CONTRADICTION: ImpactLevel.HIGH,
        UpdateType.MODEL_RULE_UPDATE: ImpactLevel.CRITICAL,
        UpdateType.SAFETY_UPDATE: ImpactLevel.CRITICAL,
    }

    def analyze(
        self,
        candidate: LearningCandidate,
    ) -> ImpactAssessment:
        components: list[ImpactedComponent] = []
        warnings: list[str] = []

        base_level = self._UPDATE_IMPACT[
            candidate.update_type
        ]

        for entity_id in sorted(
            candidate.affected_entity_ids
        ):
            components.append(
                ImpactedComponent(
                    component_type="entity",
                    component_id=entity_id,
                    impact_level=base_level,
                    reason=(
                        "Öğrenme adayı varlığın kayıtlı "
                        "bilgisini değiştirebilir."
                    ),
                )
            )

        for layer_code in sorted(
            candidate.affected_layer_codes
        ):
            layer_level = max(
                base_level,
                ImpactLevel.MEDIUM,
                key=self._impact_rank,
            )

            components.append(
                ImpactedComponent(
                    component_type="layer",
                    component_id=layer_code,
                    impact_level=layer_level,
                    reason=(
                        "Katman görünümü, filtreleri veya "
                        "veri seçimi etkilenebilir."
                    ),
                )
            )

        for key in sorted(
            candidate.proposed_changes
        ):
            components.append(
                ImpactedComponent(
                    component_type="model_field",
                    component_id=key,
                    impact_level=base_level,
                    reason=(
                        "Kalıcı model alanı için yeni değer önerildi."
                    ),
                )
            )

        if candidate.contradiction_count:
            warnings.append(
                "Çelişkili kaynak veya iddia bulundu."
            )

        if candidate.confidence_score < 70:
            warnings.append(
                "Öğrenme adayı güven skoru yüksek değil."
            )

        if not components:
            components.append(
                ImpactedComponent(
                    component_type="candidate",
                    component_id=candidate.candidate_id,
                    impact_level=ImpactLevel.LOW,
                    reason=(
                        "Henüz doğrudan etkilenen bileşen tanımlanmadı."
                    ),
                )
            )

        overall_level = max(
            (
                component.impact_level
                for component in components
            ),
            key=self._impact_rank,
        )

        requires_regression_test = (
            self._impact_rank(overall_level)
            >= self._impact_rank(ImpactLevel.HIGH)
        )

        requires_report_regeneration = bool(
            candidate.affected_entity_ids
            or candidate.affected_layer_codes
        )

        return ImpactAssessment(
            candidate_id=candidate.candidate_id,
            overall_level=overall_level,
            components=tuple(components),
            requires_regression_test=requires_regression_test,
            requires_manifest_update=True,
            requires_report_regeneration=(
                requires_report_regeneration
            ),
            requires_human_approval=True,
            warnings=tuple(warnings),
        )

    @staticmethod
    def _impact_rank(
        level: ImpactLevel,
    ) -> int:
        ranks = {
            ImpactLevel.NONE: 0,
            ImpactLevel.LOW: 1,
            ImpactLevel.MEDIUM: 2,
            ImpactLevel.HIGH: 3,
            ImpactLevel.CRITICAL: 4,
        }

        return ranks[level]
