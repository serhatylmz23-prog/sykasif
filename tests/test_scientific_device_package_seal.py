import json

from syk_simulasyon.syk_ui_runtime.scientific_device_evidence import (
    DeviceEvidenceStore,
)
from syk_simulasyon.syk_ui_runtime.scientific_device_evidence_package import (
    DeviceEvidencePackageBuilder,
)
from syk_simulasyon.syk_ui_runtime.scientific_device_package_seal import (
    DeviceEvidencePackageSeal,
)


def test_cihaz_paket_raporu_ve_muhru(
    tmp_path,
):
    evidence = DeviceEvidenceStore(
        root=tmp_path / "evidence"
    )

    evidence.append(
        session_id="session-001",
        device_id="serial:COM7",
        module_id="gpr",
        payload={
            "live_value": 51.2,
            "confidence": 96.4,
        },
    )

    packages = DeviceEvidencePackageBuilder(
        evidence=evidence,
        root=tmp_path / "packages",
    )

    session = {
        "id": "session-001",
        "device_id": "serial:COM7",
        "module_id": "gpr",
        "state": "stopped",
        "sample_count": 1,
        "started_at": (
            "2026-08-03T05:00:00+00:00"
        ),
        "stopped_at": (
            "2026-08-03T05:10:00+00:00"
        ),
        "metadata": {},
    }

    packages.build(
        session=session
    )

    seals = DeviceEvidencePackageSeal(
        packages=packages,
        root=tmp_path / "seals",
    )

    result = seals.create(
        session=session
    )

    assert result["verification"]["valid"]

    assert len(
        result["package_sha256"]
    ) == 64

    assert len(
        result["report_sha256"]
    ) == 64

    assert len(
        result["seal_sha256"]
    ) == 64

    report_path = seals.report_path(
        "session-001"
    )

    seal_path = seals.seal_path(
        "session-001"
    )

    assert report_path.is_file()
    assert seal_path.is_file()

    report = json.loads(
        report_path.read_text(
            encoding="utf-8"
        )
    )

    assert report["session_id"] == (
        "session-001"
    )

    assert report["package_valid"]
    assert report["evidence_chain_valid"]

    seal = json.loads(
        seal_path.read_text(
            encoding="utf-8"
        )
    )

    assert (
        seal["maximum_digital_confidence"]
        == 99.9
    )

    verification = seals.verify(
        "session-001"
    )

    assert verification["valid"]


def test_paket_degisince_muhur_bozulur(
    tmp_path,
):
    evidence = DeviceEvidenceStore(
        root=tmp_path / "evidence"
    )

    evidence.append(
        session_id="session-002",
        device_id="tcp:gpr",
        module_id="gpr",
        payload={
            "live_value": 48.4,
        },
    )

    packages = DeviceEvidencePackageBuilder(
        evidence=evidence,
        root=tmp_path / "packages",
    )

    session = {
        "id": "session-002",
        "device_id": "tcp:gpr",
        "module_id": "gpr",
        "state": "stopped",
        "sample_count": 1,
    }

    packages.build(
        session=session
    )

    seals = DeviceEvidencePackageSeal(
        packages=packages,
        root=tmp_path / "seals",
    )

    seals.create(
        session=session
    )

    package_path = packages.package_path(
        "session-002"
    )

    with package_path.open("ab") as stream:
        stream.write(b"degisim")

    verification = seals.verify(
        "session-002"
    )

    assert not verification["valid"]
    assert verification["reason"] in {
        "package_verification_failed",
        "package_sha256_mismatch",
    }