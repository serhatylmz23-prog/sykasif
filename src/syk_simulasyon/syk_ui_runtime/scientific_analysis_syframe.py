from __future__ import annotations

from typing import Any

from .scientific_device_analysis import (
    ScientificDeviceAnalysisEngine,
)
from .syframe_manager import SyFrameManager


class ScientificAnalysisSyFrameBridge:
    def __init__(
        self,
        *,
        analysis: ScientificDeviceAnalysisEngine,
        syframe: SyFrameManager,
    ) -> None:
        self._analysis = analysis
        self._syframe = syframe

    def apply(
        self,
        session_id: str,
    ) -> dict[str, Any]:
        verification = self._analysis.verify(
            session_id
        )

        if not verification["valid"]:
            raise ValueError(
                "Doğrulanmamış analiz SyFrame'e aktarılamaz."
            )

        result = self._analysis.get(
            session_id
        )

        decision = result["decision"]
        syframe_state = decision[
            "syframe_state"
        ]

        confidence = float(
            result["digital_confidence"]
        )

        mode = self._resolve_mode(
            result
        )

        state = self._syframe.update(
            state=syframe_state,
            mode=mode,
            visible=True,
            confidence=confidence,
        )

        return {
            "session_id": session_id,
            "analysis_sha256": result[
                "analysis_sha256"
            ],
            "analysis_verified": True,
            "decision": decision,
            "trend": result["trend"],
            "anomalies": result[
                "anomalies"
            ],
            "syframe": {
                "state": {
                    "id": state.id,
                    "title": state.title,
                    "color": state.color,
                },
                "mode": self._syframe.mode,
                "visible": self._syframe.visible,
                "confidence": (
                    self._syframe.confidence
                ),
            },
            "field_validation_required": (
                result[
                    "field_validation_required"
                ]
            ),
        }

    def snapshot(self) -> dict[str, Any]:
        state = self._syframe.state

        return {
            "state": {
                "id": state.id,
                "title": state.title,
                "color": state.color,
            },
            "mode": self._syframe.mode,
            "visible": self._syframe.visible,
            "confidence": self._syframe.confidence,
        }

    def _resolve_mode(
        self,
        result: dict[str, Any],
    ) -> str:
        anomaly_count = int(
            result["anomalies"].get(
                "count",
                0,
            )
        )

        if anomaly_count > 0:
            return "anomaly"

        decision_id = result[
            "decision"
        ]["id"]

        if decision_id == "digitally_verified":
            return "evidence"

        if decision_id in {
            "insufficient_data",
            "non_numeric_review",
            "analysis_required",
            "low_confidence",
        }:
            return "region"

        return "focus"