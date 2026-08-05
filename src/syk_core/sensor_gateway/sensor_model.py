from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import uuid4


class SensorKind(StrEnum):
    SONAR = "sonar"
    GPS = "gps"
    WATER_TEMPERATURE = "water-temperature"
    DEPTH = "depth"
    THERMAL = "thermal"
    SPECTRAL = "spectral"
    MAGNETIC = "magnetic"
    ERT = "ert"
    GPR = "gpr"
    SEISMIC = "seismic"
    BOTANICAL = "botanical"
    SOIL = "soil"
    WATER = "water"
    GENERIC = "generic"


class SensorAuthority(StrEnum):
    SIMULATION = "simulation"
    EXTERNAL_LIVE = "external-live"
    EXTERNAL_REPLAY = "external-replay"
    MANUAL_IMPORT = "manual-import"


class SensorHealth(StrEnum):
    UNKNOWN = "unknown"
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    OFFLINE = "offline"


@dataclass(frozen=True, slots=True)
class SensorSource:
    source_id: str
    name: str
    kind: SensorKind
    authority: SensorAuthority
    health: SensorHealth
    real_device_data: bool
    simulation_data: bool
    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        if not self.source_id.strip():
            raise ValueError(
                "Sensör kaynak kimliği boş bırakılamaz."
            )

        if not self.name.strip():
            raise ValueError(
                "Sensör kaynak adı boş bırakılamaz."
            )

        if (
            self.real_device_data
            and self.simulation_data
        ):
            raise ValueError(
                "Gerçek ve simülasyon verisi aynı kaynakta "
                "birlikte işaretlenemez."
            )

        if (
            self.authority
            == SensorAuthority.SIMULATION
            and not self.simulation_data
        ):
            raise ValueError(
                "Simülasyon yetkisi simülasyon verisi "
                "olarak işaretlenmelidir."
            )

        if (
            self.authority
            == SensorAuthority.EXTERNAL_LIVE
            and not self.real_device_data
        ):
            raise ValueError(
                "Canlı haricî kaynak gerçek cihaz verisi "
                "olarak işaretlenmelidir."
            )

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["kind"] = self.kind.value
        data["authority"] = self.authority.value
        data["health"] = self.health.value

        return data


@dataclass(frozen=True, slots=True)
class SensorEnvelope:
    envelope_id: str
    source_id: str
    kind: SensorKind
    timestamp: str
    sequence: int
    payload: dict[str, Any]
    research_id: str | None
    workspace_id: str | None
    evidence_status: str
    confidence: float
    real_device_data: bool
    simulation_data: bool

    def __post_init__(self) -> None:
        if self.sequence < 1:
            raise ValueError(
                "Sensör sıra numarası birden küçük olamaz."
            )

        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(
                "Güven değeri 0 ile 1 arasında olmalıdır."
            )

        if (
            self.real_device_data
            and self.simulation_data
        ):
            raise ValueError(
                "Sensör paketi hem gerçek hem simülasyon "
                "olarak işaretlenemez."
            )

    @classmethod
    def create(
        cls,
        *,
        source: SensorSource,
        sequence: int,
        payload: dict[str, Any],
        research_id: str | None = None,
        workspace_id: str | None = None,
        evidence_status: str = "candidate-unverified",
        confidence: float = 0.0,
    ) -> "SensorEnvelope":
        return cls(
            envelope_id=str(uuid4()),
            source_id=source.source_id,
            kind=source.kind,
            timestamp=datetime.now(
                UTC
            ).isoformat(),
            sequence=sequence,
            payload=dict(payload),
            research_id=research_id,
            workspace_id=workspace_id,
            evidence_status=evidence_status,
            confidence=confidence,
            real_device_data=source.real_device_data,
            simulation_data=source.simulation_data,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "envelope_id": self.envelope_id,
            "source_id": self.source_id,
            "kind": self.kind.value,
            "timestamp": self.timestamp,
            "sequence": self.sequence,
            "payload": dict(self.payload),
            "research_id": self.research_id,
            "workspace_id": self.workspace_id,
            "evidence_status": self.evidence_status,
            "confidence": self.confidence,
            "real_device_data": self.real_device_data,
            "simulation_data": self.simulation_data,
        }