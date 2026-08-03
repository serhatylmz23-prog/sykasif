import json

from syk_simulasyon.syk_ui_runtime.scientific_device_evidence import (
    DeviceEvidenceStore,
)


def test_cihaz_kanit_jsonl_ve_hash_zinciri(tmp_path):
    store = DeviceEvidenceStore(
        root=tmp_path
    )

    first = store.append(
        session_id="session-001",
        device_id="serial:COM7",
        module_id="gpr",
        payload={
            "live_value": 42.8,
            "confidence": 94.2,
        },
    )

    second = store.append(
        session_id="session-001",
        device_id="serial:COM7",
        module_id="gpr",
        payload={
            "live_value": 43.1,
            "confidence": 95.0,
        },
    )

    assert first["sequence"] == 1
    assert first["previous_hash"] is None
    assert len(first["sha256"]) == 64

    assert second["sequence"] == 2
    assert (
        second["previous_hash"]
        == first["sha256"]
    )

    path = store.session_path(
        "session-001"
    )

    assert path.is_file()

    lines = path.read_text(
        encoding="utf-8"
    ).splitlines()

    assert len(lines) == 2
    assert json.loads(lines[0])["sequence"] == 1
    assert json.loads(lines[1])["sequence"] == 2

    verification = store.verify(
        "session-001"
    )

    assert verification["valid"]
    assert verification["record_count"] == 2
    assert (
        verification["last_hash"]
        == second["sha256"]
    )