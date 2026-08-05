from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from threading import RLock
from typing import Any
from uuid import uuid4

from syk_core.external_devices import (
    DeviceConnectionState,
    SonarTargetType,
)

from .external_device_runtime import (
    ExternalDeviceRuntime,
    SonarFrameRecord,
    external_device_runtime,
)


class SonarSessionState(StrEnum):
    READY = "ready"
    ACTIVE = "active"
    STOPPED = "stopped"
    ERROR = "error"


@dataclass(frozen=True, slots=True)
class SonarTimelineEntry:
    sequence: int
    frame_id: str
    timestamp: str
    depth_m: float
    water_temperature_c: float | None
    target_count: int
    fish_target_count: int
    bottom_classification: str
    latitude: float | None
    longitude: float | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class SonarSession:
    session_id: str
    device_id: str
    research_id: str | None
    workspace_id: str | None
    name: str
    state: SonarSessionState
    shallow_coast_profile: bool
    maximum_priority_depth_m: float
    started_at: str | None
    stopped_at: str | None
    created_at: str
    updated_at: str
    frame_record_ids: list[str] = field(
        default_factory=list
    )
    timeline: list[SonarTimelineEntry] = field(
        default_factory=list
    )
    gps_track: list[dict[str, Any]] = field(
        default_factory=list
    )
    evidence_candidate_ids: list[str] = field(
        default_factory=list
    )
    map_layer_state: dict[str, Any] = field(
        default_factory=dict
    )
    last_error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        fish_target_count = sum(
            entry.fish_target_count
            for entry in self.timeline
        )

        all_target_count = sum(
            entry.target_count
            for entry in self.timeline
        )

        depth_values = [
            entry.depth_m
            for entry in self.timeline
        ]

        minimum_depth_m = (
            min(depth_values)
            if depth_values
            else None
        )

        maximum_depth_m = (
            max(depth_values)
            if depth_values
            else None
        )

        average_depth_m = (
            round(
                sum(depth_values)
                / len(depth_values),
                3,
            )
            if depth_values
            else None
        )

        bottom_summary: dict[str, int] = {}

        for entry in self.timeline:
            bottom_summary[
                entry.bottom_classification
            ] = (
                bottom_summary.get(
                    entry.bottom_classification,
                    0,
                )
                + 1
            )

        return {
            "session_id": self.session_id,
            "device_id": self.device_id,
            "research_id": self.research_id,
            "workspace_id": self.workspace_id,
            "name": self.name,
            "state": self.state.value,
            "shallow_coast_profile": (
                self.shallow_coast_profile
            ),
            "maximum_priority_depth_m": (
                self.maximum_priority_depth_m
            ),
            "started_at": self.started_at,
            "stopped_at": self.stopped_at,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "frame_count": len(
                self.frame_record_ids
            ),
            "frame_record_ids": list(
                self.frame_record_ids
            ),
            "timeline": [
                entry.to_dict()
                for entry in self.timeline
            ],
            "gps_track": list(
                self.gps_track
            ),
            "evidence_candidate_ids": list(
                self.evidence_candidate_ids
            ),
            "map_layer_state": dict(
                self.map_layer_state
            ),
            "summary": {
                "target_count": all_target_count,
                "fish_target_count": (
                    fish_target_count
                ),
                "minimum_depth_m": minimum_depth_m,
                "maximum_depth_m": maximum_depth_m,
                "average_depth_m": average_depth_m,
                "bottom_classification": (
                    bottom_summary
                ),
            },
            "last_error": self.last_error,
        }


class SonarSessionRuntime:
    def __init__(
        self,
        *,
        device_runtime: ExternalDeviceRuntime,
    ) -> None:
        self._lock = RLock()
        self._device_runtime = device_runtime
        self._sessions: dict[
            str,
            SonarSession,
        ] = {}

    @staticmethod
    def _now() -> str:
        return datetime.now(
            UTC
        ).isoformat()

    def reset(self) -> None:
        with self._lock:
            self._sessions.clear()

    def create(
        self,
        *,
        device_id: str,
        name: str,
        research_id: str | None = None,
        workspace_id: str | None = None,
        maximum_priority_depth_m: float = 2.0,
    ) -> SonarSession:
        device = self._device_runtime.get_device(
            device_id
        )

        if device is None:
            raise LookupError(
                "Haricî cihaz bulunamadı."
            )

        clean_name = name.strip()

        if not clean_name:
            raise ValueError(
                "Sonar oturumu adı boş bırakılamaz."
            )

        if maximum_priority_depth_m <= 0:
            raise ValueError(
                "Öncelikli derinlik sıfırdan "
                "büyük olmalıdır."
            )

        now = self._now()

        session = SonarSession(
            session_id=str(uuid4()),
            device_id=device_id,
            research_id=(
                research_id.strip()
                if research_id
                else None
            ),
            workspace_id=(
                workspace_id.strip()
                if workspace_id
                else None
            ),
            name=clean_name,
            state=SonarSessionState.READY,
            shallow_coast_profile=True,
            maximum_priority_depth_m=(
                maximum_priority_depth_m
            ),
            started_at=None,
            stopped_at=None,
            created_at=now,
            updated_at=now,
            map_layer_state={
                "layer_key": "garmin-sonar-live",
                "visible": False,
                "frame_count": 0,
                "fish_target_count": 0,
                "last_depth_m": None,
                "last_position": None,
                "profile": "shallow-coast-0-2m",
            },
        )

        with self._lock:
            self._sessions[
                session.session_id
            ] = session

        return session

    def get(
        self,
        session_id: str,
    ) -> SonarSession | None:
        with self._lock:
            return self._sessions.get(
                session_id
            )

    def list(
        self,
        *,
        device_id: str | None = None,
        research_id: str | None = None,
        workspace_id: str | None = None,
        state: SonarSessionState | None = None,
    ) -> list[SonarSession]:
        with self._lock:
            sessions = list(
                self._sessions.values()
            )

        if device_id is not None:
            sessions = [
                session
                for session in sessions
                if session.device_id == device_id
            ]

        if research_id is not None:
            sessions = [
                session
                for session in sessions
                if (
                    session.research_id
                    == research_id
                )
            ]

        if workspace_id is not None:
            sessions = [
                session
                for session in sessions
                if (
                    session.workspace_id
                    == workspace_id
                )
            ]

        if state is not None:
            sessions = [
                session
                for session in sessions
                if session.state == state
            ]

        return sorted(
            sessions,
            key=lambda item: item.created_at,
        )

    def start(
        self,
        session_id: str,
    ) -> SonarSession | None:
        session = self.get(session_id)

        if session is None:
            return None

        device = self._device_runtime.get_device(
            session.device_id
        )

        if device is None:
            raise LookupError(
                "Oturuma bağlı cihaz bulunamadı."
            )

        if (
            device.connection_state
            != DeviceConnectionState.CONNECTED
        ):
            raise RuntimeError(
                "Sonar oturumu başlatılamadı; "
                "cihaz bağlı değil."
            )

        with self._lock:
            if (
                session.state
                == SonarSessionState.ACTIVE
            ):
                return session

            if (
                session.state
                == SonarSessionState.STOPPED
            ):
                raise RuntimeError(
                    "Durdurulmuş sonar oturumu "
                    "yeniden başlatılamaz."
                )

            now = self._now()

            session.state = (
                SonarSessionState.ACTIVE
            )
            session.started_at = now
            session.updated_at = now
            session.last_error = None

            session.map_layer_state[
                "visible"
            ] = True

            return session

    def stop(
        self,
        session_id: str,
    ) -> SonarSession | None:
        session = self.get(session_id)

        if session is None:
            return None

        with self._lock:
            if (
                session.state
                == SonarSessionState.STOPPED
            ):
                return session

            if (
                session.state
                != SonarSessionState.ACTIVE
            ):
                raise RuntimeError(
                    "Yalnız etkin sonar oturumu "
                    "durdurulabilir."
                )

            now = self._now()

            session.state = (
                SonarSessionState.STOPPED
            )
            session.stopped_at = now
            session.updated_at = now

            session.map_layer_state[
                "visible"
            ] = False

            return session

    def capture(
        self,
        session_id: str,
        *,
        frame_count: int = 1,
    ) -> SonarSession | None:
        session = self.get(session_id)

        if session is None:
            return None

        if frame_count < 1 or frame_count > 250:
            raise ValueError(
                "Kare sayısı 1 ile 250 "
                "arasında olmalıdır."
            )

        if (
            session.state
            != SonarSessionState.ACTIVE
        ):
            raise RuntimeError(
                "Sonar oturumu etkin değil."
            )

        for _ in range(frame_count):
            record = (
                self._device_runtime.read_frame(
                    session.device_id,
                    research_id=(
                        session.research_id
                    ),
                    workspace_id=(
                        session.workspace_id
                    ),
                )
            )

            if record is None:
                raise LookupError(
                    "Sonar karesi okunamadı."
                )

            self._append_record(
                session,
                record,
            )

        return session

    def _append_record(
        self,
        session: SonarSession,
        record: SonarFrameRecord,
    ) -> None:
        frame = record.frame

        fish_target_count = sum(
            1
            for target in frame.targets
            if (
                target.target_type
                == SonarTargetType.FISH
            )
        )

        gps_fix = frame.gps_fix

        latitude = (
            gps_fix.latitude
            if gps_fix is not None
            else None
        )

        longitude = (
            gps_fix.longitude
            if gps_fix is not None
            else None
        )

        entry = SonarTimelineEntry(
            sequence=(
                len(session.timeline) + 1
            ),
            frame_id=frame.frame_id,
            timestamp=frame.timestamp,
            depth_m=frame.depth_m,
            water_temperature_c=(
                frame.water_temperature_c
            ),
            target_count=len(frame.targets),
            fish_target_count=(
                fish_target_count
            ),
            bottom_classification=(
                frame.bottom_classification.value
            ),
            latitude=latitude,
            longitude=longitude,
        )

        with self._lock:
            session.frame_record_ids.append(
                record.record_id
            )

            session.timeline.append(entry)

            session.evidence_candidate_ids.append(
                record.evidence_candidate.candidate_id
            )

            if gps_fix is not None:
                session.gps_track.append(
                    {
                        "sequence": entry.sequence,
                        "timestamp": (
                            gps_fix.timestamp
                        ),
                        "latitude": (
                            gps_fix.latitude
                        ),
                        "longitude": (
                            gps_fix.longitude
                        ),
                        "altitude_m": (
                            gps_fix.altitude_m
                        ),
                        "accuracy_m": (
                            gps_fix.accuracy_m
                        ),
                        "quality": (
                            gps_fix.quality.value
                        ),
                    }
                )

            map_state = (
                session.map_layer_state
            )

            map_state["visible"] = True
            map_state["frame_count"] = len(
                session.timeline
            )

            map_state[
                "fish_target_count"
            ] = sum(
                item.fish_target_count
                for item in session.timeline
            )

            map_state[
                "last_depth_m"
            ] = frame.depth_m

            map_state[
                "last_position"
            ] = (
                {
                    "latitude": latitude,
                    "longitude": longitude,
                }
                if (
                    latitude is not None
                    and longitude is not None
                )
                else None
            )

            map_state[
                "within_priority_depth"
            ] = (
                frame.depth_m
                <= session.maximum_priority_depth_m
            )

            session.updated_at = self._now()


sonar_session_runtime = SonarSessionRuntime(
    device_runtime=external_device_runtime
)