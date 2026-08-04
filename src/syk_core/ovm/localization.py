"""Türkçe arayüz etiketleri."""

from __future__ import annotations

from collections.abc import Mapping
from enum import Enum
from typing import Any

from .enums import (
    ConfidenceLevel,
    EntityKind,
    RuntimeState,
    VisualStatus,
)


_ENTITY_LABELS: dict[EntityKind, str] = {
    EntityKind.LOCATION: "Konum",
    EntityKind.MAP_PIN: "Harita Pini",
    EntityKind.RESEARCH_AREA: "Araştırma Alanı",

    EntityKind.PHOTO: "Fotoğraf",
    EntityKind.VIDEO: "Video",
    EntityKind.VIDEO_FRAME: "Video Karesi",
    EntityKind.AUDIO: "Ses Kaydı",
    EntityKind.DOCUMENT: "Belge",

    EntityKind.ANNOTATION: "Açıklama",
    EntityKind.FRAME: "Çerçeve",
    EntityKind.MARKER: "İşaret",
    EntityKind.MEASUREMENT: "Ölçüm",

    EntityKind.SURFACE_MODEL: "Yüzey Modeli",
    EntityKind.POINT_CLOUD: "Nokta Bulutu",
    EntityKind.ADAPTIVE_MESH: "Adaptif Ağ",
    EntityKind.THREE_D_MODEL: "3B Model",

    EntityKind.CAVITY: "Oyuk",
    EntityKind.CHANNEL: "Kanal",
    EntityKind.CRACK: "Çatlak",
    EntityKind.MINERAL_VEIN: "Mineral Damarı",
    EntityKind.SURFACE_EROSION: "Yüzey Aşınımı",
    EntityKind.ROUGHNESS: "Pürüzlülük",
    EntityKind.SLOPE: "Eğim",

    EntityKind.GEOLOGY: "Jeoloji",
    EntityKind.HYDROGEOLOGY: "Hidrojeoloji",
    EntityKind.BOTANICAL: "Botanik",
    EntityKind.SOIL: "Toprak",
    EntityKind.WATER: "Su",
    EntityKind.CHEMICAL: "Kimyasal Analiz",
    EntityKind.MATERIAL: "Materyal",
    EntityKind.MINERAL: "Mineral",

    EntityKind.SONAR: "Sonar",
    EntityKind.FISH: "Balık",
    EntityKind.FISH_SPECIES: "Balık Türü",
    EntityKind.FISH_OBSERVATION: "Balık Gözlemi",

    EntityKind.THERMAL: "Termal Analiz",
    EntityKind.SPECTRAL: "Spektral Analiz",
    EntityKind.MAGNETIC: "Manyetik Analiz",
    EntityKind.GRAVITY: "Gravite Analizi",
    EntityKind.ERT: "Elektrik Direnç",
    EntityKind.GPR: "GPR",
    EntityKind.SEISMIC: "Sismik Analiz",
    EntityKind.LIDAR: "Lidar",
    EntityKind.GPS: "GPS",
    EntityKind.RTK: "RTK",

    EntityKind.HISTORICAL_SITE: "Tarihî Alan",
    EntityKind.ARCHAEOLOGICAL_SITE: "Arkeolojik Alan",
    EntityKind.STRUCTURE: "Yapı",
    EntityKind.ARTIFACT: "Buluntu",
    EntityKind.INSCRIPTION: "Yazıt",
    EntityKind.STATUE: "Heykel",
    EntityKind.TIMELINE: "Zaman Çizelgesi",

    EntityKind.EVIDENCE: "Kanıt",
    EntityKind.EXPERT_OPINION: "Uzman Görüşü",
    EntityKind.AI_ANALYSIS: "Yapay Zekâ Analizi",
    EntityKind.DECISION: "Karar",
    EntityKind.REPORT: "Rapor",
    EntityKind.MANIFEST: "Manifest",
    EntityKind.DIGITAL_SIGNATURE: "Dijital İmza",
}


_RUNTIME_LABELS: dict[RuntimeState, str] = {
    RuntimeState.NEW: "Yeni",
    RuntimeState.WAITING: "Bekliyor",
    RuntimeState.LOADING: "Yükleniyor",
    RuntimeState.ACTIVE: "Aktif",
    RuntimeState.ANALYZING: "Analiz Ediliyor",
    RuntimeState.VERIFYING: "Doğrulanıyor",
    RuntimeState.COMPLETED: "Tamamlandı",
    RuntimeState.PAUSED: "Duraklatıldı",
    RuntimeState.STOPPED: "Durduruldu",
    RuntimeState.OFFLINE: "Çevrimdışı",
    RuntimeState.ERROR: "Hata",
    RuntimeState.ARCHIVED: "Arşivlendi",
}


_VISUAL_STATUS_LABELS: dict[VisualStatus, str] = {
    VisualStatus.NEUTRAL: "Nötr",
    VisualStatus.VERIFIED: "Doğrulandı",
    VisualStatus.ANALYZING: "Analiz Ediliyor",
    VisualStatus.REVIEW_REQUIRED: "İncelenmeli",
    VisualStatus.LOW_CONFIDENCE: "Düşük Güven",
    VisualStatus.INCONSISTENT: "Tutarsız Veri",
    VisualStatus.RARE_ANOMALY: "Nadir Anomali",
    VisualStatus.REFERENCE: "Referans Veri",
    VisualStatus.CRITICAL: "Kritik",
}


_CONFIDENCE_LABELS: dict[ConfidenceLevel, str] = {
    ConfidenceLevel.UNKNOWN: "Bilinmiyor",
    ConfidenceLevel.VERY_LOW: "Çok Düşük",
    ConfidenceLevel.LOW: "Düşük",
    ConfidenceLevel.MEDIUM: "Orta",
    ConfidenceLevel.HIGH: "Yüksek",
    ConfidenceLevel.VERY_HIGH: "Çok Yüksek",
    ConfidenceLevel.VERIFIED: "Doğrulanmış",
}


class TurkishLabelRegistry:
    """Türkçe arayüz etiketlerini merkezi olarak yönetir."""

    def __init__(self) -> None:
        self._custom_labels: dict[str, str] = {}

    def register(
        self,
        key: str,
        label: str,
        *,
        replace: bool = False,
    ) -> None:
        normalized_key = key.strip()
        normalized_label = label.strip()

        if not normalized_key:
            raise ValueError("Etiket anahtarı boş olamaz.")

        if not normalized_label:
            raise ValueError("Türkçe etiket boş olamaz.")

        if normalized_key in self._custom_labels and not replace:
            raise ValueError(
                f"Etiket anahtarı zaten kayıtlı: {normalized_key}"
            )

        self._custom_labels[normalized_key] = normalized_label

    def get(
        self,
        value: Enum | str,
        *,
        default: str | None = None,
    ) -> str:
        if isinstance(value, EntityKind):
            return _ENTITY_LABELS[value]

        if isinstance(value, RuntimeState):
            return _RUNTIME_LABELS[value]

        if isinstance(value, VisualStatus):
            return _VISUAL_STATUS_LABELS[value]

        if isinstance(value, ConfidenceLevel):
            return _CONFIDENCE_LABELS[value]

        key = str(value)

        if key in self._custom_labels:
            return self._custom_labels[key]

        if default is not None:
            return default

        return key

    def export(self) -> Mapping[str, str]:
        payload: dict[str, str] = {}

        for item, label in _ENTITY_LABELS.items():
            payload[f"entity.{item.value}"] = label

        for item, label in _RUNTIME_LABELS.items():
            payload[f"runtime.{item.value}"] = label

        for item, label in _VISUAL_STATUS_LABELS.items():
            payload[f"visual_status.{item.value}"] = label

        for item, label in _CONFIDENCE_LABELS.items():
            payload[f"confidence.{item.value}"] = label

        payload.update(self._custom_labels)

        return payload


_DEFAULT_REGISTRY = TurkishLabelRegistry()


def get_turkish_label(
    value: Enum | str,
    *,
    default: str | None = None,
) -> str:
    """Varlık veya durum için Türkçe arayüz etiketini döndürür."""

    return _DEFAULT_REGISTRY.get(
        value,
        default=default,
    )


def ensure_utf8_text(value: Any) -> str:
    """Arayüz metnini UTF-8 uyumlu ve kırpılmış hale getirir."""

    text = str(value).strip()

    if not text:
        raise ValueError("Arayüz metni boş olamaz.")

    text.encode("utf-8")

    return text
