from __future__ import annotations

import hashlib
import json
import zipfile
from datetime import UTC, datetime
from pathlib import Path


ROOT = Path("terminal_v2")
SOURCE = ROOT / "generated"
RELEASE = ROOT / "release"

PACKAGE = RELEASE / "SYK_TERMINAL_V2_GENERATED.zip"
MANIFEST = RELEASE / "SYK_TERMINAL_V2_GENERATED.manifest.json"
SHA_FILE = RELEASE / "SYK_TERMINAL_V2_GENERATED.zip.sha256"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)

    return digest.hexdigest()


def collect_files() -> list[Path]:
    if not SOURCE.is_dir():
        raise FileNotFoundError(
            f"Üretim klasörü bulunamadı: {SOURCE}"
        )

    files = sorted(
        path
        for path in SOURCE.rglob("*")
        if path.is_file()
        and "__pycache__" not in path.parts
        and path.suffix != ".pyc"
    )

    if not files:
        raise RuntimeError(
            "Paketlenecek üretim dosyası bulunamadı."
        )

    return files


def create_package(files: list[Path]) -> None:
    RELEASE.mkdir(parents=True, exist_ok=True)

    if PACKAGE.exists():
        PACKAGE.unlink()

    with zipfile.ZipFile(
        PACKAGE,
        mode="w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=9,
    ) as archive:
        for path in files:
            archive.write(
                path,
                arcname=path.relative_to(ROOT).as_posix(),
            )


def create_manifest(files: list[Path]) -> dict:
    records = []

    for path in files:
        records.append(
            {
                "path": path.relative_to(ROOT).as_posix(),
                "size": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )

    manifest = {
        "package": PACKAGE.name,
        "created_utc": datetime.now(UTC).isoformat(),
        "source": SOURCE.relative_to(ROOT).as_posix(),
        "file_count": len(records),
        "files": records,
    }

    MANIFEST.write_text(
        json.dumps(
            manifest,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    return manifest


def verify_package(manifest: dict) -> str:
    if not PACKAGE.is_file() or PACKAGE.stat().st_size == 0:
        raise RuntimeError("ZIP paketi oluşturulamadı.")

    if not MANIFEST.is_file() or MANIFEST.stat().st_size == 0:
        raise RuntimeError("Manifest oluşturulamadı.")

    with zipfile.ZipFile(PACKAGE, "r") as archive:
        bad_file = archive.testzip()

        if bad_file is not None:
            raise RuntimeError(
                f"ZIP doğrulama hatası: {bad_file}"
            )

        archive_files = sorted(
            item.filename
            for item in archive.infolist()
            if not item.is_dir()
        )

    manifest_files = sorted(
        item["path"]
        for item in manifest["files"]
    )

    if archive_files != manifest_files:
        raise RuntimeError(
            "ZIP içeriği ile manifest eşleşmiyor."
        )

    package_sha = sha256_file(PACKAGE)

    SHA_FILE.write_text(
        f"{package_sha}  {PACKAGE.name}\n",
        encoding="ascii",
    )

    if len(package_sha) != 64:
        raise RuntimeError("SHA256 çıktısı geçersiz.")

    return package_sha


def main() -> int:
    files = collect_files()

    create_package(files)

    manifest = create_manifest(files)

    package_sha = verify_package(manifest)

    print()
    print("=" * 52)
    print("PACKAGE ENGINE")
    print("=" * 52)
    print(f"FILE_COUNT    = {manifest['file_count']}")
    print(f"PACKAGE       = {PACKAGE}")
    print(f"PACKAGE_SIZE  = {PACKAGE.stat().st_size}")
    print(f"MANIFEST      = {MANIFEST}")
    print(f"SHA256_FILE   = {SHA_FILE}")
    print(f"SHA256        = {package_sha}")
    print("PACKAGE_ENGINE_READY")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
