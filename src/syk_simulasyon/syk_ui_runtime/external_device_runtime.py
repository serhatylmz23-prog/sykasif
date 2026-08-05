from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from threading import RLock
from typing import Any
from uuid import uuid4

from syk_core.external_devices import (
    DeviceConnectionState,
    GarminAdapter,
    GarminMockConfiguration,
    SonarFrame,
)


@dataclass(frozen=True, slots=True)
class SonarEvidenceCandidate:
    candidate_id: str
    device_id: str
    frame_id: str
    research_id: str | None
    workspace_id: str | None
    evidence_status: str
    confidence: float
    created_at: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class SonarFrameRecord:
    record_id: str
    device_id: str
    research_id: str | None
    workspace_id: str | None
    frame: SonarFrame
    evidence_candidate: SonarEvidenceCandidate
    created_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "record_id": self.record_id,
            "device_id": self.device_id,
            "research_id": self.research_id,
            "workspace_id": self.workspace_id,
            "frame": self.frame.to_dict(),
            "evidence_candidate": (
                self.evidence_candidate.to_dict()
            ),
            "created_at": self.created_at,
        }


class ExternalDeviceRuntime:
    def __init__(self) -> None:
        self._lock = RLock()
        self._devices: dict[str, GarminAdapter] = {}
        self._records: list[SonarFrameRecord] = []

    @staticmethod
    def _now() -> str:
        return datetime.now(
            UTC
        ).isoformat()

    def reset(self) -> None:
        with self._lock:
            for device in self._devices.values():
                if (
                    device.connection_state
                    == DeviceConnectionState.CONNECTED
                ):
                    device.disconnect()

            self._devices.clear()
            self._records.clear()

    def register_mock_garmin(
        self,
        *,
        latitude: float = 38.7123,
        longitude: float = 38.4521,
        minimum_depth_m: float = 0.35,
        maximum_depth_m: float = 2.0,
        water_temperature_c: float = 19.5,
        seed: int = 1903,
    ) -> GarminAdapter:
        adapter = GarminAdapter(
            GarminMockConfiguration(
                latitude=latitude,
                longitude=longitude,
                minimum_depth_m=minimum_depth_m,
                maximum_depth_m=maximum_depth_m,
                water_temperature_c=(
                    water_temperature_c
                ),
                seed=seed,
            )
        )

        device_id = (
            adapter.profile.identity.device_id
        )

        with self._lock:
            self._devices[device_id] = adapter

        return adapter

    def get_device(
        self,
        device_id: str,
    ) -> GarminAdapter | None:
        with self._lock:
            return self._devices.get(device_id)

    def list_devices(self) -> list[dict[str, Any]]:
        with self._lock:
            devices = tuple(
                self._devices.values()
            )

        return [
            device.status_snapshot()
            for device in devices
        ]

    def connect(
        self,
        device_id: str,
    ) -> GarminAdapter | None:
        device = self.get_device(device_id)

        if device is None:
            return None

        device.connect()

        return device

    def disconnect(
        self,
        device_id: str,
    ) -> GarminAdapter | None:
        device = self.get_device(device_id)

        if device is None:
            return None

        device.disconnect()

        return device

    def read_frame(
        self,
        device_id: str,
        *,
        research_id: str | None = None,
        workspace_id: str | None = None,
    ) -> SonarFrameRecord | None:
        device = self.get_device(device_id)

        if device is None:
            return None

        frame = device.read_frame()

        target_confidence = max(
            (
                target.confidence
                for target in frame.targets
            ),
            default=0.0,
        )

        evidence_confidence = round(
            max(
                frame.bottom_confidence,
                target_confidence,
            ),
            3,
        )

        candidate = SonarEvidenceCandidate(
            candidate_id=str(uuid4()),
            device_id=device_id,
            frame_id=frame.frame_id,
            research_id=research_id,
            workspace_id=workspace_id,
            evidence_status="candidate-unverified",
            confidence=evidence_confidence,
            created_at=self._now(),
        )

        record = SonarFrameRecord(
            record_id=str(uuid4()),
            device_id=device_id,
            research_id=research_id,
            workspace_id=workspace_id,
            frame=frame,
            evidence_candidate=candidate,
            created_at=self._now(),
        )

        with self._lock:
            self._records.append(record)

        return record

    def list_records(
        self,
        *,
        device_id: str | None = None,
        research_id: str | None = None,
        workspace_id: str | None = None,
    ) -> list[SonarFrameRecord]:
        with self._lock:
            records = list(self._records)

        if device_id is not None:
            records = [
                record
                for record in records
                if record.device_id == device_id
            ]

        if research_id is not None:
            records = [
                record
                for record in records
                if record.research_id == research_id
            ]

        if workspace_id is not None:
            records = [
                record
                for record in records
                if record.workspace_id == workspace_id
            ]

        return records


external_device_runtime = ExternalDeviceRuntime()