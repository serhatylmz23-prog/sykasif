from pathlib import Path
import json


PWA = Path("terminal_v2/pwa")


def test_pwa_shell_files_exist():
    required = {
        "index.html",
        "pwa.css",
        "pwa.js",
        "service-worker.js",
        "manifest.webmanifest",
    }

    assert required.issubset(
        {
            path.name
            for path in PWA.iterdir()
        }
    )


def test_pwa_supports_iphone():
    text = (
        PWA / "index.html"
    ).read_text(
        encoding="utf-8-sig",
    )

    assert "apple-mobile-web-app-capable" in text
    assert "apple-touch-icon" in text
    assert "viewport-fit=cover" in text


def test_manifest_has_required_icons():
    manifest = json.loads(
        (
            PWA / "manifest.webmanifest"
        ).read_text(
            encoding="utf-8-sig",
        )
    )

    sizes = {
        icon["sizes"]
        for icon in manifest["icons"]
    }

    assert {
        "180x180",
        "192x192",
        "512x512",
    }.issubset(sizes)

    assert manifest["display"] == "standalone"
    assert manifest["lang"] == "tr"


def test_pwa_has_offline_shell():
    text = (
        PWA / "service-worker.js"
    ).read_text(
        encoding="utf-8-sig",
    )

    assert "CACHE_NAME" in text
    assert "APP_SHELL" in text
    assert 'self.addEventListener(\n    "fetch"' in text


def test_pwa_connects_to_shared_runtime():
    text = (
        PWA / "pwa.js"
    ).read_text(
        encoding="utf-8-sig",
    )

    assert "/api/v2/runtime-state" in text
    assert "/api/v2/modul-kartlari" in text
    assert "/api/v2/modul-kartlari/aktif" in text
