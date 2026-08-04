"""Dinamik katman davranış motoru."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..enums import ResearchCategory
from .entity import OvmEntity
from .enums import (
    EntityKind,
    RuntimeState,
    VisualStatus,
)


@dataclass(slots=True, frozen=True)
class DynamicLayerContext:
    """Katmanların dinamik davranışını belirleyen çalışma bağlamı."""

    research_category: ResearchCategory
    gps_available: bool
    rtk_available: bool
    online_available: bool
    device_data_available: bool
    selected_layer_codes: frozenset[str] = frozenset()
    zoom_level: float = 14.0
    map_mode: str = "two_dimensional"
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.zoom_level < 0:
            raise ValueError(
                "Yakınlaştırma seviyesi negatif olamaz."
            )


@dataclass(slots=True, frozen=True)
class DynamicLayerResult:
    """Dinamik değerlendirme sonucu."""

    visible: bool
    opacity: float
    layer_order: int
    runtime_state: RuntimeState
    visual_status: VisualStatus
    icon_code: str
    reasons: tuple[str, ...]


class DynamicLayerEngine:
    """OVM varlıklarını konum ve çalışma bağlamına göre düzenler."""

    _LAYER_ORDER: dict[EntityKind, int] = {
        EntityKind.LOCATION: 10,
        EntityKind.MAP_PIN: 20,
        EntityKind.RESEARCH_AREA: 30,

        EntityKind.GEOLOGY: 100,
        EntityKind.HYDROGEOLOGY: 110,
        EntityKind.BOTANICAL: 120,
        EntityKind.SOIL: 130,
        EntityKind.WATER: 140,

        EntityKind.SURFACE_MODEL: 200,
        EntityKind.POINT_CLOUD: 210,
        EntityKind.ADAPTIVE_MESH: 220,
        EntityKind.THREE_D_MODEL: 230,

        EntityKind.CAVITY: 300,
        EntityKind.CHANNEL: 310,
        EntityKind.CRACK: 320,
        EntityKind.MINERAL_VEIN: 330,
        EntityKind.SURFACE_EROSION: 340,
        EntityKind.ROUGHNESS: 350,
        EntityKind.SLOPE: 360,

        EntityKind.SONAR: 400,
        EntityKind.FISH_SPECIES: 410,
        EntityKind.FISH_OBSERVATION: 420,

        EntityKind.THERMAL: 500,
        EntityKind.SPECTRAL: 510,
        EntityKind.MAGNETIC: 520,
        EntityKind.GRAVITY: 530,
        EntityKind.ERT: 540,
        EntityKind.GPR: 550,
        EntityKind.SEISMIC: 560,
        EntityKind.LIDAR: 570,

        EntityKind.HISTORICAL_SITE: 600,
        EntityKind.ARCHAEOLOGICAL_SITE: 610,
        EntityKind.STRUCTURE: 620,
        EntityKind.ARTIFACT: 630,
        EntityKind.INSCRIPTION: 640,
        EntityKind.STATUE: 650,

        EntityKind.PHOTO: 700,
        EntityKind.VIDEO: 710,
        EntityKind.ANNOTATION: 800,
        EntityKind.FRAME: 810,
        EntityKind.MARKER: 820,

        EntityKind.EVIDENCE: 900,
        EntityKind.EXPERT_OPINION: 910,
        EntityKind.AI_ANALYSIS: 920,
        EntityKind.DECISION: 930,
        EntityKind.REPORT: 940,
    }

    _ICON_CODES: dict[EntityKind, str] = {
        kind: f"syk-{kind.value.replace('_', '-')}"
        for kind in EntityKind
    }

    def evaluate(
        self,
        entity: OvmEntity,
        context: DynamicLayerContext,
    ) -> DynamicLayerResult:
        reasons: list[str] = []

        visible = entity.visible
        opacity = entity.opacity
        runtime_state = entity.runtime_state
        visual_status = entity.visual_status

        if entity.kind == EntityKind.GPS:
            visible = context.gps_available
            reasons.append(
                "GPS kullanılabilirliğine göre değerlendirildi."
            )

        if entity.kind == EntityKind.RTK:
            visible = context.rtk_available
            reasons.append(
                "RTK düzeltme durumuna göre değerlendirildi."
            )

        if entity.kind in {
            EntityKind.SATELLITE
            if hasattr(EntityKind, "SATELLITE")
            else EntityKind.LOCATION
        }:
            reasons.append(
                "Çevrimiçi veri durumuna göre değerlendirildi."
            )

        if entity.kind in {
            EntityKind.POINT_CLOUD,
            EntityKind.ADAPTIVE_MESH,
            EntityKind.SURFACE_MODEL,
            EntityKind.THREE_D_MODEL,
            EntityKind.LIDAR,
            EntityKind.SONAR,
            EntityKind.THERMAL,
            EntityKind.SPECTRAL,
            EntityKind.MAGNETIC,
            EntityKind.GRAVITY,
            EntityKind.ERT,
            EntityKind.GPR,
            EntityKind.SEISMIC,
        }:
            if not context.device_data_available:
                visible = False
                runtime_state = RuntimeState.WAITING
                reasons.append(
                    "Cihaz verisi bulunmadığı için beklemeye alındı."
                )
            else:
                reasons.append(
                    "Cihaz verisi kullanılabilir."
                )

        if entity.layer_code:
            if (
                context.selected_layer_codes
                and entity.layer_code
                not in context.selected_layer_codes
            ):
                visible = False
                reasons.append(
                    "Katman kullanıcı seçimi dışında bırakıldı."
                )

        if entity.confidence_score is not None:
            if entity.confidence_score < 40:
                visual_status = VisualStatus.LOW_CONFIDENCE
                opacity = min(opacity, 0.72)
                reasons.append(
                    "Düşük güven skoru görsel stile uygulandı."
                )
            elif entity.confidence_score >= 99.9:
                visual_status = VisualStatus.VERIFIED
                reasons.append(
                    "Dijital doğrulama eşiği karşılandı."
                )

        if runtime_state == RuntimeState.ERROR:
            visual_status = VisualStatus.CRITICAL
            reasons.append(
                "Çalışma hatası kritik durum olarak gösterildi."
            )

        return DynamicLayerResult(
            visible=visible,
            opacity=opacity,
            layer_order=self._LAYER_ORDER.get(
                entity.kind,
                500,
            ),
            runtime_state=runtime_state,
            visual_status=visual_status,
            icon_code=(
                entity.icon_code
                or self._ICON_CODES[entity.kind]
            ),
            reasons=tuple(reasons),
        )

    def apply(
        self,
        entity: OvmEntity,
        context: DynamicLayerContext,
    ) -> DynamicLayerResult:
        result = self.evaluate(
            entity,
            context,
        )

        entity.visible = result.visible
        entity.opacity = result.opacity
        entity.layer_order = result.layer_order
        entity.runtime_state = result.runtime_state
        entity.visual_status = result.visual_status
        entity.icon_code = result.icon_code

        entity.metadata["dynamic_layer_reasons"] = list(
            result.reasons
        )
        entity.identity.touch()

        return result
