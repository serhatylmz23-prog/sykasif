from __future__ import annotations

from typing import Any

from .scientific_device_evidence import DeviceEvidenceStore
from .scientific_device_session import (
    ScientificDeviceSessionManager,
)


class ScientificDeviceRecordingPipeline:
    def __init__(
        self,
        *,
        sessions: ScientificDeviceSessionManager,
        evidence: DeviceEvidenceStore,
    ) -> None:
        self._sessions = sessions
        self._evidence = evidence

    def ingest(
        self,
        *,
        device_id: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        active = self._sessions.active_for_device(
            device_id
        )

        if active is None:
            return {
                "recorded": False,
                "reason": "active_session_not_found",
                "device_id": device_id,
            }

        record = self._evidence.append(
            session_id=active["id"],
            device_id=device_id,
            module_id=active["module_id"],
            payload=payload,
        )

        session = self._sessions.append_sample(
            active["id"],
            count=1,
        )

        return {
            "recorded": True,
            "session": session,
            "evidence": record,
        }