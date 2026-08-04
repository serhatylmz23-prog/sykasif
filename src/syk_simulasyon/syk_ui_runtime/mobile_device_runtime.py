from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
import json
from threading import RLock
from typing import Any
from uuid import uuid4


DEVICE_TYPES = {
    "phone",
    "tablet",
    "desktop",
    "browser",
}

ORIENTATIONS = {
    "portrait",
    "landscape",
    "unknown",
}

INPUT_MODES = {
    "touch",
    "mouse",
    "hybrid",
    "unknown",
}


@dataclass(frozen=True, slots=True)
class DeviceViewport:
    width: int
    height: int
    pixel_ratio: float
    orientation: str

    def validate(self) -> None:
        if self.width <= 0:
            raise ValueError(
                "Ekran genişliği pozitif olmalıdır."
            )

        if self.height <= 0:
            raise ValueError(
                "Ekran yüksekliği pozitif olmalıdır."
            )

        if self.pixel_ratio <= 0:
            raise ValueError(
                "Piksel oranı pozitif olmalıdır."
            )

        if self.orientation not in ORIENTATIONS:
            raise ValueError(
                "Geçersiz ekran yönü."
            )

    def as_dict(self) -> dict[str, Any]:
        return {
            "width": self.width,
            "height": self.height,
            "pixel_ratio": round(
                self.pixel_ratio,
                3,
            ),
            "orientation": self.orientation,
        }


@dataclass(frozen=True, slots=True)
class DeviceCapabilities:
    touch: bool
    camera: bool
    microphone: bool
    location: bool
    notification: bool
    vibration: bool
    fullscreen: bool
    wake_lock: bool
    online: bool
    input_mode: str

    def validate(self) -> None:
        if self.input_mode not in INPUT_MODES:
            raise ValueError(
                "Geçersiz giriş yöntemi."
            )

    def as_dict(self) -> dict[str, Any]:
        return {
            "touch": self.touch,
            "camera": self.camera,
            "microphone": self.microphone,
            "location": self.location,
            "notification": self.notification,
            "vibration": self.vibration,
            "fullscreen": self.fullscreen,
            "wake_lock": self.wake_lock,
            "online": self.online,
            "input_mode": self.input_mode,
        }


@dataclass(frozen=True, slots=True)
class DeviceRegistration:
    device_id: str
    device_type: str
    title: str
    platform: str
    user_agent: str
    language: str
    timezone: str
    viewport: DeviceViewport
    capabilities: DeviceCapabilities
    trusted: bool
    active: bool
    created_at: str
    updated_at: str
    record_sha256: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema": (
                "sykasif-mobile-device/v1"
            ),
            "device_id": self.device_id,
            "device_type": self.device_type,
            "title": self.title,
            "platform": self.platform,
            "user_agent": self.user_agent,
            "language": self.language,
            "timezone": self.timezone,
            "viewport": self.viewport.as_dict(),
            "capabilities": (
                self.capabilities.as_dict()
            ),
            "trusted": self.trusted,
            "active": self.active,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "record_sha256": (
                self.record_sha256
            ),
        }


@dataclass(frozen=True, slots=True)
class LayoutProfile:
    profile_id: str
    device_type: str
    orientation: str
    density: str
    navigation_mode: str
    panel_mode: str
    columns: int
    compact_header: bool
    touch_target_px: int
    fullscreen_recommended: bool

    def as_dict(self) -> dict[str, Any]:
        return {
            "profile_id": self.profile_id,
            "device_type": self.device_type,
            "orientation": self.orientation,
            "density": self.density,
            "navigation_mode": (
                self.navigation_mode
            ),
            "panel_mode": self.panel_mode,
            "columns": self.columns,
            "compact_header": (
                self.compact_header
            ),
            "touch_target_px": (
                self.touch_target_px
            ),
            "fullscreen_recommended": (
                self.fullscreen_recommended
            ),
        }


class MobileDeviceRuntime:
    def __init__(
        self,
        *,
        maximum_devices: int = 50,
    ) -> None:
        if maximum_devices <= 0:
            raise ValueError(
                "Azami cihaz sayısı pozitif olmalıdır."
            )

        self.maximum_devices = maximum_devices

        self._devices: dict[
            str,
            DeviceRegistration,
        ] = {}

        self._order: list[str] = []
        self._lock = RLock()

    def register(
        self,
        *,
        device_type: str,
        title: str,
        platform: str,
        user_agent: str,
        language: str,
        timezone: str,
        viewport: DeviceViewport,
        capabilities: DeviceCapabilities,
        device_id: str | None = None,
        trusted: bool = False,
    ) -> dict[str, Any]:
        normalized_type = (
            device_type.strip().lower()
        )

        if normalized_type not in DEVICE_TYPES:
            raise ValueError(
                "Geçersiz cihaz türü."
            )

        normalized_title = title.strip()
        normalized_platform = platform.strip()
        normalized_language = language.strip()
        normalized_timezone = timezone.strip()

        if not normalized_title:
            raise ValueError(
                "Cihaz başlığı boş olamaz."
            )

        if not normalized_platform:
            raise ValueError(
                "Cihaz platformu boş olamaz."
            )

        if not normalized_language:
            raise ValueError(
                "Cihaz dili boş olamaz."
            )

        if not normalized_timezone:
            raise ValueError(
                "Saat dilimi boş olamaz."
            )

        viewport.validate()
        capabilities.validate()

        resolved_id = (
            device_id.strip()
            if device_id
            else f"SYK-DEV-{uuid4().hex[:20]}"
        )

        if not resolved_id:
            raise ValueError(
                "Cihaz kimliği boş olamaz."
            )

        now = datetime.now(
            UTC
        ).isoformat()

        unsigned = {
            "device_id": resolved_id,
            "device_type": normalized_type,
            "title": normalized_title,
            "platform": normalized_platform,
            "user_agent": str(
                user_agent or ""
            ),
            "language": normalized_language,
            "timezone": normalized_timezone,
            "viewport": viewport.as_dict(),
            "capabilities": (
                capabilities.as_dict()
            ),
            "trusted": bool(trusted),
            "active": True,
            "created_at": now,
            "updated_at": now,
        }

        record_sha256 = self._hash(
            unsigned
        )

        registration = DeviceRegistration(
            device_id=resolved_id,
            device_type=normalized_type,
            title=normalized_title,
            platform=normalized_platform,
            user_agent=str(
                user_agent or ""
            ),
            language=normalized_language,
            timezone=normalized_timezone,
            viewport=viewport,
            capabilities=capabilities,
            trusted=bool(trusted),
            active=True,
            created_at=now,
            updated_at=now,
            record_sha256=record_sha256,
        )

        with self._lock:
            is_new = (
                resolved_id
                not in self._devices
            )

            self._devices[
                resolved_id
            ] = registration

            if is_new:
                self._order.append(
                    resolved_id
                )

            self._trim()

        return self._result(
            registration
        )

    def update_viewport(
        self,
        device_id: str,
        *,
        viewport: DeviceViewport,
    ) -> dict[str, Any]:
        viewport.validate()

        with self._lock:
            current = self._require(
                device_id
            )

            updated = self._replace(
                current,
                viewport=viewport,
                active=True,
            )

            self._devices[
                device_id
            ] = updated

        return self._result(updated)

    def update_capabilities(
        self,
        device_id: str,
        *,
        capabilities: DeviceCapabilities,
    ) -> dict[str, Any]:
        capabilities.validate()

        with self._lock:
            current = self._require(
                device_id
            )

            updated = self._replace(
                current,
                capabilities=capabilities,
                active=True,
            )

            self._devices[
                device_id
            ] = updated

        return self._result(updated)

    def trust(
        self,
        device_id: str,
        *,
        trusted: bool,
    ) -> dict[str, Any]:
        with self._lock:
            current = self._require(
                device_id
            )

            updated = self._replace(
                current,
                trusted=bool(trusted),
            )

            self._devices[
                device_id
            ] = updated

        return self._result(updated)

    def deactivate(
        self,
        device_id: str,
    ) -> dict[str, Any]:
        with self._lock:
            current = self._require(
                device_id
            )

            updated = self._replace(
                current,
                active=False,
            )

            self._devices[
                device_id
            ] = updated

        return self._result(updated)

    def get(
        self,
        device_id: str,
    ) -> dict[str, Any]:
        with self._lock:
            registration = self._require(
                device_id
            )

        return self._result(
            registration
        )

    def list(
        self,
        *,
        active_only: bool = False,
    ) -> list[dict[str, Any]]:
        with self._lock:
            registrations = [
                self._devices[
                    device_id
                ]
                for device_id
                in self._order
                if device_id
                in self._devices
            ]

        if active_only:
            registrations = [
                registration
                for registration
                in registrations
                if registration.active
            ]

        return [
            self._result(registration)
            for registration
            in registrations
        ]

    def layout_for(
        self,
        *,
        device_type: str,
        viewport: DeviceViewport,
        capabilities: DeviceCapabilities,
    ) -> LayoutProfile:
        viewport.validate()
        capabilities.validate()

        resolved_type = (
            device_type.strip().lower()
        )

        if resolved_type not in DEVICE_TYPES:
            resolved_type = self.detect_type(
                width=viewport.width,
                height=viewport.height,
                touch=capabilities.touch,
            )

        short_edge = min(
            viewport.width,
            viewport.height,
        )

        if (
            resolved_type == "phone"
            or short_edge < 600
        ):
            density = "compact"
            navigation_mode = (
                "bottom_navigation"
            )
            panel_mode = "single_panel"
            columns = 1
            compact_header = True
            touch_target = 48
            fullscreen = True

        elif (
            resolved_type == "tablet"
            or short_edge < 1000
        ):
            density = "comfortable"
            navigation_mode = (
                "side_navigation"
                if (
                    viewport.orientation
                    == "landscape"
                )
                else "bottom_navigation"
            )

            panel_mode = (
                "dual_panel"
                if (
                    viewport.orientation
                    == "landscape"
                )
                else "single_panel"
            )

            columns = (
                2
                if (
                    viewport.orientation
                    == "landscape"
                )
                else 1
            )

            compact_header = False
            touch_target = 48
            fullscreen = True

        else:
            density = "desktop"
            navigation_mode = (
                "side_navigation"
            )
            panel_mode = "multi_panel"
            columns = 3
            compact_header = False
            touch_target = (
                44
                if capabilities.touch
                else 36
            )
            fullscreen = False

        profile_id = (
            f"{resolved_type}-"
            f"{viewport.orientation}-"
            f"{density}"
        )

        return LayoutProfile(
            profile_id=profile_id,
            device_type=resolved_type,
            orientation=(
                viewport.orientation
            ),
            density=density,
            navigation_mode=(
                navigation_mode
            ),
            panel_mode=panel_mode,
            columns=columns,
            compact_header=(
                compact_header
            ),
            touch_target_px=(
                touch_target
            ),
            fullscreen_recommended=(
                fullscreen
            ),
        )

    @staticmethod
    def detect_type(
        *,
        width: int,
        height: int,
        touch: bool,
    ) -> str:
        if width <= 0 or height <= 0:
            raise ValueError(
                "Ekran ölçüsü pozitif olmalıdır."
            )

        short_edge = min(
            width,
            height,
        )

        long_edge = max(
            width,
            height,
        )

        if touch and short_edge < 600:
            return "phone"

        if (
            touch
            and short_edge < 1000
            and long_edge <= 1800
        ):
            return "tablet"

        return "desktop"

    def snapshot(
        self,
    ) -> dict[str, Any]:
        devices = self.list()

        unsigned = {
            "schema": (
                "sykasif-mobile-device-runtime/v1"
            ),
            "device_count": len(devices),
            "active_count": sum(
                1
                for item in devices
                if item["device"]["active"]
            ),
            "trusted_count": sum(
                1
                for item in devices
                if item["device"]["trusted"]
            ),
            "devices": devices,
            "status": "ready",
            "scope": (
                "browser_phone_tablet_runtime"
            ),
            "native_android_bridge_ready": False,
        }

        return {
            **unsigned,
            "snapshot_sha256": self._hash(
                unsigned
            ),
        }

    def _result(
        self,
        registration: DeviceRegistration,
    ) -> dict[str, Any]:
        layout = self.layout_for(
            device_type=(
                registration.device_type
            ),
            viewport=registration.viewport,
            capabilities=(
                registration.capabilities
            ),
        )

        return {
            "device": (
                registration.as_dict()
            ),
            "layout": layout.as_dict(),
        }

    def _replace(
        self,
        current: DeviceRegistration,
        *,
        viewport: (
            DeviceViewport | None
        ) = None,
        capabilities: (
            DeviceCapabilities | None
        ) = None,
        trusted: bool | None = None,
        active: bool | None = None,
    ) -> DeviceRegistration:
        updated_at = datetime.now(
            UTC
        ).isoformat()

        resolved_viewport = (
            viewport
            or current.viewport
        )

        resolved_capabilities = (
            capabilities
            or current.capabilities
        )

        resolved_trusted = (
            current.trusted
            if trusted is None
            else trusted
        )

        resolved_active = (
            current.active
            if active is None
            else active
        )

        unsigned = {
            "device_id": current.device_id,
            "device_type": (
                current.device_type
            ),
            "title": current.title,
            "platform": current.platform,
            "user_agent": (
                current.user_agent
            ),
            "language": current.language,
            "timezone": current.timezone,
            "viewport": (
                resolved_viewport.as_dict()
            ),
            "capabilities": (
                resolved_capabilities
                .as_dict()
            ),
            "trusted": resolved_trusted,
            "active": resolved_active,
            "created_at": current.created_at,
            "updated_at": updated_at,
        }

        return DeviceRegistration(
            device_id=current.device_id,
            device_type=current.device_type,
            title=current.title,
            platform=current.platform,
            user_agent=current.user_agent,
            language=current.language,
            timezone=current.timezone,
            viewport=resolved_viewport,
            capabilities=(
                resolved_capabilities
            ),
            trusted=resolved_trusted,
            active=resolved_active,
            created_at=current.created_at,
            updated_at=updated_at,
            record_sha256=self._hash(
                unsigned
            ),
        )

    def _require(
        self,
        device_id: str,
    ) -> DeviceRegistration:
        try:
            return self._devices[
                device_id
            ]
        except KeyError as error:
            raise KeyError(
                "Telefon veya tablet kaydı "
                "bulunamadı."
            ) from error

    def _trim(self) -> None:
        overflow = (
            len(self._order)
            - self.maximum_devices
        )

        if overflow <= 0:
            return

        expired = self._order[
            :overflow
        ]

        del self._order[
            :overflow
        ]

        for device_id in expired:
            self._devices.pop(
                device_id,
                None,
            )

    @staticmethod
    def _hash(
        payload: dict[str, Any],
    ) -> str:
        canonical = json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")

        return sha256(
            canonical
        ).hexdigest()


mobile_device_runtime = (
    MobileDeviceRuntime()
)