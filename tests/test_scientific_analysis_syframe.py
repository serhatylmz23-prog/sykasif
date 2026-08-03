import pytest

from syk_simulasyon.syk_ui_runtime.scientific_analysis_syframe import (
    ScientificAnalysisSyFrameBridge,
)
from syk_simulasyon.syk_ui_runtime.syframe_manager import (
    SyFrameManager,
)


class FakeAnalysis:
    def __init__(
        self,
        result: dict,
        *,
        valid: bool = True,
    ) -> None:
        self.result = result
        self.valid = valid

    def verify(self, session_id: str):
        return {
            "valid": self.valid,
            "session_id": session_id,
        }

    def get(self, session_id: str):
        return {
            **self.result,
            "session_id": session_id,
        }


def test_dogrulanmis_analiz_syframee_aktarilir():
    analysis = FakeAnalysis(
        {
            "analysis_sha256": "a" * 64,
            "digital_confidence": 96.4,
            "decision": {
                "id": "digitally_verified",
                "title": (
                    "Dijital Olarak Doğrulandı"
                ),
                "syframe_state": "verified",
            },
            "trend": {
                "available": True,
                "direction": "increasing",
                "slope": 0.2,
            },
            "anomalies": {
                "available": True,
                "count": 0,
                "indexes": [],
            },
            "field_validation_required": True,
        }
    )

    syframe = SyFrameManager()

    bridge = ScientificAnalysisSyFrameBridge(
        analysis=analysis,
        syframe=syframe,
    )

    result = bridge.apply(
        "session-001"
    )

    assert result[
        "analysis_verified"
    ]

    assert result["syframe"][
        "state"
    ]["id"] == "verified"

    assert result["syframe"][
        "mode"
    ] == "evidence"

    assert result["syframe"][
        "confidence"
    ] == 96.4

    assert result[
        "field_validation_required"
    ]

    assert syframe.state.id == "verified"


def test_anomali_syframe_moduna_aktarilir():
    analysis = FakeAnalysis(
        {
            "analysis_sha256": "b" * 64,
            "digital_confidence": 91.0,
            "decision": {
                "id": "anomaly_detected",
                "title": "Anomali İncelenmeli",
                "syframe_state": "rare_anomaly",
            },
            "trend": {
                "available": True,
                "direction": "stable",
                "slope": 0.0,
            },
            "anomalies": {
                "available": True,
                "count": 2,
                "indexes": [3, 8],
            },
            "field_validation_required": True,
        }
    )

    syframe = SyFrameManager()

    result = ScientificAnalysisSyFrameBridge(
        analysis=analysis,
        syframe=syframe,
    ).apply("session-002")

    assert result["syframe"][
        "state"
    ]["id"] == "rare_anomaly"

    assert result["syframe"][
        "mode"
    ] == "anomaly"


def test_dogrulanmamis_analiz_aktarilmaz():
    bridge = ScientificAnalysisSyFrameBridge(
        analysis=FakeAnalysis(
            {},
            valid=False,
        ),
        syframe=SyFrameManager(),
    )

    with pytest.raises(ValueError):
        bridge.apply("session-003")