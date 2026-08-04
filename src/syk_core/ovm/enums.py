"""OVM numaralandırmaları."""

from __future__ import annotations

from enum import StrEnum


class EntityKind(StrEnum):
    """SyKaşif ortak varlık türleri."""

    LOCATION = "location"
    MAP_PIN = "map_pin"
    RESEARCH_AREA = "research_area"

    PHOTO = "photo"
    VIDEO = "video"
    VIDEO_FRAME = "video_frame"
    AUDIO = "audio"
    DOCUMENT = "document"

    ANNOTATION = "annotation"
    FRAME = "frame"
    MARKER = "marker"
    MEASUREMENT = "measurement"

    SURFACE_MODEL = "surface_model"
    POINT_CLOUD = "point_cloud"
    ADAPTIVE_MESH = "adaptive_mesh"
    THREE_D_MODEL = "three_d_model"

    CAVITY = "cavity"
    CHANNEL = "channel"
    CRACK = "crack"
    MINERAL_VEIN = "mineral_vein"
    SURFACE_EROSION = "surface_erosion"
    ROUGHNESS = "roughness"
    SLOPE = "slope"

    GEOLOGY = "geology"
    HYDROGEOLOGY = "hydrogeology"
    BOTANICAL = "botanical"
    SOIL = "soil"
    WATER = "water"
    CHEMICAL = "chemical"
    MATERIAL = "material"
    MINERAL = "mineral"

    SONAR = "sonar"
    FISH = "fish"
    FISH_SPECIES = "fish_species"
    FISH_OBSERVATION = "fish_observation"

    THERMAL = "thermal"
    SPECTRAL = "spectral"
    MAGNETIC = "magnetic"
    GRAVITY = "gravity"
    ERT = "ert"
    GPR = "gpr"
    SEISMIC = "seismic"
    LIDAR = "lidar"
    GPS = "gps"
    RTK = "rtk"

    HISTORICAL_SITE = "historical_site"
    ARCHAEOLOGICAL_SITE = "archaeological_site"
    STRUCTURE = "structure"
    ARTIFACT = "artifact"
    INSCRIPTION = "inscription"
    STATUE = "statue"
    TIMELINE = "timeline"

    EVIDENCE = "evidence"
    EXPERT_OPINION = "expert_opinion"
    AI_ANALYSIS = "ai_analysis"
    DECISION = "decision"
    REPORT = "report"
    MANIFEST = "manifest"
    DIGITAL_SIGNATURE = "digital_signature"


class RuntimeState(StrEnum):
    """Varlığın çalışma durumu."""

    NEW = "new"
    WAITING = "waiting"
    LOADING = "loading"
    ACTIVE = "active"
    ANALYZING = "analyzing"
    VERIFYING = "verifying"
    COMPLETED = "completed"
    PAUSED = "paused"
    STOPPED = "stopped"
    OFFLINE = "offline"
    ERROR = "error"
    ARCHIVED = "archived"


class VisualStatus(StrEnum):
    """SyFrame ve dinamik ikonlarda kullanılan durum."""

    NEUTRAL = "neutral"
    VERIFIED = "verified"
    ANALYZING = "analyzing"
    REVIEW_REQUIRED = "review_required"
    LOW_CONFIDENCE = "low_confidence"
    INCONSISTENT = "inconsistent"
    RARE_ANOMALY = "rare_anomaly"
    REFERENCE = "reference"
    CRITICAL = "critical"


class ConfidenceLevel(StrEnum):
    """Güven düzeyi."""

    UNKNOWN = "unknown"
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"
    VERIFIED = "verified"
