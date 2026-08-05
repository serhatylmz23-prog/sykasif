from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from hashlib import sha256
from json import dumps
from threading import RLock
from typing import Any
from uuid import uuid4

from syk_core.sensor_gateway import (
    SensorEnvelope,
    SensorGateway,
    SensorHealth,
    sensor_gateway,
)


class SensorSessionState(StrEnum):
    READY = "ready"
    ACTIVE = "active"
    STOPPED = "stopped"
    ERROR = "error"


@dataclass(frozen=True, slots=True)
class SensorSessionTimelineEntry:
    sequence: int
    envelope_id: str
    source_id: str
    kind: str
    timestamp: str
    confidence: float
    latitude: float | None
    longitude: float | None
    payload: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class SensorGatewaySession:
    session_id: str
    name: str
    research_id: str | None
    workspace_id: str | None
    source_ids: list[str]
    state: SensorSessionState
    created_at: str
    updated_at: str
    started_at: str | None = None
    stopped_at: str | None = None
    envelope_ids: list[str] = field(
        default_factory=list
    )
    timeline: list[
        SensorSessionTimelineEntry
    ] = field(
        default_factory=list
    )
    gps_track: list[
        dict[str, Any]
    ] = field(
        default_factory=list
    )
    evidence_candidate_ids: list[
        str
    ] = field(
        default_factory=list
    )
    last_error: str | None = None

    def to_dict(
        self,
        source_health: dict[str, str],
    ) -> dict[str, Any]:
        source_counts: dict[str, int] = {}
        kind_counts: dict[str, int] = {}

        confidence_values: list[float] = []

        for entry in self.timeline:
            source_counts[
                entry.source_id
            ] = (
                source_counts.get(
                    entry.source_id,
                    0,
                )
                + 1
            )

            kind_counts[
                entry.kind
            ] = (
                kind_counts.get(
                    entry.kind,
                    0,
                )
                + 1
            )

            confidence_values.append(
                entry.confidence
            )

        average_confidence = (
            round(
                sum(confidence_values)
                / len(confidence_values),
                4,
            )
            if confidence_values
            else None
        )

        return {
            "session_id": self.session_id,
            "name": self.name,
            "research_id": self.research_id,
            "workspace_id": self.workspace_id,
            "source_ids": list(
                self.source_ids
            ),
            "state": self.state.value,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "started_at": self.started_at,
            "stopped_at": self.stopped_at,
            "envelope_count": len(
                self.envelope_ids
            ),
            "envelope_ids": list(
                self.envelope_ids
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
            "source_health": dict(
                source_health
            ),
            "summary": {
                "source_counts": source_counts,
                "kind_counts": kind_counts,
                "average_confidence": (
                    average_confidence
                ),
                "gps_point_count": len(
                    self.gps_track
                ),
                "cross_evidence_count": len(
                    self.evidence_candidate_ids
                ),
            },
            "last_error": self.last_error,
        }


class SensorGatewaySessionRuntime:
    def __init__(
        self,
        *,
        gateway: SensorGateway,
    ) -> None:
        self._gateway = gateway
        self._lock = RLock()

        self._sessions: dict[
            str,
            SensorGatewaySession,
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
        name: str,
        source_ids: list[str],
        research_id: str | None = None,
        workspace_id: str | None = None,
    ) -> SensorGatewaySession:
        clean_name = name.strip()

        if not clean_name:
            raise ValueError(
                "Sensör oturumu adı boş bırakılamaz."
            )

        clean_source_ids = list(
            dict.fromkeys(
                source_id.strip()
                for source_id in source_ids
                if source_id.strip()
            )
        )

        if not clean_source_ids:
            raise ValueError(
                "En az bir sensör kaynağı gereklidir."
            )

        missing = [
            source_id
            for source_id in clean_source_ids
            if (
                self._gateway.get_source(
                    source_id
                )
                is None
            )
        ]

        if missing:
            raise LookupError(
                "Sensör kaynakları bulunamadı: "
                + ", ".join(missing)
            )

        now = self._now()

        session = SensorGatewaySession(
            session_id=str(uuid4()),
            name=clean_name,
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
            source_ids=clean_source_ids,
            state=SensorSessionState.READY,
            created_at=now,
            updated_at=now,
        )

        with self._lock:
            self._sessions[
                session.session_id
            ] = session

        return session

    def get(
        self,
        session_id: str,
    ) -> SensorGatewaySession | None:
        with self._lock:
            return self._sessions.get(
                session_id
            )

    def list(
        self,
        *,
        research_id: str | None = None,
        workspace_id: str | None = None,
        state: SensorSessionState | None = None,
    ) -> list[SensorGatewaySession]:
        with self._lock:
            sessions = list(
                self._sessions.values()
            )

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
    ) -> SensorGatewaySession | None:
        session = self.get(session_id)

        if session is None:
            return None

        with self._lock:
            if (
                session.state
                == SensorSessionState.STOPPED
            ):
                raise RuntimeError(
                    "Durdurulmuş sensör oturumu "
                    "yeniden başlatılamaz."
                )

            if (
                session.state
                == SensorSessionState.ACTIVE
            ):
                return session

            now = self._now()

            session.state = (
                SensorSessionState.ACTIVE
            )
            session.started_at = now
            session.updated_at = now
            session.last_error = None

        return session

    def stop(
        self,
        session_id: str,
    ) -> SensorGatewaySession | None:
        session = self.get(session_id)

        if session is None:
            return None

        with self._lock:
            if (
                session.state
                == SensorSessionState.STOPPED
            ):
                return session

            if (
                session.state
                != SensorSessionState.ACTIVE
            ):
                raise RuntimeError(
                    "Yalnız etkin sensör oturumu "
                    "durdurulabilir."
                )

            now = self._now()

            session.state = (
                SensorSessionState.STOPPED
            )
            session.stopped_at = now
            session.updated_at = now

        return session

    def sync(
        self,
        session_id: str,
    ) -> SensorGatewaySession | None:
        session = self.get(session_id)

        if session is None:
            return None

        if (
            session.state
            != SensorSessionState.ACTIVE
        ):
            raise RuntimeError(
                "Sensör oturumu etkin değil."
            )

        envelopes = (
            self._gateway.list_envelopes(
                research_id=session.research_id,
                workspace_id=session.workspace_id,
            )
        )

        known_ids = set(
            session.envelope_ids
        )

        candidates = [
            envelope
            for envelope in envelopes
            if (
                envelope.envelope_id
                not in known_ids
                and envelope.source_id
                in session.source_ids
            )
        ]

        candidates.sort(
            key=lambda item: (
                item.timestamp,
                item.source_id,
                item.sequence,
            )
        )

        for envelope in candidates:
            self._append_envelope(
                session,
                envelope,
            )

        return session

    def _append_envelope(
        self,
        session: SensorGatewaySession,
        envelope: SensorEnvelope,
    ) -> None:
        payload = envelope.payload

        latitude = self._float_or_none(
            payload.get("latitude")
        )

        longitude = self._float_or_none(
            payload.get("longitude")
        )

        gps_payload = payload.get(
            "gps"
        )

        if isinstance(
            gps_payload,
            dict,
        ):
            latitude = self._float_or_none(
                gps_payload.get(
                    "latitude"
                )
            )

            longitude = self._float_or_none(
                gps_payload.get(
                    "longitude"
                )
            )

        entry = SensorSessionTimelineEntry(
            sequence=len(
                session.timeline
            ) + 1,
            envelope_id=envelope.envelope_id,
            source_id=envelope.source_id,
            kind=envelope.kind.value,
            timestamp=envelope.timestamp,
            confidence=envelope.confidence,
            latitude=latitude,
            longitude=longitude,
            payload=dict(payload),
        )

        cross_evidence_id = self._cross_evidence_id(
            session,
            envelope,
        )

        with self._lock:
            session.envelope_ids.append(
                envelope.envelope_id
            )

            session.timeline.append(
                entry
            )

            session.evidence_candidate_ids.append(
                cross_evidence_id
            )

            if (
                latitude is not None
                and longitude is not None
            ):
                session.gps_track.append(
                    {
                        "sequence": entry.sequence,
                        "timestamp": (
                            envelope.timestamp
                        ),
                        "source_id": (
                            envelope.source_id
                        ),
                        "latitude": latitude,
                        "longitude": longitude,
                    }
                )

            session.updated_at = self._now()

    def source_health(
        self,
        session: SensorGatewaySession,
    ) -> dict[str, str]:
        result: dict[str, str] = {}

        for source_id in session.source_ids:
            source = self._gateway.get_source(
                source_id
            )

            result[source_id] = (
                source.health.value
                if source is not None
                else SensorHealth.OFFLINE.value
            )

        return result

    def serialize(
        self,
        session: SensorGatewaySession,
    ) -> dict[str, Any]:
        return session.to_dict(
            self.source_health(
                session
            )
        )

    @staticmethod
    def _float_or_none(
        value: Any,
    ) -> float | None:
        if value is None:
            return None

        try:
            return float(value)
        except (
            TypeError,
            ValueError,
        ):
            return None

    @staticmethod
    def _cross_evidence_id(
        session: SensorGatewaySession,
        envelope: SensorEnvelope,
    ) -> str:
        payload = dumps(
            {
                "session_id": session.session_id,
                "envelope_id": envelope.envelope_id,
                "source_id": envelope.source_id,
                "research_id": session.research_id,
                "workspace_id": session.workspace_id,
            },
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )

        digest = sha256(
            payload.encode("utf-8")
        ).hexdigest()

        return (
            "cross-evidence-"
            + digest[:32]
        )


sensor_gateway_session_runtime = (
    SensorGatewaySessionRuntime(
        gateway=sensor_gateway
    )
)