"""Canlı ekosistem motoru numaralandırmaları."""

from __future__ import annotations

from enum import StrEnum


class EcosystemEntityType(StrEnum):
    """Canlı ekosistem varlık türü."""

    FISH = "fish"
    PLANT = "plant"
    TREE = "tree"
    SHRUB = "shrub"
    HERB = "herb"
    AQUATIC_PLANT = "aquatic_plant"
    ALGAE = "algae"
    MOSS = "moss"
    LICHEN = "lichen"
    FUNGI = "fungi"


class ObservationSource(StrEnum):
    """Gözlemin üretildiği kaynak."""

    LIVE_CAMERA = "live_camera"
    PHOTO = "photo"
    VIDEO_FRAME = "video_frame"
    SONAR = "sonar"
    MANUAL = "manual"
    DRONE = "drone"
    LIDAR = "lidar"
    SATELLITE = "satellite"
    SENSOR = "sensor"


class SalinityType(StrEnum):
    """Su tuzluluk sınıfı."""

    FRESHWATER = "freshwater"
    BRACKISH = "brackish"
    SALTWATER = "saltwater"
    UNKNOWN = "unknown"


class WaterBodyType(StrEnum):
    """Su kütlesi türü."""

    RESERVOIR = "reservoir"
    LAKE = "lake"
    RIVER = "river"
    STREAM = "stream"
    POND = "pond"
    WETLAND = "wetland"
    SEA = "sea"
    COAST = "coast"
    UNKNOWN = "unknown"


class ConservationState(StrEnum):
    """Tür koruma ve değerlendirme durumu."""

    UNKNOWN = "unknown"
    COMMON = "common"
    LOCAL = "local"
    RARE = "rare"
    PROTECTED = "protected"
    INVASIVE = "invasive"
    REVIEW_REQUIRED = "review_required"


class PlantCondition(StrEnum):
    """Bitkinin gözlenen sağlık durumu."""

    UNKNOWN = "unknown"
    HEALTHY = "healthy"
    STRESSED = "stressed"
    DRYING = "drying"
    DISEASE_SUSPECTED = "disease_suspected"
    PEST_DAMAGE = "pest_damage"
    PHYSICAL_DAMAGE = "physical_damage"
    DEAD = "dead"


class SonarTargetState(StrEnum):
    """Sonar hedefinin çalışma durumu."""

    NEW = "new"
    TRACKED = "tracked"
    CLASSIFYING = "classifying"
    MATCHED = "matched"
    LOST = "lost"
    REJECTED = "rejected"
