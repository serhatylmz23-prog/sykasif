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
PORT = 8013
LOCAL_HOST = "127.0.0.1"
RUNTIME_HOST = "0.0.0.0"


def local_ipv4() -> str:
    sock = socket.socket(
        socket.AF_INET,
        socket.SOCK_DGRAM,
    )

    try:
        sock.connect(("8.8.8.8", 80))
        return str(sock.getsockname()[0])
    except OSError:
        return "127.0.0.1"
    finally:
        sock.close()


def port_is_open(
    host: str,
    port: int,
    timeout: float = 0.40,
) -> bool:
    with socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM,
    ) as sock:
        sock.settimeout(timeout)

        return sock.connect_ex(
            (host, port),
        ) == 0


def get_json(
    url: str,
    timeout: float = 5.0,
) -> dict:
    request = Request(
        url,
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
                f"{url} HTTP {response.status}"
            )

        return json.loads(
            response.read().decode("utf-8")
        )


def post_json(
    url: str,
    payload: dict | None = None,
    timeout: float = 5.0,
) -> dict:
    body = (
        json.dumps(payload).encode("utf-8")
        if payload is not None
        else b""
    )

    request = Request(
        url,
        data=body,
        method="POST",
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Cache-Control": "no-cache",
        },
    )

    with urlopen(
        request,
        timeout=timeout,
    ) as response:
        if response.status != 200:
            raise RuntimeError(
                f"{url} HTTP {response.status}"
            )

        return json.loads(
            response.read().decode("utf-8")
        )


def runtime_is_compatible() -> bool:
    try:
        health = get_json(
            f"http://{LOCAL_HOST}:{PORT}/health",
            timeout=2.0,
        )

        status = get_json(
            f"http://{LOCAL_HOST}:{PORT}/api/v2/status",
            timeout=2.0,
        )

        return (
            health.get("status") == "ok"
            and health.get("terminal") == "v2"
            and status.get("terminal", {}).get("version")
            == "2.0.0"
        )
    except (
        URLError,
        TimeoutError,
        ConnectionError,
        OSError,
        ValueError,
        RuntimeError,
    ):
        return False


def start_runtime() -> subprocess.Popen:
    command = [
        sys.executable,
        "-m",
        "uvicorn",
        "terminal_v2.app.main:app",
        "--host",
        RUNTIME_HOST,
        "--port",
        str(PORT),
        "--log-level",
        "warning",
    ]

    return subprocess.Popen(
        command,
        cwd=ROOT.parent,
    )


def wait_runtime(
    process: subprocess.Popen | None,
    timeout: float = 15.0,
) -> None:
    deadline = time.monotonic() + timeout
    last_error: Exception | None = None

    while time.monotonic() < deadline:
        if (
            process is not None
            and process.poll() is not None
        ):
            raise RuntimeError(
                f"Runtime kapandı: {process.returncode}"
            )

        try:
            if runtime_is_compatible():
                return
        except Exception as exc:
            last_error = exc

        time.sleep(0.25)

    raise RuntimeError(
        f"Terminal V2 çalışma süresinde başlamadı: {last_error}"
    )


def stop_owned_runtime(
    process: subprocess.Popen | None,
) -> None:
    if process is None:
        return

    if process.poll() is not None:
        return

    process.terminate()

    try:
        process.wait(timeout=8)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)

    deadline = time.monotonic() + 8.0

    while time.monotonic() < deadline:
        if not port_is_open(LOCAL_HOST, PORT):
            return

        time.sleep(0.10)

    raise RuntimeError(
        "Başlatılan runtime portu kapanmadı."
    )


def main() -> int:
    lan_ip = local_ipv4()

    runtime_process: subprocess.Popen | None = None
    runtime_owned = False

    print()
    print("=" * 68)
    print("SYK TERMINAL V2 TABLET / LAN DOGRULAMA")
    print("=" * 68)

    if port_is_open(LOCAL_HOST, PORT):
        if not runtime_is_compatible():
            raise RuntimeError(
                f"{PORT} portu açık ancak Terminal V2 çalışmıyor."
            )

        print()
        print("RUNTIME        : MEVCUT CALISAN RUNTIME KULLANILACAK")
        print("PORT           : 8013")
        print("RUNTIME SAHIBI : HARICI")
    else:
        runtime_process = start_runtime()
        runtime_owned = True

        wait_runtime(runtime_process)

        print()
        print("RUNTIME        : YENI RUNTIME BASLATILDI")
        print("PORT           : 8013")
        print("RUNTIME SAHIBI : DOGRULAMA BETIGI")

    try:
        session = post_json(
            f"http://{LOCAL_HOST}:{PORT}"
            "/api/v2/tablet-validation/session"
        )

        token = session["token"]

        tablet_url = (
            f"http://{lan_ip}:{PORT}"
            f"/tablet-validation/{token}"
        )

        status_url = (
            f"http://{LOCAL_HOST}:{PORT}"
            f"/api/v2/tablet-validation/session/{token}"
        )

        print()
        print("TABLET IP      : 192.168.1.101")
        print("BILGISAYAR IP  :", lan_ip)
        print()
        print("TABLET TARAYICISINDA ACIN:")
        print()
        print(tablet_url)
        print()
        print("TABLETTE 'TABLETI DOGRULA' DUGMESINE BASIN.")
        print()
        print("BEKLENIYOR...")

        deadline = time.monotonic() + 300

        while time.monotonic() < deadline:
            status = get_json(status_url)

            if status.get("digital_checks_passed"):
                report_path = (
                    ROOT
                    / "release"
                    / "TABLET_LAN_VALIDATION_REPORT.json"
                )

                report_path.parent.mkdir(
                    parents=True,
                    exist_ok=True,
                )

                report = {
                    "status": (
                        "TABLET_LAN_DIGITAL_VALIDATION_PASS"
                    ),
                    "runtime_reused": not runtime_owned,
                    "runtime_port": PORT,
                    "computer_lan_ip": lan_ip,
                    "validation": status,
                }

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
                print("=" * 68)
                print("TABLET_LAN_DIGITAL_VALIDATION_PASS")
                print("=" * 68)
                print(
                    f"CLIENT         : {status['client_host']}"
                )
                print(
                    "VIEWPORT       : "
                    f"{status['viewport_width']}x"
                    f"{status['viewport_height']}"
                )
                print(
                    f"TOUCH          : {status['touch_supported']}"
                )
                print(
                    f"EVENT SOURCE   : "
                    f"{status['event_source_supported']}"
                )
                print(
                    f"SSE            : {status['sse_connected']}"
                )
                print(
                    f"RUNTIME REUSED : {not runtime_owned}"
                )
                print(
                    f"REPORT         : {report_path}"
                )

                return 0

            time.sleep(1)

        raise RuntimeError(
            "Tablet doğrulaması 5 dakika içinde tamamlanmadı."
        )
    finally:
        if runtime_owned:
            stop_owned_runtime(runtime_process)
        else:
            print()
            print(
                "MEVCUT RUNTIME ACIK BIRAKILDI."
            )


if __name__ == "__main__":
    raise SystemExit(main())
