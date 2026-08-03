from syk_simulasyon.syk_ui_runtime.scientific_device_evidence import (
    DeviceEvidenceStore,
)
from syk_simulasyon.syk_ui_runtime.scientific_device_recording_pipeline import (
    ScientificDeviceRecordingPipeline,
)


class FakeSessions:
    def __init__(self):
        self.sample_count = 0
        self.active = {
            "serial:COM7": {
                "id": "session-001",
                "device_id": "serial:COM7",
                "module_id": "gpr",
                "state": "recording",
                "sample_count": 0,
            }
        }

    def active_for_device(
        self,
        device_id: str,
    ):
        return self.active.get(device_id)

    def append_sample(
        self,
        session_id: str,
        *,
        count: int,
    ):
        self.sample_count += count

        return {
            "id": session_id,
            "state": "recording",
            "sample_count": self.sample_count,
        }


def test_aktif_oturuma_otomatik_kanit_yazimi(
    tmp_path,
):
    sessions = FakeSessions()

    evidence = DeviceEvidenceStore(
        root=tmp_path
    )

    pipeline = ScientificDeviceRecordingPipeline(
        sessions=sessions,
        evidence=evidence,
    )

    first = pipeline.ingest(
        device_id="serial:COM7",
        payload={
            "transport": "serial",
            "live_value": 51.4,
            "confidence": 96.2,
            "status": "verified",
            "source": "syk_probe_v2",
        },
    )

    assert first["recorded"]
    assert first["session"]["sample_count"] == 1
    assert first["evidence"]["sequence"] == 1
    assert first["evidence"]["previous_hash"] is None

    second = pipeline.ingest(
        device_id="serial:COM7",
        payload={
            "transport": "serial",
            "live_value": 52.1,
            "confidence": 96.8,
            "status": "verified",
            "source": "syk_probe_v2",
        },
    )

    assert second["recorded"]
    assert second["session"]["sample_count"] == 2
    assert second["evidence"]["sequence"] == 2

    assert (
        second["evidence"]["previous_hash"]
        == first["evidence"]["sha256"]
    )

    verification = evidence.verify(
        "session-001"
    )

    assert verification["valid"]
    assert verification["record_count"] == 2


def test_aktif_oturum_yoksa_paket_yazilmaz(
    tmp_path,
):
    pipeline = ScientificDeviceRecordingPipeline(
        sessions=FakeSessions(),
        evidence=DeviceEvidenceStore(
            root=tmp_path
        ),
    )

    result = pipeline.ingest(
        device_id="tcp:unknown",
        payload={
            "live_value": 1,
        },
    )

    assert not result["recorded"]

    assert (
        result["reason"]
        == "active_session_not_found"
    )