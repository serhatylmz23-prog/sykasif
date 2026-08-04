from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
import json
from threading import RLock
from typing import Any


PERMISSION_STATES = {
    "unknown",
    "default",
    "prompt",
    "granted",
    "denied",
    "unsupported",
}

SERVICE_STATES = {
    "idle",
    "starting",
    "active",
    "stopping",
    "error",
    "unsupported",
}

CONNECTION_STATES = {
    "online",
    "offline",
}

PAIRING_STATES = {
    "unpaired",
    "waiting",
    "paired",
    "expired",
    "revoked",
}


@dataclass(frozen=True, slots=True)
class MobileControlState:
    device_id: str
    device_type: str
    camera_state: str
    microphone_state: str
    location_state: str
    notification_permission: str
    connection_state: str
    pairing_state: str
    offline_queue_count: int
    fullscreen: bool
    wake_lock: bool
    last_error: str | None
    updated_at: str

    def validate(self) -> None:
        if not self.device_id:
            raise ValueError(
                "Cihaz kimliği boş olamaz."
            )

        if self.device_type not in {
            "phone",
            "tablet",
            "desktop",
            "browser",
        }:
            raise ValueError(
                "Geçersiz cihaz türü."
            )

        for state in (
            self.camera_state,
            self.microphone_state,
            self.location_state,
        ):
            if state not in SERVICE_STATES:
                raise ValueError(
                    "Geçersiz servis durumu."
                )

        if (
            self.notification_permission
            not in PERMISSION_STATES
        ):
            raise ValueError(
                "Geçersiz bildirim izin durumu."
            )

        if (
            self.connection_state
            not in CONNECTION_STATES
        ):
            raise ValueError(
                "Geçersiz bağlantı durumu."
            )

        if (
            self.pairing_state
            not in PAIRING_STATES
        ):
            raise ValueError(
                "Geçersiz eşleştirme durumu."
            )

        if self.offline_queue_count < 0:
            raise ValueError(
                "Çevrimdışı kuyruk sayısı "
                "negatif olamaz."
            )

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema": (
                "sykasif-mobile-control-state/v1"
            ),
            "device_id": self.device_id,
            "device_type": self.device_type,
            "camera_state": (
                self.camera_state
            ),
            "microphone_state": (
                self.microphone_state
            ),
            "location_state": (
                self.location_state
            ),
            "notification_permission": (
                self.notification_permission
            ),
            "connection_state": (
                self.connection_state
            ),
            "pairing_state": (
                self.pairing_state
            ),
            "offline_queue_count": (
                self.offline_queue_count
            ),
            "fullscreen": self.fullscreen,
            "wake_lock": self.wake_lock,
            "last_error": self.last_error,
            "updated_at": self.updated_at,
        }


class MobileControlRuntime:
    def __init__(
        self,
        *,
        maximum_devices: int = 100,
    ) -> None:
        if maximum_devices <= 0:
            raise ValueError(
                "Azami cihaz sayısı pozitif "
                "olmalıdır."
            )

        self.maximum_devices = (
            maximum_devices
        )

        self._states: dict[
            str,
            MobileControlState,
        ] = {}

        self._order: list[str] = []
        self._lock = RLock()

    def register(
        self,
        *,
        device_id: str,
        device_type: str,
    ) -> dict[str, Any]:
        normalized_id = (
            device_id.strip()
        )

        normalized_type = (
            device_type.strip().lower()
        )

        if not normalized_id:
            raise ValueError(
                "Cihaz kimliği boş olamaz."
            )

        state = MobileControlState(
            device_id=normalized_id,
            device_type=normalized_type,
            camera_state="idle",
            microphone_state="idle",
            location_state="idle",
            notification_permission=(
                "unknown"
            ),
            connection_state="online",
            pairing_state="unpaired",
            offline_queue_count=0,
            fullscreen=False,
            wake_lock=False,
            last_error=None,
            updated_at=self._now(),
        )

        state.validate()

        with self._lock:
            is_new = (
                normalized_id
                not in self._states
            )

            self._states[
                normalized_id
            ] = state

            if is_new:
                self._order.append(
                    normalized_id
                )

            self._trim()

        return self._serialize(state)

    def update(
        self,
        device_id: str,
        *,
        camera_state: str | None = None,
        microphone_state: str | None = None,
        location_state: str | None = None,
        notification_permission: (
            str | None
        ) = None,
        connection_state: str | None = None,
        pairing_state: str | None = None,
        offline_queue_count: int | None = None,
        fullscreen: bool | None = None,
        wake_lock: bool | None = None,
        last_error: str | None = None,
    ) -> dict[str, Any]:
        with self._lock:
            current = self._require(
                device_id
            )

            updated = MobileControlState(
                device_id=current.device_id,
                device_type=current.device_type,
                camera_state=(
                    current.camera_state
                    if camera_state is None
                    else camera_state.strip().lower()
                ),
                microphone_state=(
                    current.microphone_state
                    if microphone_state is None
                    else microphone_state
                        .strip()
                        .lower()
                ),
                location_state=(
                    current.location_state
                    if location_state is None
                    else location_state
                        .strip()
                        .lower()
                ),
                notification_permission=(
                    current
                    .notification_permission
                    if (
                        notification_permission
                        is None
                    )
                    else notification_permission
                        .strip()
                        .lower()
                ),
                connection_state=(
                    current.connection_state
                    if connection_state is None
                    else connection_state
                        .strip()
                        .lower()
                ),
                pairing_state=(
                    current.pairing_state
                    if pairing_state is None
                    else pairing_state
                        .strip()
                        .lower()
                ),
                offline_queue_count=(
                    current
                    .offline_queue_count
                    if (
                        offline_queue_count
                        is None
                    )
                    else int(
                        offline_queue_count
                    )
                ),
                fullscreen=(
                    current.fullscreen
                    if fullscreen is None
                    else bool(fullscreen)
                ),
                wake_lock=(
                    current.wake_lock
                    if wake_lock is None
                    else bool(wake_lock)
                ),
                last_error=(
                    last_error
                    if last_error
                    else None
                ),
                updated_at=self._now(),
            )

            updated.validate()

            self._states[
                device_id
            ] = updated

        return self._serialize(updated)

    def get(
        self,
        device_id: str,
    ) -> dict[str, Any]:
        with self._lock:
            state = self._require(
                device_id
            )

        return self._serialize(state)

    def list(
        self,
    ) -> list[dict[str, Any]]:
        with self._lock:
            states = [
                self._states[device_id]
                for device_id
                in self._order
                if device_id
                in self._states
            ]

        return [
            self._serialize(state)
            for state in states
        ]

    def reset(
        self,
        device_id: str,
    ) -> dict[str, Any]:
        with self._lock:
            current = self._require(
                device_id
            )

            reset_state = (
                MobileControlState(
                    device_id=(
                        current.device_id
                    ),
                    device_type=(
                        current.device_type
                    ),
                    camera_state="idle",
                    microphone_state="idle",
                    location_state="idle",
                    notification_permission=(
                        current
                        .notification_permission
                    ),
                    connection_state=(
                        current.connection_state
                    ),
                    pairing_state=(
                        current.pairing_state
                    ),
                    offline_queue_count=(
                        current
                        .offline_queue_count
                    ),
                    fullscreen=False,
                    wake_lock=False,
                    last_error=None,
                    updated_at=self._now(),
                )
            )

            self._states[
                device_id
            ] = reset_state

        return self._serialize(
            reset_state
        )

    def snapshot(
        self,
    ) -> dict[str, Any]:
        devices = self.list()

        unsigned = {
            "schema": (
                "sykasif-mobile-control-runtime/v1"
            ),
            "device_count": len(devices),
            "active_camera_count": sum(
                1
                for item in devices
                if item["state"][
                    "camera_state"
                ] == "active"
            ),
            "active_microphone_count": sum(
                1
                for item in devices
                if item["state"][
                    "microphone_state"
                ] == "active"
            ),
            "active_location_count": sum(
                1
                for item in devices
                if item["state"][
                    "location_state"
                ] == "active"
            ),
            "paired_device_count": sum(
                1
                for item in devices
                if item["state"][
                    "pairing_state"
                ] == "paired"
            ),
            "offline_device_count": sum(
                1
                for item in devices
                if item["state"][
                    "connection_state"
                ] == "offline"
            ),
            "devices": devices,
            "status": "ready",
        }

        return {
            **unsigned,
            "snapshot_sha256": (
                self._hash(unsigned)
            ),
        }

    def _serialize(
        self,
        state: MobileControlState,
    ) -> dict[str, Any]:
        payload = state.as_dict()

        return {
            "state": payload,
            "state_sha256": (
                self._hash(payload)
            ),
        }

    def _require(
        self,
        device_id: str,
    ) -> MobileControlState:
        try:
            return self._states[
                device_id
            ]

        except KeyError as error:
            raise KeyError(
                "Mobil kontrol cihazı "
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
            self._states.pop(
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

    @staticmethod
    def _now() -> str:
        return datetime.now(
            UTC
        ).isoformat()


mobile_control_runtime = (
    MobileControlRuntime()
)