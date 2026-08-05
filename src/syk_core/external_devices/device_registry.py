from __future__ import annotations

from threading import RLock
from typing import Any

from .device_model import ExternalDevice


class DeviceRegistry:
    def __init__(self) -> None:
        self._lock = RLock()
        self._devices: dict[
            str,
            ExternalDevice,
        ] = {}

    def reset(self) -> None:
        with self._lock:
            self._devices.clear()

    def register(
        self,
        device: ExternalDevice,
    ) -> None:
        device_id = (
            device.profile.identity.device_id
        )

        with self._lock:
            if device_id in self._devices:
                raise ValueError(
                    "Cihaz kimliği zaten kayıtlı: "
                    f"{device_id}"
                )

            self._devices[device_id] = device

    def replace(
        self,
        device: ExternalDevice,
    ) -> None:
        device_id = (
            device.profile.identity.device_id
        )

        with self._lock:
            self._devices[device_id] = device

    def unregister(
        self,
        device_id: str,
    ) -> ExternalDevice | None:
        with self._lock:
            return self._devices.pop(
                device_id,
                None,
            )

    def get(
        self,
        device_id: str,
    ) -> ExternalDevice | None:
        with self._lock:
            return self._devices.get(device_id)

    def list_devices(
        self,
    ) -> tuple[ExternalDevice, ...]:
        with self._lock:
            return tuple(
                self._devices.values()
            )

    def status_snapshot(
        self,
    ) -> dict[str, Any]:
        with self._lock:
            devices = tuple(
                self._devices.values()
            )

        return {
            "count": len(devices),
            "devices": [
                device.status_snapshot()
                for device in devices
            ],
        }


device_registry = DeviceRegistry()