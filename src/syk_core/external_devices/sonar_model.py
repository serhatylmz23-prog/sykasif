from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import uuid4

from .gps_model import GpsFix


class SonarTargetType(StrEnum):
    UNKNOWN = "unknown"
    FISH = "fish"
    VEGETATION = "vegetation"
    ROCK = "rock"
    STRUCTURE = "structure"
    DEBRIS = "debris"


class BottomClassification(StrEnum):
    UNKNOWN = "unknown"
    SOFT = "soft"
    MEDIUM = "medium"
    HARD = "hard"
    ROCKY = "rocky"
    VEGETATED = "vegetated"


@dataclass(frozen=True, slots=True)
class SonarTarget:
    target_id: str
    target_type: SonarTargetType
    depth_m: float
    confidence: float
    relative_x_m: float | None = None
    relative_y_m: float | None = None
    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        if not self.target_id.strip():
            raise ValueError(
                "Sonar hedef kimliği boş bırakılamaz."
            )

        if self.depth_m < 0:
            raise ValueError(
                "Hedef derinliği negatif olamaz."
            )

        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(
                "Güven değeri 0 ile 1 arasında olmalıdır."
            )

    @classmethod
    def create(
        cls,
        *,
        target_type: SonarTargetType,
        depth_m: float,
        confidence: float,
        relative_x_m: float | None = None,
        relative_y_m: float | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> "SonarTarget":
        return cls(
            target_id=str(uuid4()),
            target_type=target_type,
            depth_m=depth_m,
            confidence=confidence,
            relative_x_m=relative_x_m,
            relative_y_m=relative_y_m,
            metadata=metadata or {},
        )

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["target_type"] = self.target_type.value

        return data


@dataclass(frozen=True, slots=True)
class SonarFrame:
    frame_id: str
    device_id: str
    timestamp: str
    depth_m: float
    water_temperature_c: float | None
    bottom_classification: BottomClassification
    bottom_confidence: float
    gps_fix: GpsFix | None
    targets: tuple[SonarTarget, ...]
    raw_data_available: bool
    source_mode: str
    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        if not self.frame_id.strip():
            raise ValueError(
                "Sonar kare kimliği boş bırakılamaz."
            )

        if not self.device_id.strip():
            raise ValueError(
                "Cihaz kimliği boş bırakılamaz."
            )

        if self.depth_m < 0:
            raise ValueError(
                "Derinlik negatif olamaz."
            )

        if not 0.0 <= self.bottom_confidence <= 1.0:
            raise ValueError(
                "Dip güven değeri 0 ile 1 arasında olmalıdır."
            )

    @classmethod
    def create(
        cls,
        *,
        device_id: str,
        depth_m: float,
        water_temperature_c: float | None,
        bottom_classification: BottomClassification,
        bottom_confidence: float,
        gps_fix: GpsFix | None,
        targets: tuple[SonarTarget, ...] = (),
        raw_data_available: bool = False,
        source_mode: str = "mock",
        metadata: dict[str, Any] | None = None,
    ) -> "SonarFrame":
        return cls(
            frame_id=str(uuid4()),
            device_id=device_id,
            timestamp=datetime.now(
                UTC
            ).isoformat(),
            depth_m=depth_m,
            water_temperature_c=water_temperature_c,
            bottom_classification=(
                bottom_classification
            ),
            bottom_confidence=bottom_confidence,
            gps_fix=gps_fix,
            targets=targets,
            raw_data_available=raw_data_available,
            source_mode=source_mode.strip(),
            metadata=metadata or {},
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "frame_id": self.frame_id,
            "device_id": self.device_id,
            "timestamp": self.timestamp,
            "depth_m": self.depth_m,
            "water_temperature_c": (
                self.water_temperature_c
            ),
            "bottom_classification": (
                self.bottom_classification.value
            ),
            "bottom_confidence": (
                self.bottom_confidence
            ),
            "gps_fix": (
                self.gps_fix.to_dict()
                if self.gps_fix is not None
                else None
            ),
            "targets": [
                target.to_dict()
                for target in self.targets
            ],
            "raw_data_available": (
                self.raw_data_available
            ),
            "source_mode": self.source_mode,
            "metadata": dict(self.metadata),
        }