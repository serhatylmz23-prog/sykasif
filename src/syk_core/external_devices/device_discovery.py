from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from .connection_model import (
    DeviceEndpoint,
    DeviceTransportType,
)


@dataclass(frozen=True, slots=True)
class DiscoveredDeviceEndpoint:
    discovery_id: str
    manufacturer_hint: str
    model_hint: str
    endpoint: DeviceEndpoint
    verified: bool
    discovery_source: str
    metadata: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["endpoint"] = (
            self.endpoint.to_dict()
        )

        return data


class DeviceDiscoveryService:
    def discover(
        self,
        *,
        include_mock_candidates: bool = False,
    ) -> tuple[DiscoveredDeviceEndpoint, ...]:
        candidates: list[
            DiscoveredDeviceEndpoint
        ] = []

        if include_mock_candidates:
            candidates.append(
                DiscoveredDeviceEndpoint(
                    discovery_id=(
                        "discovery-garmin-file-replay"
                    ),
                    manufacturer_hint="Garmin",
                    model_hint="NMEA Replay Candidate",
                    endpoint=DeviceEndpoint(
                        transport=(
                            DeviceTransportType.FILE_REPLAY
                        ),
                        source_path=(
                            "artifacts/device_replay/"
                            "garmin_nmea_sample.log"
                        ),
                        metadata={
                            "simulation_only": True,
                        },
                    ),
                    verified=False,
                    discovery_source=(
                        "deterministic-development-profile"
                    ),
                    metadata={
                        "real_device": False,
                        "automatic_connection": False,
                    },
                )
            )

        return tuple(candidates)


device_discovery_service = DeviceDiscoveryService()