from __future__ import annotations

import hashlib
import json
import math
import statistics
from datetime import UTC, datetime
from pathlib import Path
from threading import RLock
from typing import Any

from .scientific_device_evidence import DeviceEvidenceStore
from .scientific_device_session import (
    ScientificDeviceSessionManager,
)


class ScientificDeviceAnalysisEngine:
    def __init__(
        self,
        *,
        sessions: ScientificDeviceSessionManager,
        evidence: DeviceEvidenceStore,
        root: Path | None = None,
    ) -> None:
        self._sessions = sessions
        self._evidence = evidence
        self._root = (
            root
            or Path("artifacts")
            / "device_session_analysis"
        )
        self._lock = RLock()
        self._root.mkdir(parents=True, exist_ok=True)

    def analysis_path(self, session_id: str) -> Path:
        safe_id = "".join(
            character
            for character in session_id
            if character.isalnum()
            or character in {"-", "_"}
        )

        if not safe_id:
            raise ValueError(
                "Geçerli oturum kimliği gerekli."
            )

        return self._root / (
            f"{safe_id}.analysis.json"
        )

    def analyze(
        self,
        session_id: str,
    ) -> dict[str, Any]:
        session = self._sessions.get(session_id)
        records = self._evidence.records(session_id)

        if not records:
            raise ValueError(
                "Analiz için kanıt kaydı bulunamadı."
            )

        evidence_verification = (
            self._evidence.verify(session_id)
        )

        if not evidence_verification["valid"]:
            raise ValueError(
                "Kanıt zinciri doğrulanamadı."
            )

        values: list[float] = []
        confidences: list[float] = []
        statuses: dict[str, int] = {}
        sources: dict[str, int] = {}

        for record in records:
            payload = record.get("payload", {})

            value = payload.get("live_value")

            if (
                isinstance(value, (int, float))
                and not isinstance(value, bool)
                and math.isfinite(float(value))
            ):
                values.append(float(value))

            confidence = payload.get("confidence")

            if (
                isinstance(confidence, (int, float))
                and not isinstance(confidence, bool)
                and math.isfinite(float(confidence))
            ):
                confidences.append(
                    max(
                        0.0,
                        min(99.9, float(confidence)),
                    )
                )

            status = str(
                payload.get("status", "unknown")
            )
            source = str(
                payload.get("source", "unknown")
            )

            statuses[status] = (
                statuses.get(status, 0) + 1
            )
            sources[source] = (
                sources.get(source, 0) + 1
            )

        statistics_result = self._statistics(values)
        trend_result = self._trend(values)
        anomaly_result = self._anomalies(values)

        digital_confidence = self._confidence(
            confidences=confidences,
            record_count=len(records),
        )

        decision = self._decision(
            record_count=len(records),
            numeric_count=len(values),
            confidence=digital_confidence,
            anomaly_count=anomaly_result["count"],
        )

        unsigned = {
            "schema": (
                "sykasif-device-session-analysis/v1"
            ),
            "session_id": session_id,
            "device_id": session.get("device_id"),
            "module_id": session.get("module_id"),
            "session_state": session.get("state"),
            "record_count": len(records),
            "numeric_record_count": len(values),
            "evidence_chain_valid": True,
            "evidence_last_hash": (
                evidence_verification.get("last_hash")
            ),
            "statistics": statistics_result,
            "trend": trend_result,
            "anomalies": anomaly_result,
            "status_counts": statuses,
            "source_counts": sources,
            "digital_confidence": digital_confidence,
            "decision": decision,
            "analysis_scope": "digital_records_only",
            "field_validation_required": True,
            "generated_at": datetime.now(
                UTC
            ).isoformat(),
        }

        result = {
            **unsigned,
            "analysis_sha256": self._dict_hash(
                unsigned
            ),
        }

        path = self.analysis_path(session_id)

        with self._lock:
            path.write_text(
                json.dumps(
                    result,
                    ensure_ascii=False,
                    sort_keys=True,
                    indent=2,
                ),
                encoding="utf-8",
            )

        return result

    def get(
        self,
        session_id: str,
    ) -> dict[str, Any]:
        path = self.analysis_path(session_id)

        if not path.is_file():
            raise KeyError(session_id)

        return json.loads(
            path.read_text(encoding="utf-8")
        )

    def verify(
        self,
        session_id: str,
    ) -> dict[str, Any]:
        try:
            result = self.get(session_id)
        except KeyError:
            return {
                "valid": False,
                "reason": "analysis_not_found",
            }

        expected = result.get("analysis_sha256")

        unsigned = {
            key: value
            for key, value in result.items()
            if key != "analysis_sha256"
        }

        actual = self._dict_hash(unsigned)

        if expected != actual:
            return {
                "valid": False,
                "reason": (
                    "analysis_sha256_mismatch"
                ),
            }

        evidence_verification = (
            self._evidence.verify(session_id)
        )

        if not evidence_verification["valid"]:
            return {
                "valid": False,
                "reason": (
                    "evidence_verification_failed"
                ),
            }

        if (
            result["evidence_last_hash"]
            != evidence_verification.get("last_hash")
        ):
            return {
                "valid": False,
                "reason": (
                    "evidence_reference_mismatch"
                ),
            }

        return {
            "valid": True,
            "session_id": session_id,
            "analysis_sha256": actual,
            "record_count": result["record_count"],
            "digital_confidence": (
                result["digital_confidence"]
            ),
            "decision": result["decision"],
        }

    def _statistics(
        self,
        values: list[float],
    ) -> dict[str, Any]:
        if not values:
            return {
                "available": False,
                "count": 0,
                "minimum": None,
                "maximum": None,
                "mean": None,
                "median": None,
                "standard_deviation": None,
            }

        deviation = (
            statistics.pstdev(values)
            if len(values) > 1
            else 0.0
        )

        return {
            "available": True,
            "count": len(values),
            "minimum": min(values),
            "maximum": max(values),
            "mean": statistics.fmean(values),
            "median": statistics.median(values),
            "standard_deviation": deviation,
        }

    def _trend(
        self,
        values: list[float],
    ) -> dict[str, Any]:
        if len(values) < 2:
            return {
                "available": False,
                "slope": 0.0,
                "direction": "insufficient_data",
            }

        x_values = list(range(len(values)))
        x_mean = statistics.fmean(x_values)
        y_mean = statistics.fmean(values)

        numerator = sum(
            (x - x_mean) * (y - y_mean)
            for x, y in zip(
                x_values,
                values,
                strict=True,
            )
        )

        denominator = sum(
            (x - x_mean) ** 2
            for x in x_values
        )

        slope = (
            numerator / denominator
            if denominator
            else 0.0
        )

        epsilon = max(
            1e-9,
            abs(y_mean) * 0.001,
        )

        if slope > epsilon:
            direction = "increasing"
        elif slope < -epsilon:
            direction = "decreasing"
        else:
            direction = "stable"

        return {
            "available": True,
            "slope": slope,
            "direction": direction,
        }

    def _anomalies(
        self,
        values: list[float],
    ) -> dict[str, Any]:
        if len(values) < 3:
            return {
                "available": False,
                "count": 0,
                "indexes": [],
                "threshold": 2.5,
            }

        mean = statistics.fmean(values)
        deviation = statistics.pstdev(values)

        if deviation == 0:
            return {
                "available": True,
                "count": 0,
                "indexes": [],
                "threshold": 2.5,
            }

        indexes = [
            index
            for index, value in enumerate(values)
            if abs(
                (value - mean) / deviation
            ) >= 2.5
        ]

        return {
            "available": True,
            "count": len(indexes),
            "indexes": indexes,
            "threshold": 2.5,
        }

    def _confidence(
        self,
        *,
        confidences: list[float],
        record_count: int,
    ) -> float:
        base = (
            statistics.fmean(confidences)
            if confidences
            else 50.0
        )

        completeness = min(
            1.0,
            record_count / 10.0,
        )

        result = (
            base * 0.85
            + completeness * 14.9
        )

        return round(
            max(0.0, min(99.9, result)),
            3,
        )

    def _decision(
        self,
        *,
        record_count: int,
        numeric_count: int,
        confidence: float,
        anomaly_count: int,
    ) -> dict[str, Any]:
        if record_count < 3:
            return {
                "id": "insufficient_data",
                "title": "Yetersiz Veri",
                "syframe_state": "review",
            }

        if numeric_count == 0:
            return {
                "id": "non_numeric_review",
                "title": "Sayısal Olmayan Veri",
                "syframe_state": "review",
            }

        if anomaly_count > 0:
            return {
                "id": "anomaly_detected",
                "title": "Anomali İncelenmeli",
                "syframe_state": "rare_anomaly",
            }

        if confidence >= 90.0:
            return {
                "id": "digitally_verified",
                "title": (
                    "Dijital Olarak Doğrulandı"
                ),
                "syframe_state": "verified",
            }

        if confidence >= 70.0:
            return {
                "id": "analysis_required",
                "title": "Analiz Ediliyor",
                "syframe_state": "analyzing",
            }

        return {
            "id": "low_confidence",
            "title": "Düşük Güven",
            "syframe_state": "low_confidence",
        }

    def _dict_hash(
        self,
        payload: dict[str, Any],
    ) -> str:
        canonical = json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")

        return hashlib.sha256(
            canonical
        ).hexdigest()