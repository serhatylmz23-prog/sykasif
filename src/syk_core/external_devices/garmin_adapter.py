from __future__ import annotations

from dataclasses import dataclass
from random import Random
from threading import RLock

from .device_model import (
    DeviceCapability,
    DeviceConnectionState,
    DeviceHealth,
    DeviceIdentity,
    DeviceProfile,
    ExternalDevice,
)
from .gps_model import GpsFix, GpsFixQuality
from .sonar_model import (
    BottomClassification,
    SonarFrame,
    SonarTarget,
    SonarTargetType,
)


@dataclass(frozen=True, slots=True)
class GarminMockConfiguration:
    latitude: float = 38.7123
    longitude: float = 38.4521
    altitude_m: float | None = 845.0
    accuracy_m: float = 2.0
    minimum_depth_m: float = 0.35
    maximum_depth_m: float = 2.0
    water_temperature_c: float = 19.5
    seed: int = 1903

    def __post_init__(self) -> None:
        if self.minimum_depth_m < 0:
            raise ValueError(
                "Asgari derinlik negatif olamaz."
            )

        if (
            self.maximum_depth_m
            < self.minimum_depth_m
        ):
            raise ValueError(
                "Azami derinlik asgari derinlikten "
                "küçük olamaz."
            )


class GarminAdapter(ExternalDevice):
    def __init__(
        self,
        configuration: (
            GarminMockConfiguration | None
        ) = None,
    ) -> None:
        self._configuration = (
            configuration
            or GarminMockConfiguration()
        )

        identity = DeviceIdentity(
            manufacturer="Garmin",
            model="Generic Sonar Adapter",
            serial_number="MOCK-GARMIN-001",
            device_id="garmin-sonar-mock-001",
        )

        profile = DeviceProfile(
            identity=identity,
            capabilities=(
                DeviceCapability.SONAR,
                DeviceCapability.DEPTH,
                DeviceCapability.WATER_TEMPERATURE,
                DeviceCapability.GPS,
                DeviceCapability.BOTTOM_PROFILE,
                DeviceCapability.TARGET_DETECTION,
                DeviceCapability.RECORDING,
            ),
            shallow_coast_priority_depth_m=2.0,
            metadata={
                "adapter_mode": "mock",
                "real_protocol_connected": False,
                "manufacturer_software_modified": False,
            },
        )

        super().__init__(profile)

        self._lock = RLock()
        self._random = Random(
            self._configuration.seed
        )
        self._frame_number = 0

    @property
    def configuration(
        self,
    ) -> GarminMockConfiguration:
        return self._configuration

    def connect(self) -> None:
        with self._lock:
            self._set_state(
                connection_state=(
                    DeviceConnectionState.CONNECTING
                ),
                health=DeviceHealth.UNKNOWN,
            )

            self._set_state(
                connection_state=(
                    DeviceConnectionState.CONNECTED
                ),
                health=DeviceHealth.HEALTHY,
            )

    def disconnect(self) -> None:
        with self._lock:
            self._set_state(
                connection_state=(
                    DeviceConnectionState.DISCONNECTED
                ),
                health=DeviceHealth.UNKNOWN,
            )

    def read_frame(self) -> SonarFrame:
        with self._lock:
            if (
                self.connection_state
                != DeviceConnectionState.CONNECTED
            ):
                raise RuntimeError(
                    "Garmin bağdaştırıcısı bağlı değil."
                )

            self._frame_number += 1

            minimum = (
                self.configuration.minimum_depth_m
            )
            maximum = (
                self.configuration.maximum_depth_m
            )

            depth_m = round(
                self._random.uniform(
                    minimum,
                    maximum,
                ),
                2,
            )

            latitude = (
                self.configuration.latitude
                + self._random.uniform(
                    -0.00002,
                    0.00002,
                )
            )

            longitude = (
                self.configuration.longitude
                + self._random.uniform(
                    -0.00002,
                    0.00002,
                )
            )

            gps_fix = GpsFix.create(
                latitude=latitude,
                longitude=longitude,
                altitude_m=(
                    self.configuration.altitude_m
                ),
                accuracy_m=(
                    self.configuration.accuracy_m
                ),
                quality=GpsFixQuality.STANDARD,
            )

            targets: tuple[SonarTarget, ...]

            if self._frame_number % 2 == 0:
                targets = (
                    SonarTarget.create(
                        target_type=(
                            SonarTargetType.FISH
                        ),
                        depth_m=max(
                            0.1,
                            round(depth_m * 0.62, 2),
                        ),
                        confidence=0.74,
                        relative_x_m=0.8,
                        relative_y_m=-0.35,
                        metadata={
                            "classification_state": (
                                "supporting-indication"
                            ),
                            "species_identified": False,
                        },
                    ),
                )
            else:
                targets = ()

            bottom = (
                BottomClassification.VEGETATED
                if depth_m < 0.9
                else BottomClassification.MEDIUM
            )

            return SonarFrame.create(
                device_id=(
                    self.profile.identity.device_id
                ),
                depth_m=depth_m,
                water_temperature_c=(
                    self.configuration
                    .water_temperature_c
                ),
                bottom_classification=bottom,
                bottom_confidence=0.81,
                gps_fix=gps_fix,
                targets=targets,
                raw_data_available=False,
                source_mode="mock",
                metadata={
                    "frame_number": self._frame_number,
                    "priority_profile": (
                        "shallow-coast-0-2m"
                    ),
                    "evidence_status": "unverified",
                    "real_device_data": False,
                },
            )