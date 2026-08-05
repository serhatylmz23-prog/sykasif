from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path("terminal_v2")
BUILDER = ROOT / "builder"
RELEASE = ROOT / "release"

PIPELINE = BUILDER / "production_pipeline.py"
PACKAGE_ENGINE = BUILDER / "package_engine.py"

PACKAGE = RELEASE / "SYK_TERMINAL_V2_GENERATED.zip"
MANIFEST = RELEASE / "SYK_TERMINAL_V2_GENERATED.manifest.json"
SHA_FILE = RELEASE / "SYK_TERMINAL_V2_GENERATED.zip.sha256"

RELEASE_INDEX = RELEASE / "release-index.json"
LATEST_RELEASE = RELEASE / "LATEST_RELEASE.txt"
AUTOMATION_REPORT = RELEASE / "release-automation-report.json"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)

    return digest.hexdigest()


def run_step(name: str, script: Path) -> dict[str, Any]:
    if not script.is_file():
        raise FileNotFoundError(
            f"{name} betiği bulunamadı: {script}"
        )

    print()
    print(f"[RUN ] {name}")

    started = datetime.now(UTC)

    result = subprocess.run(
        [sys.executable, str(script)],
        cwd=Path.cwd(),
        text=True,
        check=False,
    )

    finished = datetime.now(UTC)

    if result.returncode != 0:
        raise RuntimeError(
            f"{name} başarısız. Çıkış kodu: {result.returncode}"
        )

    print(f"[PASS] {name}")

    return {
        "name": name,
        "script": script.as_posix(),
        "return_code": result.returncode,
        "started_utc": started.isoformat(),
        "finished_utc": finished.isoformat(),
        "duration_seconds": round(
            (finished - started).total_seconds(),
            6,
        ),
    }


def load_manifest() -> dict[str, Any]:
    if not MANIFEST.is_file():
        raise FileNotFoundError(
            f"Manifest bulunamadı: {MANIFEST}"
        )

    return json.loads(
        MANIFEST.read_text(encoding="utf-8")
    )


def read_recorded_sha() -> str:
    if not SHA_FILE.is_file():
        raise FileNotFoundError(
            f"SHA256 dosyası bulunamadı: {SHA_FILE}"
        )

    parts = SHA_FILE.read_text(
        encoding="ascii"
    ).strip().split()

    if not parts:
        raise RuntimeError("SHA256 dosyası boş.")

    value = parts[0].strip().lower()

    if len(value) != 64:
        raise RuntimeError(
            f"Geçersiz SHA256 uzunluğu: {len(value)}"
        )

    return value


def validate_release(
    manifest: dict[str, Any],
) -> dict[str, Any]:
    required = [
        PACKAGE,
        MANIFEST,
        SHA_FILE,
    ]

    missing = [
        str(path)
        for path in required
        if not path.is_file() or path.stat().st_size == 0
    ]

    if missing:
        raise RuntimeError(
            f"Eksik veya boş release dosyaları: {missing}"
        )

    actual_sha = sha256_file(PACKAGE)
    recorded_sha = read_recorded_sha()

    if actual_sha != recorded_sha:
        raise RuntimeError(
            "ZIP SHA256 doğrulaması başarısız."
        )

    manifest_package = manifest.get("package")

    if manifest_package != PACKAGE.name:
        raise RuntimeError(
            "Manifest paket adı ile ZIP adı eşleşmiyor."
        )

    file_count = manifest.get("file_count")

    if not isinstance(file_count, int) or file_count <= 0:
        raise RuntimeError(
            "Manifest file_count değeri geçersiz."
        )

    files = manifest.get("files")

    if not isinstance(files, list):
        raise RuntimeError(
            "Manifest files alanı geçersiz."
        )

    if len(files) != file_count:
        raise RuntimeError(
            "Manifest file_count ile files sayısı eşleşmiyor."
        )

    release_id = (
        datetime.now(UTC)
        .strftime("SYK_TERMINAL_V2_%Y%m%dT%H%M%SZ")
    )

    return {
        "release_id": release_id,
        "package": PACKAGE.name,
        "package_path": PACKAGE.as_posix(),
        "package_size": PACKAGE.stat().st_size,
        "package_sha256": actual_sha,
        "manifest": MANIFEST.name,
        "manifest_path": MANIFEST.as_posix(),
        "sha256_file": SHA_FILE.name,
        "sha256_path": SHA_FILE.as_posix(),
        "generated_file_count": file_count,
        "validated_utc": datetime.now(UTC).isoformat(),
        "status": "VALIDATED",
    }


def load_release_index() -> dict[str, Any]:
    if not RELEASE_INDEX.is_file():
        return {
            "schema": "syk-terminal-v2-release-index-v1",
            "release_count": 0,
            "latest_release_id": None,
            "releases": [],
        }

    data = json.loads(
        RELEASE_INDEX.read_text(encoding="utf-8")
    )

    if not isinstance(data.get("releases"), list):
        raise RuntimeError(
            "Release index releases alanı geçersiz."
        )

    return data


def update_release_index(
    release_record: dict[str, Any],
) -> dict[str, Any]:
    index = load_release_index()

    releases = [
        item
        for item in index["releases"]
        if item.get("package_sha256")
        != release_record["package_sha256"]
    ]

    releases.append(release_record)

    releases.sort(
        key=lambda item: item["validated_utc"]
    )

    index.update(
        {
            "schema": "syk-terminal-v2-release-index-v1",
            "updated_utc": datetime.now(UTC).isoformat(),
            "release_count": len(releases),
            "latest_release_id": release_record["release_id"],
            "releases": releases,
        }
    )

    RELEASE_INDEX.write_text(
        json.dumps(
            index,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    LATEST_RELEASE.write_text(
        "\n".join(
            [
                f"RELEASE_ID={release_record['release_id']}",
                f"PACKAGE={release_record['package']}",
                f"SHA256={release_record['package_sha256']}",
                f"STATUS={release_record['status']}",
                "",
            ]
        ),
        encoding="utf-8",
    )

    return index


def write_report(
    started: datetime,
    steps: list[dict[str, Any]],
    release_record: dict[str, Any],
    index: dict[str, Any],
) -> None:
    finished = datetime.now(UTC)

    report = {
        "schema": "syk-terminal-v2-release-automation-v1",
        "started_utc": started.isoformat(),
        "finished_utc": finished.isoformat(),
        "duration_seconds": round(
            (finished - started).total_seconds(),
            6,
        ),
        "status": "PASS",
        "steps": steps,
        "release": release_record,
        "release_index": {
            "path": RELEASE_INDEX.as_posix(),
            "release_count": index["release_count"],
            "latest_release_id": index["latest_release_id"],
        },
    }

    AUTOMATION_REPORT.write_text(
        json.dumps(
            report,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def main() -> int:
    RELEASE.mkdir(parents=True, exist_ok=True)

    started = datetime.now(UTC)
    steps: list[dict[str, Any]] = []

    print()
    print("=" * 56)
    print("SYK TERMINAL V2 RELEASE AUTOMATION")
    print("=" * 56)

    steps.append(
        run_step(
            "PRODUCTION_PIPELINE",
            PIPELINE,
        )
    )

    steps.append(
        run_step(
            "PACKAGE_ENGINE",
            PACKAGE_ENGINE,
        )
    )

    print()
    print("[RUN ] RELEASE_VALIDATOR")

    manifest = load_manifest()
    release_record = validate_release(manifest)

    print("[PASS] RELEASE_VALIDATOR")

    print()
    print("[RUN ] RELEASE_INDEX")

    index = update_release_index(release_record)

    print("[PASS] RELEASE_INDEX")

    write_report(
        started=started,
        steps=steps,
        release_record=release_record,
        index=index,
    )

    print()
    print("=" * 56)
    print("RELEASE_AUTOMATION_READY")
    print("=" * 56)
    print(f"RELEASE_ID     = {release_record['release_id']}")
    print(f"PACKAGE        = {release_record['package_path']}")
    print(f"PACKAGE_SIZE   = {release_record['package_size']}")
    print(f"SHA256         = {release_record['package_sha256']}")
    print(f"FILE_COUNT     = {release_record['generated_file_count']}")
    print(f"RELEASE_INDEX  = {RELEASE_INDEX}")
    print(f"LATEST_RELEASE = {LATEST_RELEASE}")
    print(f"REPORT         = {AUTOMATION_REPORT}")
    print("STATUS         = PASS")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
