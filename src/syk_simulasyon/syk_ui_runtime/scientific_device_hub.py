from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from threading import RLock
from typing import Any

from .scientific_device_manager import (
    ScientificDeviceManager,
)


@dataclass
class DeviceHubRecord:
    id: str
    title: str
    transport: str
    address: str
    connected: bool = False
    state: str = "discovered"
    module_id: str | None = None
    battery: float | None = None
    signal_quality: float | None = None
    firmware: str | None = None
    last_packet_at: str | None = None
    metadata: dict[str, Any] | None = None

    def snapshot(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["metadata"] = dict(
            self.metadata or {}
        )
        return payload


class ScientificDeviceHub:
    def __init__(
        self,
        manager: ScientificDeviceManager,
    ) -> None:
        self._manager = manager
        self._lock = RLock()
        self._devices: dict[
            str,
            DeviceHubRecord,
        ] = {}

    def transports(self) -> list[dict[str, Any]]:
        return self._manager.transports()

    def inventory(self) -> list[dict[str, Any]]:
        with self._lock:
            return [
                record.snapshot()
                for record in self._devices.values()
            ]

    async def refresh(
        self,
        *,
        ble_timeout: float = 5.0,
    ) -> dict[str, Any]:
        discovery = await self._manager.discover_all(
            ble_timeout=ble_timeout
        )

        with self._lock:
            for transport_id, devices in (
                discovery["devices"].items()
            ):
                for device in devices:
                    device_id = str(device["id"])

                    existing = self._devices.get(
                        device_id
                    )

                    if existing is None:
                        self._devices[device_id] = (
                            DeviceHubRecord(
                                id=device_id,
                                title=str(
                                    device.get(
                                        "title",
                                        device_id,
                                    )
                                ),
                                transport=transport_id,
                                address=str(
                                    device.get(
                                        "address",
                                        "",
                                    )
                                ),
                                connected=bool(
                                    device.get(
                                        "connected",
                                        False,
                                    )
                                ),
                                metadata=dict(
                                    device.get(
                                        "metadata",
                                        {},
                                    )
                                ),
                            )
                        )
                    else:
                        existing.title = str(
                            device.get(
                                "title",
                                existing.title,
                            )
                        )
                        existing.address = str(
                            device.get(
                                "address",
                                existing.address,
                            )
                        )
                        existing.metadata = dict(
                            device.get(
                                "metadata",
                                existing.metadata or {},
                            )
                        )

            return {
                "devices": self.inventory(),
                "transports": self.transports(),
                "errors": discovery["errors"],
            }

    def exists(self, device_id: str) -> bool:
        with self._lock:
            return device_id in self._devices

    def get(
        self,
        device_id: str,
    ) -> dict[str, Any]:
        with self._lock:
            if device_id not in self._devices:
                raise KeyError(device_id)

            return self._devices[
                device_id
            ].snapshot()

    def register_manual(
        self,
        *,
        device_id: str,
        title: str,
        transport: str,
        address: str,
        module_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if not device_id.strip():
            raise ValueError(
                "device_id boş olamaz."
            )

        if transport not in {
            "serial",
            "tcp",
            "ble",
        }:
            raise ValueError(
                f"Desteklenmeyen taşıma: {transport}"
            )

        with self._lock:
            if device_id in self._devices:
                raise ValueError(
                    f"Cihaz zaten kayıtlı: {device_id}"
                )

            record = DeviceHubRecord(
                id=device_id,
                title=title,
                transport=transport,
                address=address,
                module_id=module_id,
                metadata=dict(metadata or {}),
            )

            self._devices[device_id] = record

            return record.snapshot()

    def set_connection(
        self,
        device_id: str,
        *,
        connected: bool,
    ) -> dict[str, Any]:
        with self._lock:
            if device_id not in self._devices:
                raise KeyError(device_id)

            record = self._devices[device_id]
            record.connected = bool(connected)
            record.state = (
                "connected"
                if record.connected
                else "disconnected"
            )

            return record.snapshot()

    def update_telemetry(
        self,
        device_id: str,
        *,
        battery: float | None = None,
        signal_quality: float | None = None,
        firmware: str | None = None,
        module_id: str | None = None,
    ) -> dict[str, Any]:
        with self._lock:
            if device_id not in self._devices:
                raise KeyError(device_id)

            record = self._devices[device_id]

            if battery is not None:
                record.battery = max(
                    0.0,
                    min(100.0, float(battery)),
                )

            if signal_quality is not None:
                record.signal_quality = max(
                    0.0,
                    min(
                        100.0,
                        float(signal_quality),
                    ),
                )

            if firmware is not None:
                record.firmware = firmware

            if module_id is not None:
                record.module_id = module_id

            record.last_packet_at = (
                datetime.now(UTC).isoformat()
            )

            return record.snapshot()