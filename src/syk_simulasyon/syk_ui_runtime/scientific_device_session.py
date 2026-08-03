from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from threading import RLock
from typing import Any
from uuid import uuid4

from .scientific_device_hub import ScientificDeviceHub


@dataclass
class DeviceSession:
    id: str
    device_id: str
    module_id: str | None
    state: str
    started_at: str
    stopped_at: str | None = None
    sample_count: int = 0
    metadata: dict[str, Any] | None = None

    def snapshot(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["metadata"] = dict(
            self.metadata or {}
        )
        return payload


class ScientificDeviceSessionManager:
    def __init__(
        self,
        device_hub: ScientificDeviceHub,
    ) -> None:
        self._device_hub = device_hub
        self._lock = RLock()
        self._sessions: dict[str, DeviceSession] = {}
        self._active_by_device: dict[str, str] = {}

    def inventory(self) -> list[dict[str, Any]]:
        with self._lock:
            return [
                session.snapshot()
                for session in self._sessions.values()
            ]

    def get(
        self,
        session_id: str,
    ) -> dict[str, Any]:
        with self._lock:
            if session_id not in self._sessions:
                raise KeyError(session_id)

            return self._sessions[
                session_id
            ].snapshot()

    def active_for_device(
        self,
        device_id: str,
    ) -> dict[str, Any] | None:
        with self._lock:
            session_id = self._active_by_device.get(
                device_id
            )

            if session_id is None:
                return None

            return self._sessions[
                session_id
            ].snapshot()

    def start(
        self,
        *,
        device_id: str,
        module_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        device = self._device_hub.get(device_id)

        if not device["connected"]:
            raise ValueError(
                "Kayıt başlatmak için cihaz bağlı olmalıdır."
            )

        with self._lock:
            if device_id in self._active_by_device:
                raise ValueError(
                    "Bu cihaz için aktif kayıt oturumu var."
                )

            resolved_module = (
                module_id
                or device.get("module_id")
            )

            session = DeviceSession(
                id=f"session-{uuid4().hex}",
                device_id=device_id,
                module_id=resolved_module,
                state="recording",
                started_at=datetime.now(
                    UTC
                ).isoformat(),
                metadata=dict(metadata or {}),
            )

            self._sessions[session.id] = session
            self._active_by_device[
                device_id
            ] = session.id

            return session.snapshot()

    def append_sample(
        self,
        session_id: str,
        *,
        count: int = 1,
    ) -> dict[str, Any]:
        if count <= 0:
            raise ValueError(
                "Örnek sayısı sıfırdan büyük olmalıdır."
            )

        with self._lock:
            if session_id not in self._sessions:
                raise KeyError(session_id)

            session = self._sessions[session_id]

            if session.state != "recording":
                raise ValueError(
                    "Durdurulmuş oturuma veri eklenemez."
                )

            session.sample_count += int(count)

            return session.snapshot()

    def stop(
        self,
        session_id: str,
    ) -> dict[str, Any]:
        with self._lock:
            if session_id not in self._sessions:
                raise KeyError(session_id)

            session = self._sessions[session_id]

            if session.state != "recording":
                raise ValueError(
                    "Kayıt oturumu zaten durdurulmuş."
                )

            session.state = "stopped"
            session.stopped_at = datetime.now(
                UTC
            ).isoformat()

            self._active_by_device.pop(
                session.device_id,
                None,
            )

            return session.snapshot()