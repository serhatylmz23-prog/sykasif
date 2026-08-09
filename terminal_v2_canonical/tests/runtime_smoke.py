from __future__ import annotations

import json
import socket
import subprocess
import sys
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
HOST = "127.0.0.1"
PORT = 18013
BASE_URL = f"http://{HOST}:{PORT}"


def port_is_open(
    host: str,
    port: int,
    timeout: float = 0.25,
) -> bool:
    with socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM,
    ) as sock:
        sock.settimeout(timeout)

        return sock.connect_ex(
            (host, port),
        ) == 0


def request_json(
    path: str,
    timeout: float = 2.0,
) -> dict:
    request = Request(
        f"{BASE_URL}{path}",
        headers={
            "Accept": "application/json",
            "Cache-Control": "no-cache",
        },
    )

    with urlopen(
        request,
        timeout=timeout,
    ) as response:
        if response.status != 200:
            raise RuntimeError(
                f"{path} HTTP {response.status}"
            )

        return json.loads(
            response.read().decode("utf-8")
        )


def request_text(
    path: str,
    timeout: float = 2.0,
) -> str:
    request = Request(
        f"{BASE_URL}{path}",
        headers={
            "Accept": "text/html",
            "Cache-Control": "no-cache",
        },
    )

    with urlopen(
        request,
        timeout=timeout,
    ) as response:
        if response.status != 200:
            raise RuntimeError(
                f"{path} HTTP {response.status}"
            )

        return response.read().decode("utf-8")


def wait_until_ready(
    process: subprocess.Popen,
    timeout: float = 15.0,
) -> None:
    deadline = time.monotonic() + timeout
    last_error: Exception | None = None

    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(
                f"Runtime erken kapandı: {process.returncode}"
            )

        try:
            health = request_json(
                "/health",
                timeout=0.75,
            )

            if health.get("status") == "ok":
                return
        except (
            URLError,
            TimeoutError,
            ConnectionError,
            OSError,
        ) as exc:
            last_error = exc

        time.sleep(0.25)

    raise RuntimeError(
        f"Runtime hazır olmadı: {last_error}"
    )


def stop_process(
    process: subprocess.Popen,
) -> None:
    if process.poll() is not None:
        return

    process.terminate()

    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)


def main() -> int:
    if port_is_open(HOST, PORT):
        raise RuntimeError(
            f"Smoke test portu kullanımda: {PORT}"
        )

    command = [
        sys.executable,
        "-m",
        "uvicorn",
        "terminal_v2.app.main:app",
        "--host",
        HOST,
        "--port",
        str(PORT),
        "--log-level",
        "warning",
    ]

    print()
    print("=" * 56)
    print("TERMINAL V2 RUNTIME SMOKE TEST")
    print("=" * 56)
    print(f"COMMAND = {' '.join(command)}")

    process = subprocess.Popen(
        command,
        cwd=ROOT.parent,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    try:
        wait_until_ready(process)

        index_html = request_text("/")
        health = request_json("/health")
        status = request_json("/api/v2/status")
        snapshot = request_json(
            "/api/v2/events/snapshot"
        )
        connections = request_json(
            "/api/v2/connections"
        )

        checks = {
            "INDEX_HTML": (
                "SyKaşif Terminal V2" in index_html
                and 'id="terminal-shell"' in index_html
            ),
            "HEALTH": (
                health.get("status") == "ok"
                and health.get("port") == 8013
            ),
            "STATUS": (
                status.get("terminal", {}).get("version")
                == "2.0.0"
                and status.get("connection", {}).get(
                    "transport"
                )
                == "SSE"
            ),
            "SSE_SNAPSHOT": (
                snapshot.get("terminal") == "v2"
                and snapshot.get("stream") == "ONLINE"
            ),
            "CONNECTION_REGISTRY": (
                "active_connections" in connections
                and "clients" in connections
            ),
        }

        failed = [
            name
            for name, passed in checks.items()
            if not passed
        ]

        for name, passed in checks.items():
            print(
                f"{name:<24} = "
                f"{'PASS' if passed else 'FAIL'}"
            )

        if failed:
            raise RuntimeError(
                f"Smoke test başarısız: {failed}"
            )

        print()
        print("RUNTIME_SMOKE_TEST_READY")

        return 0

    finally:
        stop_process(process)

        deadline = time.monotonic() + 8.0

        while time.monotonic() < deadline:
            if (
                process.poll() is not None
                and not port_is_open(HOST, PORT)
            ):
                break

            time.sleep(0.10)
        else:
            raise RuntimeError(
                "Smoke test runtime portu "
                "8 saniye i?inde kapanmad?."
            )


if __name__ == "__main__":
    raise SystemExit(main())
