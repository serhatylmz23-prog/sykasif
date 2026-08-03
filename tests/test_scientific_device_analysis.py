import json

from syk_simulasyon.syk_ui_runtime.scientific_device_analysis import (
    ScientificDeviceAnalysisEngine,
)
from syk_simulasyon.syk_ui_runtime.scientific_device_evidence import (
    DeviceEvidenceStore,
)


class FakeSessions:
    def get(self, session_id: str):
        if session_id != "session-001":
            raise KeyError(session_id)

        return {
            "id": session_id,
            "device_id": "serial:COM7",
            "module_id": "gpr",
            "state": "stopped",
            "sample_count": 10,
        }


def test_cihaz_oturum_analizi(tmp_path):
    evidence = DeviceEvidenceStore(
        root=tmp_path / "evidence"
    )

    values = [
        50.0,
        50.2,
        50.4,
        50.6,
        50.8,
        51.0,
        51.2,
        51.4,
        51.6,
        51.8,
    ]

    for value in values:
        evidence.append(
            session_id="session-001",
            device_id="serial:COM7",
            module_id="gpr",
            payload={
                "live_value": value,
                "confidence": 96.0,
                "status": "verified",
                "source": "syk_probe_v2",
            },
        )

    engine = ScientificDeviceAnalysisEngine(
        sessions=FakeSessions(),
        evidence=evidence,
        root=tmp_path / "analysis",
    )

    result = engine.analyze("session-001")

    assert result["record_count"] == 10
    assert result["numeric_record_count"] == 10
    assert result["statistics"]["minimum"] == 50.0
    assert result["statistics"]["maximum"] == 51.8
    assert result["trend"]["direction"] == "increasing"
    assert result["anomalies"]["count"] == 0
    assert result["digital_confidence"] >= 90.0
    assert result["decision"]["id"] == "digitally_verified"
    assert result["decision"]["syframe_state"] == "verified"
    assert result["field_validation_required"]
    assert len(result["analysis_sha256"]) == 64
    assert engine.verify("session-001")["valid"]

    path = engine.analysis_path("session-001")
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["record_count"] = 999

    path.write_text(
        json.dumps(payload),
        encoding="utf-8",
    )

    verification = engine.verify("session-001")

    assert not verification["valid"]
    assert (
        verification["reason"]
        == "analysis_sha256_mismatch"
    )