"""SyKaşif ortak çekirdek numaralandırmaları."""

from __future__ import annotations

from enum import StrEnum


class EntityStatus(StrEnum):
    """Ortak varlık yaşam döngüsü."""

    DRAFT = "draft"
    ACTIVE = "active"
    PROCESSING = "processing"
    WAITING = "waiting"
    COMPLETED = "completed"
    ARCHIVED = "archived"
    REJECTED = "rejected"


class ResearchCategory(StrEnum):
    """Araştırma noktasının ana inceleme amacı."""

    GENERAL = "general"
    ARCHAEOLOGY = "archaeology"
    HISTORY = "history"
    GEOLOGY = "geology"
    HYDROGEOLOGY = "hydrogeology"
    BOTANY = "botany"
    SOIL = "soil"
    WATER = "water"
    ASTRONOMY = "astronomy"
    ARCHAEOSTRONOMY = "archaeoastronomy"
    ENVIRONMENT = "environment"
    MULTIDISCIPLINARY = "multidisciplinary"


class LayerCategory(StrEnum):
    """SYK Atlas katman türleri."""

    BASE_MAP = "base_map"
    SATELLITE = "satellite"
    TOPOGRAPHY = "topography"
    GEOLOGY = "geology"
    HYDROLOGY = "hydrology"
    HYDROGEOLOGY = "hydrogeology"
    VEGETATION = "vegetation"
    CADASTRAL = "cadastral"
    ROADS = "roads"
    ARTIFICIAL_STRUCTURES = "artificial_structures"
    ARCHAEOLOGY = "archaeology"
    HISTORY = "history"
    TEMPORAL = "temporal"
    LIDAR = "lidar"
    DRONE = "drone"
    GPS = "gps"
    RTK = "rtk"
    MAGNETIC = "magnetic"
    GRAVITY = "gravity"
    SPECTRAL = "spectral"
    THERMAL = "thermal"
    ERT = "ert"
    GPR = "gpr"
    SEISMIC = "seismic"
    CHEMISTRY = "chemistry"
    SOIL = "soil"
    WATER = "water"
    BOTANICAL = "botanical"
    EVIDENCE = "evidence"
    EXPERT = "expert"
    REPORT = "report"
    CUSTOM = "custom"


class LayerStatus(StrEnum):
    """Katman çalışma durumu."""

    AVAILABLE = "available"
    LOADING = "loading"
    ACTIVE = "active"
    HIDDEN = "hidden"
    UNAVAILABLE = "unavailable"
    ERROR = "error"


class EvidenceKind(StrEnum):
    """Kanıt kayıt türleri."""

    PHOTO = "photo"
    VIDEO = "video"
    VIDEO_FRAME = "video_frame"
    AUDIO = "audio"
    DOCUMENT = "document"
    MAP = "map"
    DRONE = "drone"
    LIDAR = "lidar"
    GPS = "gps"
    RTK = "rtk"
    THREE_D_MODEL = "three_d_model"
    GEOLOGY = "geology"
    HYDROGEOLOGY = "hydrogeology"
    MAGNETIC = "magnetic"
    GRAVITY = "gravity"
    SPECTRAL = "spectral"
    THERMAL = "thermal"
    ERT = "ert"
    GPR = "gpr"
    SEISMIC = "seismic"
    CHEMISTRY = "chemistry"
    SOIL = "soil"
    WATER = "water"
    BOTANICAL = "botanical"
    SAMPLE = "sample"
    LABORATORY = "laboratory"
    EXPERT_OPINION = "expert_opinion"
    AI_ANALYSIS = "ai_analysis"
    REPORT = "report"
    MANIFEST = "manifest"
    DIGITAL_SIGNATURE = "digital_signature"


class EvidenceStatus(StrEnum):
    """Kanıt doğrulama durumu."""

    COLLECTED = "collected"
    PROCESSING = "processing"
    REVIEW_REQUIRED = "review_required"
    VERIFIED = "verified"
    REJECTED = "rejected"
    ARCHIVED = "archived"


class VerificationLevel(StrEnum):
    """Kanıtın doğrulama seviyesi."""

    UNVERIFIED = "unverified"
    SOURCE_CONFIRMED = "source_confirmed"
    HASH_CONFIRMED = "hash_confirmed"
    CROSS_CONFIRMED = "cross_confirmed"
    EXPERT_CONFIRMED = "expert_confirmed"
    DIGITALLY_VERIFIED = "digitally_verified"


class AccuracySource(StrEnum):
    """Konum doğruluğunu üreten kaynak."""

    UNKNOWN = "unknown"
    DEVICE_GPS = "device_gps"
    EXTERNAL_GPS = "external_gps"
    RTK_FLOAT = "rtk_float"
    RTK_FIXED = "rtk_fixed"
    MANUAL = "manual"
    IMPORTED = "imported"
