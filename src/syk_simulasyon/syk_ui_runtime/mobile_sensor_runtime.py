from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
import json
from math import isfinite
from threading import RLock
from typing import Any
from uuid import uuid4


PERMISSION_STATES = {
    "unknown",
    "prompt",
    "granted",
    "denied",
    "unsupported",
}

SENSOR_TYPES = {
    "camera",
    "microphone",
    "location",
}

CAMERA_FACING_MODES = {
    "user",
    "environment",
    "unknown",
}


@dataclass(frozen=True, slots=True)
class SensorPermission:
    sensor_type: str
    state: str
    updated_at: str

    def validate(self) -> None:
        if self.sensor_type not in SENSOR_TYPES:
            raise ValueError(
                "Geçersiz sensör türü."
            )

        if self.state not in PERMISSION_STATES:
            raise ValueError(
                "Geçersiz izin durumu."
            )

    def as_dict(self) -> dict[str, Any]:
        return {
            "sensor_type": self.sensor_type,
            "state": self.state,
            "updated_at": self.updated_at,
        }


@dataclass(frozen=True, slots=True)
class CameraState:
    active: bool
    facing_mode: str
    width: int | None
    height: int | None
    frame_rate: float | None
    stream_id: str | None
    started_at: str | None
    stopped_at: str | None

    def validate(self) -> None:
        if (
            self.facing_mode
            not in CAMERA_FACING_MODES
        ):
            raise ValueError(
                "Geçersiz kamera yönü."
            )

        if (
            self.width is not None
            and self.width <= 0
        ):
            raise ValueError(
                "Kamera genişliği pozitif "
                "olmalıdır."
            )

        if (
            self.height is not None
            and self.height <= 0
        ):
            raise ValueError(
                "Kamera yüksekliği pozitif "
                "olmalıdır."
            )

        if (
            self.frame_rate is not None
            and (
                self.frame_rate <= 0
                or not isfinite(
                    self.frame_rate
                )
            )
        ):
            raise ValueError(
                "Kare hızı pozitif ve sonlu "
                "olmalıdır."
            )

    def as_dict(self) -> dict[str, Any]:
        return {
            "active": self.active,
            "facing_mode": self.facing_mode,
            "width": self.width,
            "height": self.height,
            "frame_rate": self.frame_rate,
            "stream_id": self.stream_id,
            "started_at": self.started_at,
            "stopped_at": self.stopped_at,
        }


@dataclass(frozen=True, slots=True)
class MicrophoneState:
    active: bool
    sample_rate: int | None
    channels: int | None
    stream_id: str | None
    started_at: str | None
    stopped_at: str | None

    def validate(self) -> None:
        if (
            self.sample_rate is not None
            and self.sample_rate < 8000
        ):
            raise ValueError(
                "Mikrofon örnekleme hızı "
                "en az 8000 Hz olmalıdır."
            )

        if (
            self.channels is not None
            and self.channels not in {
                1,
                2,
            }
        ):
            raise ValueError(
                "Yalnız tek veya çift kanal "
                "desteklenir."
            )

    def as_dict(self) -> dict[str, Any]:
        return {
            "active": self.active,
            "sample_rate": self.sample_rate,
            "channels": self.channels,
            "stream_id": self.stream_id,
            "started_at": self.started_at,
            "stopped_at": self.stopped_at,
        }


@dataclass(frozen=True, slots=True)
class LocationReading:
    latitude: float
    longitude: float
    accuracy_meters: float
    altitude_meters: float | None
    heading_degrees: float | None
    speed_meters_per_second: float | None
    captured_at: str
    source: str

    def validate(self) -> None:
        if not -90.0 <= self.latitude <= 90.0:
            raise ValueError(
                "Enlem -90 ile 90 arasında "
                "olmalıdır."
            )

        if not -180.0 <= self.longitude <= 180.0:
            raise ValueError(
                "Boylam -180 ile 180 arasında "
                "olmalıdır."
            )

        if (
            self.accuracy_meters < 0
            or not isfinite(
                self.accuracy_meters
            )
        ):
            raise ValueError(
                "Konum doğruluk değeri geçersiz."
            )

        for value, title in (
            (
                self.altitude_meters,
                "Yükseklik",
            ),
            (
                self.heading_degrees,
                "Yön",
            ),
            (
                self.speed_meters_per_second,
                "Hız",
            ),
        ):
            if (
                value is not None
                and not isfinite(value)
            ):
                raise ValueError(
                    f"{title} değeri sonlu "
                    "olmalıdır."
                )

        if (
            self.heading_degrees is not None
            and not (
                0.0
                <= self.heading_degrees
                <= 360.0
            )
        ):
            raise ValueError(
                "Yön 0 ile 360 derece "
                "arasında olmalıdır."
            )

        if (
            self.speed_meters_per_second
            is not None
            and self.speed_meters_per_second
            < 0
        ):
            raise ValueError(
                "Hız negatif olamaz."
            )

    def as_dict(self) -> dict[str, Any]:
        return {
            "latitude": round(
                self.latitude,
                8,
            ),
            "longitude": round(
                self.longitude,
                8,
            ),
            "accuracy_meters": round(
                self.accuracy_meters,
                3,
            ),
            "altitude_meters": (
                None
                if self.altitude_meters
                is None
                else round(
                    self.altitude_meters,
                    3,
                )
            ),
            "heading_degrees": (
                None
                if self.heading_degrees
                is None
                else round(
                    self.heading_degrees,
                    3,
                )
            ),
            "speed_meters_per_second": (
                None
                if (
                    self.speed_meters_per_second
                    is None
                )
                else round(
                    self.speed_meters_per_second,
                    3,
                )
            ),
            "captured_at": self.captured_at,
            "source": self.source,
        }


@dataclass(frozen=True, slots=True)
class CapturedFrame:
    frame_id: str
    device_id: str
    media_type: str
    mime_type: str
    byte_count: int
    width: int
    height: int
    captured_at: str
    frame_sha256: str
    source: str
    digital_scope: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema": (
                "sykasif-mobile-frame/v1"
            ),
            "frame_id": self.frame_id,
            "device_id": self.device_id,
            "media_type": self.media_type,
            "mime_type": self.mime_type,
            "byte_count": self.byte_count,
            "width": self.width,
            "height": self.height,
            "captured_at": self.captured_at,
            "frame_sha256": (
                self.frame_sha256
            ),
            "source": self.source,
            "digital_scope": (
                self.digital_scope
            ),
            "field_validation_required": True,
        }


class MobileSensorRuntime:
    def __init__(
        self,
        *,
        maximum_frames: int = 100,
        maximum_locations: int = 500,
    ) -> None:
        if maximum_frames <= 0:
            raise ValueError(
                "Azami kare sayısı pozitif "
                "olmalıdır."
            )

        if maximum_locations <= 0:
            raise ValueError(
                "Azami konum sayısı pozitif "
                "olmalıdır."
            )

        self.maximum_frames = maximum_frames
        self.maximum_locations = (
            maximum_locations
        )

        now = datetime.now(
            UTC
        ).isoformat()

        self._permissions = {
            sensor_type: SensorPermission(
                sensor_type=sensor_type,
                state="unknown",
                updated_at=now,
            )
            for sensor_type
            in SENSOR_TYPES
        }

        self._camera = CameraState(
            active=False,
            facing_mode="unknown",
            width=None,
            height=None,
            frame_rate=None,
            stream_id=None,
            started_at=None,
            stopped_at=None,
        )

        self._microphone = MicrophoneState(
            active=False,
            sample_rate=None,
            channels=None,
            stream_id=None,
            started_at=None,
            stopped_at=None,
        )

        self._locations: list[
            LocationReading
        ] = []

        self._frames: dict[
            str,
            CapturedFrame,
        ] = {}

        self._frame_order: list[str] = []
        self._lock = RLock()

    def update_permission(
        self,
        *,
        sensor_type: str,
        state: str,
    ) -> dict[str, Any]:
        normalized_sensor = (
            sensor_type.strip().lower()
        )

        normalized_state = (
            state.strip().lower()
        )

        permission = SensorPermission(
            sensor_type=normalized_sensor,
            state=normalized_state,
            updated_at=datetime.now(
                UTC
            ).isoformat(),
        )

        permission.validate()

        with self._lock:
            self._permissions[
                normalized_sensor
            ] = permission

        return permission.as_dict()

    def start_camera(
        self,
        *,
        facing_mode: str,
        width: int,
        height: int,
        frame_rate: float,
        stream_id: str | None = None,
    ) -> dict[str, Any]:
        now = datetime.now(
            UTC
        ).isoformat()

        resolved_stream_id = (
            stream_id.strip()
            if stream_id
            else f"CAM-{uuid4().hex[:20]}"
        )

        camera = CameraState(
            active=True,
            facing_mode=(
                facing_mode.strip().lower()
            ),
            width=width,
            height=height,
            frame_rate=float(frame_rate),
            stream_id=resolved_stream_id,
            started_at=now,
            stopped_at=None,
        )

        camera.validate()

        with self._lock:
            self._camera = camera

        return camera.as_dict()

    def stop_camera(
        self,
    ) -> dict[str, Any]:
        with self._lock:
            current = self._camera

            stopped = CameraState(
                active=False,
                facing_mode=(
                    current.facing_mode
                ),
                width=current.width,
                height=current.height,
                frame_rate=current.frame_rate,
                stream_id=current.stream_id,
                started_at=current.started_at,
                stopped_at=datetime.now(
                    UTC
                ).isoformat(),
            )

            self._camera = stopped

        return stopped.as_dict()

    def start_microphone(
        self,
        *,
        sample_rate: int,
        channels: int,
        stream_id: str | None = None,
    ) -> dict[str, Any]:
        now = datetime.now(
            UTC
        ).isoformat()

        resolved_stream_id = (
            stream_id.strip()
            if stream_id
            else f"MIC-{uuid4().hex[:20]}"
        )

        microphone = MicrophoneState(
            active=True,
            sample_rate=sample_rate,
            channels=channels,
            stream_id=resolved_stream_id,
            started_at=now,
            stopped_at=None,
        )

        microphone.validate()

        with self._lock:
            self._microphone = microphone

        return microphone.as_dict()

    def stop_microphone(
        self,
    ) -> dict[str, Any]:
        with self._lock:
            current = self._microphone

            stopped = MicrophoneState(
                active=False,
                sample_rate=(
                    current.sample_rate
                ),
                channels=current.channels,
                stream_id=current.stream_id,
                started_at=current.started_at,
                stopped_at=datetime.now(
                    UTC
                ).isoformat(),
            )

            self._microphone = stopped

        return stopped.as_dict()

    def add_location(
        self,
        reading: LocationReading,
    ) -> dict[str, Any]:
        reading.validate()

        with self._lock:
            self._locations.append(
                reading
            )

            overflow = (
                len(self._locations)
                - self.maximum_locations
            )

            if overflow > 0:
                del self._locations[
                    :overflow
                ]

        return reading.as_dict()

    def capture_frame(
        self,
        *,
        device_id: str,
        data: bytes,
        mime_type: str,
        width: int,
        height: int,
        source: str = "mobile_camera",
    ) -> dict[str, Any]:
        normalized_device = (
            device_id.strip()
        )

        normalized_mime = (
            mime_type.strip().lower()
        )

        normalized_source = (
            source.strip()
        )

        if not normalized_device:
            raise ValueError(
                "Cihaz kimliği boş olamaz."
            )

        if not data:
            raise ValueError(
                "Kamera karesi boş olamaz."
            )

        if normalized_mime not in {
            "image/jpeg",
            "image/png",
            "image/webp",
        }:
            raise ValueError(
                "Desteklenmeyen görüntü türü."
            )

        if width <= 0 or height <= 0:
            raise ValueError(
                "Görüntü ölçüleri pozitif "
                "olmalıdır."
            )

        if not normalized_source:
            raise ValueError(
                "Kare kaynağı boş olamaz."
            )

        frame_id = (
            f"MFR-{uuid4().hex[:24]}"
        )

        captured = CapturedFrame(
            frame_id=frame_id,
            device_id=normalized_device,
            media_type="image",
            mime_type=normalized_mime,
            byte_count=len(data),
            width=width,
            height=height,
            captured_at=datetime.now(
                UTC
            ).isoformat(),
            frame_sha256=sha256(
                data
            ).hexdigest(),
            source=normalized_source,
            digital_scope=(
                "browser_captured_frame"
            ),
        )

        with self._lock:
            self._frames[
                frame_id
            ] = captured

            self._frame_order.append(
                frame_id
            )

            overflow = (
                len(self._frame_order)
                - self.maximum_frames
            )

            if overflow > 0:
                expired = self._frame_order[
                    :overflow
                ]

                del self._frame_order[
                    :overflow
                ]

                for expired_id in expired:
                    self._frames.pop(
                        expired_id,
                        None,
                    )

        return captured.as_dict()

    def get_frame(
        self,
        frame_id: str,
    ) -> dict[str, Any]:
        with self._lock:
            try:
                frame = self._frames[
                    frame_id
                ]

            except KeyError as error:
                raise KeyError(
                    "Mobil kamera karesi "
                    "bulunamadı."
                ) from error

        return frame.as_dict()

    def recent_frames(
        self,
        *,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        if limit <= 0:
            raise ValueError(
                "Kare sınırı pozitif "
                "olmalıdır."
            )

        with self._lock:
            ids = self._frame_order[
                -limit:
            ]

            return [
                self._frames[
                    frame_id
                ].as_dict()
                for frame_id in ids
            ]

    def recent_locations(
        self,
        *,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        if limit <= 0:
            raise ValueError(
                "Konum sınırı pozitif "
                "olmalıdır."
            )

        with self._lock:
            readings = self._locations[
                -limit:
            ]

        return [
            reading.as_dict()
            for reading in readings
        ]

    def snapshot(
        self,
    ) -> dict[str, Any]:
        with self._lock:
            unsigned = {
                "schema": (
                    "sykasif-mobile-sensor-runtime/v1"
                ),
                "permissions": {
                    key: value.as_dict()
                    for key, value
                    in self._permissions.items()
                },
                "camera": (
                    self._camera.as_dict()
                ),
                "microphone": (
                    self._microphone.as_dict()
                ),
                "location_count": len(
                    self._locations
                ),
                "frame_count": len(
                    self._frame_order
                ),
                "latest_location": (
                    self._locations[-1]
                    .as_dict()
                    if self._locations
                    else None
                ),
                "status": "ready",
                "native_sensor_bridge_ready": False,
            }

        canonical = json.dumps(
            unsigned,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")

        return {
            **unsigned,
            "snapshot_sha256": sha256(
                canonical
            ).hexdigest(),
        }


mobile_sensor_runtime = (
    MobileSensorRuntime()
)