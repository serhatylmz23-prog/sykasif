from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any


class DeviceConnectionState(StrEnum):
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    DEGRADED = "degraded"
    ERROR = "error"


class DeviceHealth(StrEnum):
    UNKNOWN = "unknown"
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"


class DeviceCapability(StrEnum):
    SONAR = "sonar"
    DEPTH = "depth"
    WATER_TEMPERATURE = "water-temperature"
    GPS = "gps"
    BOTTOM_PROFILE = "bottom-profile"
    TARGET_DETECTION = "target-detection"
    RECORDING = "recording"


@dataclass(frozen=True, slots=True)
class DeviceIdentity:
    manufacturer: str
    model: str
    serial_number: str
    device_id: str

    def __post_init__(self) -> None:
        for field_name in (
            "manufacturer",
            "model",
            "serial_number",
            "device_id",
        ):
            value = getattr(self, field_name).strip()

            if not value:
                raise ValueError(
                    f"{field_name} boş bırakılamaz."
                )

            object.__setattr__(
                self,
                field_name,
                value,
            )

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class DeviceProfile:
    identity: DeviceIdentity
    capabilities: tuple[DeviceCapability, ...]
    shallow_coast_priority_depth_m: float = 2.0
    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        if self.shallow_coast_priority_depth_m <= 0:
            raise ValueError(
                "Sığ kıyı öncelik derinliği "
                "sıfırdan büyük olmalıdır."
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "identity": self.identity.to_dict(),
            "capabilities": [
                capability.value
                for capability in self.capabilities
            ],
            "shallow_coast_priority_depth_m": (
                self.shallow_coast_priority_depth_m
            ),
            "metadata": dict(self.metadata),
        }


class ExternalDevice(ABC):
    def __init__(
        self,
        profile: DeviceProfile,
    ) -> None:
        self._profile = profile
        self._connection_state = (
            DeviceConnectionState.DISCONNECTED
        )
        self._health = DeviceHealth.UNKNOWN
        self._last_error: str | None = None
        self._updated_at = datetime.now(
            UTC
        ).isoformat()

    @property
    def profile(self) -> DeviceProfile:
        return self._profile

    @property
    def connection_state(
        self,
    ) -> DeviceConnectionState:
        return self._connection_state

    @property
    def health(self) -> DeviceHealth:
        return self._health

    @property
    def last_error(self) -> str | None:
        return self._last_error

    def _set_state(
        self,
        *,
        connection_state: DeviceConnectionState,
        health: DeviceHealth,
        last_error: str | None = None,
    ) -> None:
        self._connection_state = connection_state
        self._health = health
        self._last_error = last_error
        self._updated_at = datetime.now(
            UTC
        ).isoformat()

    def status_snapshot(self) -> dict[str, Any]:
        return {
            "profile": self.profile.to_dict(),
            "connection_state": (
                self.connection_state.value
            ),
            "health": self.health.value,
            "last_error": self.last_error,
            "updated_at": self._updated_at,
        }

    @abstractmethod
    def connect(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def disconnect(self) -> None:
        raise NotImplementedError