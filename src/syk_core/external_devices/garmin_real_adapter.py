from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from threading import RLock
from typing import Any

from .connection_model import (
    DeviceDataAuthority,
    DeviceEndpoint,
    DeviceProtocolProfile,
    DeviceTransportType,
    RawDataAvailability,
)
from .device_model import (
    DeviceCapability,
    DeviceConnectionState,
    DeviceHealth,
    DeviceIdentity,
    DeviceProfile,
    ExternalDevice,
)
from .nmea_model import (
    NmeaSentence,
    parse_depth_meters,
    parse_nmea_sentence,
    parse_water_temperature_c,
)


@dataclass(frozen=True, slots=True)
class GarminConnectionSnapshot:
    connected: bool
    endpoint: dict[str, Any]
    protocol: dict[str, Any]
    depth_m: float | None
    water_temperature_c: float | None
    sentence_count: int
    rejected_sentence_count: int
    real_device_data: bool
    vendor_raw_sonar_available: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "connected": self.connected,
            "endpoint": dict(self.endpoint),
            "protocol": dict(self.protocol),
            "depth_m": self.depth_m,
            "water_temperature_c": (
                self.water_temperature_c
            ),
            "sentence_count": self.sentence_count,
            "rejected_sentence_count": (
                self.rejected_sentence_count
            ),
            "real_device_data": self.real_device_data,
            "vendor_raw_sonar_available": (
                self.vendor_raw_sonar_available
            ),
        }


class GarminRealAdapter(ExternalDevice):
    def __init__(
        self,
        *,
        identity: DeviceIdentity,
        endpoint: DeviceEndpoint,
        protocol: DeviceProtocolProfile | None = None,
    ) -> None:
        if endpoint.transport == DeviceTransportType.MOCK:
            raise ValueError(
                "GerÃ§ek Garmin baÄŸdaÅŸtÄ±rÄ±cÄ±sÄ± mock baÄŸlantÄ± kabul etmez."
            )

        profile = DeviceProfile(
            identity=identity,
            capabilities=(
                DeviceCapability.DEPTH,
                DeviceCapability.WATER_TEMPERATURE,
                DeviceCapability.GPS,
                DeviceCapability.BOTTOM_PROFILE,
                DeviceCapability.RECORDING,
            ),
            shallow_coast_priority_depth_m=2.0,
            metadata={
                "adapter_mode": "real-contract",
                "real_protocol_connected": False,
                "manufacturer_software_modified": False,
            },
        )

        super().__init__(profile)

        self._endpoint = endpoint
        self._protocol = protocol or (
            DeviceProtocolProfile(
                protocol_name="NMEA-compatible",
                protocol_version=None,
                authority=(
                    DeviceDataAuthority.EXTERNAL_LIVE
                ),
                raw_data_availability=(
                    RawDataAvailability.PARTIAL
                ),
                supports_depth=True,
                supports_water_temperature=True,
                supports_position=True,
                supports_targets=False,
                supports_bottom_profile=False,
                supports_vendor_raw_sonar=False,
                notes=(
                    "YalnÄ±z desteklenen standart veri alanlarÄ± iÅŸlenir.",
                    "Garmin kapalÄ± yazÄ±lÄ±mÄ±na mÃ¼dahale edilmez.",
                    "Ham Ã¼retici sonar akÄ±ÅŸÄ± destekleniyor varsayÄ±lmaz.",
                ),
            )
        )

        self._lock = RLock()
        self._sentence_count = 0
        self._rejected_sentence_count = 0
        self._latest_depth_m: float | None = None
        self._latest_water_temperature_c: (
            float | None
        ) = None

    @property
    def endpoint(self) -> DeviceEndpoint:
        return self._endpoint

    @property
    def protocol(
        self,
    ) -> DeviceProtocolProfile:
        return self._protocol

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

    def ingest_nmea(
        self,
        sentence: str,
        *,
        validate_checksum: bool = True,
    ) -> NmeaSentence:
        with self._lock:
            if (
                self.connection_state
                != DeviceConnectionState.CONNECTED
            ):
                raise RuntimeError(
                    "GerÃ§ek Garmin baÄŸdaÅŸtÄ±rÄ±cÄ±sÄ± baÄŸlÄ± deÄŸil."
                )

            try:
                parsed = parse_nmea_sentence(
                    sentence,
                    validate_checksum=validate_checksum,
                )
            except ValueError:
                self._rejected_sentence_count += 1
                self._set_state(
                    connection_state=(
                        DeviceConnectionState.DEGRADED
                    ),
                    health=DeviceHealth.WARNING,
                    last_error=(
                        "GeÃ§ersiz NMEA cÃ¼mlesi reddedildi."
                    ),
                )
                raise

            self._sentence_count += 1

            depth_m = parse_depth_meters(
                parsed
            )

            if depth_m is not None:
                if depth_m < 0:
                    raise ValueError(
                        "Negatif derinlik kabul edilemez."
                    )

                self._latest_depth_m = depth_m

            water_temperature_c = (
                parse_water_temperature_c(
                    parsed
                )
            )

            if water_temperature_c is not None:
                self._latest_water_temperature_c = (
                    water_temperature_c
                )

            self._set_state(
                connection_state=(
                    DeviceConnectionState.CONNECTED
                ),
                health=DeviceHealth.HEALTHY,
            )

            return parsed

    def ingest_many(
        self,
        sentences: Iterable[str],
        *,
        validate_checksum: bool = True,
    ) -> tuple[NmeaSentence, ...]:
        return tuple(
            self.ingest_nmea(
                sentence,
                validate_checksum=validate_checksum,
            )
            for sentence in sentences
        )

    def connection_snapshot(
        self,
    ) -> GarminConnectionSnapshot:
        return GarminConnectionSnapshot(
            connected=(
                self.connection_state
                == DeviceConnectionState.CONNECTED
            ),
            endpoint=self.endpoint.to_dict(),
            protocol=self.protocol.to_dict(),
            depth_m=self._latest_depth_m,
            water_temperature_c=(
                self._latest_water_temperature_c
            ),
            sentence_count=self._sentence_count,
            rejected_sentence_count=(
                self._rejected_sentence_count
            ),
            real_device_data=True,
            vendor_raw_sonar_available=(
                self.protocol.supports_vendor_raw_sonar
            ),
        )

    def status_snapshot(self) -> dict[str, Any]:
        data = super().status_snapshot()

        data["endpoint"] = self.endpoint.to_dict()
        data["protocol"] = self.protocol.to_dict()
        data["connection_snapshot"] = (
            self.connection_snapshot().to_dict()
        )

        return data