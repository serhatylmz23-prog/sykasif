import json
import zipfile

from syk_simulasyon.syk_ui_runtime.scientific_device_evidence import (
    DeviceEvidenceStore,
)
from syk_simulasyon.syk_ui_runtime.scientific_device_evidence_package import (
    DeviceEvidencePackageBuilder,
)


def test_cihaz_kanit_teslim_paketi(
    tmp_path,
):
    evidence_root = (
        tmp_path / "evidence"
    )

    package_root = (
        tmp_path / "packages"
    )

    evidence = DeviceEvidenceStore(
        root=evidence_root
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

    evidence.append(
        session_id="session-001",
        device_id="serial:COM7",
        module_id="gpr",
        payload={
            "live_value": 52.1,
            "confidence": 97.0,
        },
    )

    builder = DeviceEvidencePackageBuilder(
        evidence=evidence,
        root=package_root,
    )

    result = builder.build(
        session={
            "id": "session-001",
            "device_id": "serial:COM7",
            "module_id": "gpr",
            "state": "stopped",
            "sample_count": 2,
            "started_at": (
                "2026-08-03T05:00:00+00:00"
            ),
            "stopped_at": (
                "2026-08-03T05:10:00+00:00"
            ),
            "metadata": {},
        }
    )

    assert result["verification"]["valid"]
    assert result["manifest"][
        "evidence_chain_valid"
    ]
    assert result["manifest"][
        "evidence_record_count"
    ] == 2

    assert len(
        result["package_sha256"]
    ) == 64

    package_path = builder.package_path(
        "session-001"
    )

    assert package_path.is_file()

    with zipfile.ZipFile(
        package_path,
        mode="r",
    ) as archive:
        names = set(archive.namelist())

        assert names == {
            "evidence.jsonl",
            "session.json",
            "manifest.json",
            "sha256sum.txt",
        }

        manifest = json.loads(
            archive.read(
                "manifest.json"
            ).decode("utf-8")
        )

        assert manifest[
            "session_id"
        ] == "session-001"

        assert manifest[
            "evidence_record_count"
        ] == 2

    verification = builder.verify(
        "session-001"
    )

    assert verification["valid"]
    assert verification[
        "record_count"
    ] == 2


def test_paket_bulunamazsa_dogrulanmaz(
    tmp_path,
):
    builder = DeviceEvidencePackageBuilder(
        evidence=DeviceEvidenceStore(
            root=tmp_path / "evidence"
        ),
        root=tmp_path / "packages",
    )

    result = builder.verify(
        "unknown-session"
    )

    assert not result["valid"]
    assert (
        result["reason"]
        == "package_not_found"
    )