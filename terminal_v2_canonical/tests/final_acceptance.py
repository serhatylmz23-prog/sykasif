from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from terminal_v2.app.main import app


ROOT = Path("terminal_v2")

client = TestClient(app)


def require_file(path: str) -> Path:
    target = ROOT / path

    if not target.is_file():
        raise RuntimeError(
            f"Zorunlu dosya bulunamadı: {target}"
        )

    if target.stat().st_size == 0:
        raise RuntimeError(
            f"Zorunlu dosya boş: {target}"
        )

    return target


def check_response(
    path: str,
    *,
    expected_type: str | None = None,
):
    response = client.get(path)

    if response.status_code != 200:
        raise RuntimeError(
            f"{path} HTTP {response.status_code}"
        )

    if (
        expected_type is not None
        and expected_type
        not in response.headers.get(
            "content-type",
            "",
        )
    ):
        raise RuntimeError(
            f"{path} içerik türü geçersiz."
        )

    return response


def main() -> int:
    required_files = [
        "app/main.py",
        "core/sse.py",
        "core/connection_registry.py",
        "core/power_guard.py",
        "run_terminal.py",
        "START_TERMINAL_V2.ps1",
        "templates/index.html",
        "static/css/main.css",
        "static/js/main.js",
        "static/js/live_runtime.js",
        "tests/runtime_smoke.py",
    ]

    for filename in required_files:
        require_file(filename)

    index = check_response(
        "/",
        expected_type="text/html",
    )

    health = check_response(
        "/health",
        expected_type="application/json",
    ).json()

    status = check_response(
        "/api/v2/status",
        expected_type="application/json",
    ).json()

    snapshot = check_response(
        "/api/v2/events/snapshot",
        expected_type="application/json",
    ).json()

    metrics = check_response(
        "/api/v2/events/metrics",
        expected_type="application/json",
    ).json()

    connections = check_response(
        "/api/v2/connections",
        expected_type="application/json",
    ).json()

    css = check_response(
        "/static/css/main.css",
    ).text

    main_js = check_response(
        "/static/js/main.js",
    ).text

    live_js = check_response(
        "/static/js/live_runtime.js",
    ).text

    checks = {
        "INDEX_SHELL": (
            "SyKaşif Terminal V2" in index.text
            and 'id="terminal-shell"' in index.text
        ),
        "RESPONSIVE_UI": (
            "@media (max-width: 820px)" in css
            and ".terminal-shell" in css
        ),
        "MAIN_JS": (
            "fetchStatus" in main_js
            and "EventSource" in main_js
        ),
        "LIVE_RUNTIME_JS": (
            "terminal.metrics" in live_js
            and "EventSource" in live_js
        ),
        "HEALTH": (
            health.get("status") == "ok"
            and health.get("terminal") == "v2"
        ),
        "STATUS": (
            status.get(
                "terminal",
                {},
            ).get("version") == "2.0.0"
            and status.get(
                "connection",
                {},
            ).get("transport") == "SSE"
        ),
        "SSE_SNAPSHOT": (
            snapshot.get("runtime") == "ONLINE"
            and snapshot.get("stream") == "ONLINE"
        ),
        "SSE_METRICS": (
            metrics.get("type") == "metrics"
            and "active_connections" in metrics
            and "active_tablet" in metrics
        ),
        "CONNECTION_REGISTRY": (
            "active_connections" in connections
            and isinstance(
                connections.get("clients"),
                list,
            )
        ),
    }

    failed = [
        name
        for name, passed in checks.items()
        if not passed
    ]

    print()
    print("=" * 56)
    print("TERMINAL V2 FINAL ACCEPTANCE")
    print("=" * 56)

    for name, passed in checks.items():
        print(
            f"{name:<26} = "
            f"{'PASS' if passed else 'FAIL'}"
        )

    if failed:
        raise RuntimeError(
            f"Final kabul başarısız: {failed}"
        )

    report = {
        "terminal": "SYK Terminal V2",
        "version": "2.0.0",
        "status": "DIGITAL_ACCEPTANCE_PASS",
        "checks": checks,
        "physical_tablet_test": "PENDING",
    }

    report_path = (
        ROOT
        / "release"
        / "FINAL_ACCEPTANCE_REPORT.json"
    )

    report_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    report_path.write_text(
        json.dumps(
            report,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    print()
    print(f"REPORT = {report_path}")
    print("FINAL_ACCEPTANCE_READY")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
