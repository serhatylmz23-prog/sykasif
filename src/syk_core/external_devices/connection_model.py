from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any


class DeviceTransportType(StrEnum):
    SERIAL = "serial"
    USB = "usb"
    TCP = "tcp"
    UDP = "udp"
    NMEA_0183 = "nmea-0183"
    NMEA_2000_GATEWAY = "nmea-2000-gateway"
    FILE_REPLAY = "file-replay"
    MOCK = "mock"


class DeviceDataAuthority(StrEnum):
    SIMULATION = "simulation"
    EXTERNAL_LIVE = "external-live"
    EXTERNAL_REPLAY = "external-replay"
    MANUAL_IMPORT = "manual-import"


class RawDataAvailability(StrEnum):
    AVAILABLE = "available"
    PARTIAL = "partial"
    UNAVAILABLE = "unavailable"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class DeviceEndpoint:
    transport: DeviceTransportType
    host: str | None = None
    port: int | None = None
    serial_port: str | None = None
    baud_rate: int | None = None
    source_path: str | None = None
    timeout_seconds: float = 5.0
    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        if self.timeout_seconds <= 0:
            raise ValueError(
                "BaÄŸlantÄ± zaman aÅŸÄ±mÄ± sÄ±fÄ±rdan bÃ¼yÃ¼k olmalÄ±dÄ±r."
            )

        if self.port is not None:
            if not 1 <= self.port <= 65535:
                raise ValueError(
                    "AÄŸ portu 1 ile 65535 arasÄ±nda olmalÄ±dÄ±r."
                )

        if self.baud_rate is not None:
            if self.baud_rate <= 0:
                raise ValueError(
                    "Seri baÄŸlantÄ± hÄ±zÄ± sÄ±fÄ±rdan bÃ¼yÃ¼k olmalÄ±dÄ±r."
                )

        if self.transport in {
            DeviceTransportType.TCP,
            DeviceTransportType.UDP,
        }:
            if not self.host or self.port is None:
                raise ValueError(
                    "AÄŸ baÄŸlantÄ±sÄ± iÃ§in host ve port gereklidir."
                )

        if self.transport in {
            DeviceTransportType.SERIAL,
            DeviceTransportType.USB,
            DeviceTransportType.NMEA_0183,
        }:
            if not self.serial_port:
                raise ValueError(
                    "Seri baÄŸlantÄ± iÃ§in port adÄ± gereklidir."
                )

        if self.transport == DeviceTransportType.FILE_REPLAY:
            if not self.source_path:
                raise ValueError(
                    "Dosya tekrar oynatma iÃ§in kaynak yolu gereklidir."
                )

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["transport"] = self.transport.value

        return data


@dataclass(frozen=True, slots=True)
class DeviceProtocolProfile:
    protocol_name: str
    protocol_version: str | None
    authority: DeviceDataAuthority
    raw_data_availability: RawDataAvailability
    supports_depth: bool
    supports_water_temperature: bool
    supports_position: bool
    supports_targets: bool
    supports_bottom_profile: bool
    supports_vendor_raw_sonar: bool
    notes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.protocol_name.strip():
            raise ValueError(
                "Protokol adÄ± boÅŸ bÄ±rakÄ±lamaz."
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "protocol_name": self.protocol_name,
            "protocol_version": self.protocol_version,
            "authority": self.authority.value,
            "raw_data_availability": (
                self.raw_data_availability.value
            ),
            "supports_depth": self.supports_depth,
            "supports_water_temperature": (
                self.supports_water_temperature
            ),
            "supports_position": self.supports_position,
            "supports_targets": self.supports_targets,
            "supports_bottom_profile": (
                self.supports_bottom_profile
            ),
            "supports_vendor_raw_sonar": (
                self.supports_vendor_raw_sonar
            ),
            "notes": list(self.notes),
        }