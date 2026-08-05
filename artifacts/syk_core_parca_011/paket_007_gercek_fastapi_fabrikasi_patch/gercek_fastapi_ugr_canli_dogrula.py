from __future__ import annotations

import argparse
import json
import os
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Sequence

import httpx


HOST = "127.0.0.1"
PORT = 8013
BASE_URL = f"http://{HOST}:{PORT}"


def port_open(
    host: str,
    port: int,
    *,
    timeout: float = 0.25,
) -> bool:
    with socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM,
    ) as connection:
        connection.settimeout(
            timeout
        )

        return (
            connection.connect_ex(
                (
                    host,
                    port,
                )
            )
            == 0
        )


def wait_for_port(
    process: subprocess.Popen[str],
    *,
    timeout: float = 15.0,
) -> None:
    deadline = (
        time.monotonic()
        + timeout
    )

    while (
        time.monotonic()
        < deadline
    ):
        if process.poll() is not None:
            raise RuntimeError(
                "Runtime port açılmadan kapandı. "
                f"CIKIS_KODU={process.returncode}"
            )

        if port_open(
            HOST,
            PORT,
        ):
            return

        time.sleep(
            0.10
        )

    raise TimeoutError(
        "Runtime 8013 portu zamanında açılmadı."
    )


def stop_process(
    process: subprocess.Popen[str],
) -> None:
    if process.poll() is not None:
        return

    try:
        if os.name == "nt":
            process.send_signal(
                signal.CTRL_BREAK_EVENT
            )
        else:
            process.send_signal(
                signal.SIGINT
            )

        process.wait(
            timeout=5.0
        )

    except Exception:
        if process.poll() is None:
            process.terminate()

        try:
            process.wait(
                timeout=3.0
            )
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(
                timeout=3.0
            )


def request_result(
    client: httpx.Client,
    method: str,
    path: str,
    **kwargs: Any,
) -> dict[str, Any]:
    start = time.perf_counter()

    response = client.request(
        method,
        path,
        **kwargs,
    )

    duration_ms = (
        time.perf_counter()
        - start
    ) * 1000.0

    content_type = response.headers.get(
        "content-type",
        "",
    )

    parsed_json = None

    if (
        "application/json"
        in content_type
    ):
        try:
            parsed_json = response.json()
        except Exception:
            parsed_json = None

    return {
        "method": method,
        "path": path,
        "status_code": response.status_code,
        "content_type": content_type,
        "duration_ms": duration_ms,
        "text_first_500": response.text[
            :500
        ],
        "json": parsed_json,
    }


def parser_create() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--patch-report",
        required=True,
    )

    parser.add_argument(
        "--output-json",
        required=True,
    )

    parser.add_argument(
        "--output-text",
        required=True,
    )

    parser.add_argument(
        "--stdout",
        required=True,
    )

    parser.add_argument(
        "--stderr",
        required=True,
    )

    return parser


def main(
    argv: Sequence[str] | None = None,
) -> int:
    arguments = parser_create().parse_args(
        argv
    )

    patch_report = json.loads(
        Path(
            arguments.patch_report
        ).read_text(
            encoding="utf-8-sig"
        )
    )

    app_import = patch_report[
        "patch"
    ][
        "import_nesnesi"
    ]

    factory = bool(
        patch_report[
            "patch"
        ][
            "factory"
        ]
    )

    if port_open(
        HOST,
        PORT,
    ):
        raise RuntimeError(
            "8013 portu doğrulama öncesinde kullanımda."
        )

    command = [
        sys.executable,
        "-X",
        "utf8",
        "-m",
        "uvicorn",
        app_import,
        "--host",
        HOST,
        "--port",
        str(
            PORT
        ),
        "--log-level",
        "info",
        "--no-access-log",
    ]

    if factory:
        command.append(
            "--factory"
        )

    stdout_path = Path(
        arguments.stdout
    )

    stderr_path = Path(
        arguments.stderr
    )

    stdout_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    creation_flags = 0

    if os.name == "nt":
        creation_flags = (
            subprocess
            .CREATE_NEW_PROCESS_GROUP
        )

    stdout_handle = stdout_path.open(
        "w",
        encoding="utf-8",
    )

    stderr_handle = stderr_path.open(
        "w",
        encoding="utf-8",
    )

    process: subprocess.Popen[
        str
    ] | None = None

    checks: list[
        dict[str, Any]
    ] = []

    try:
        process = subprocess.Popen(
            command,
            cwd=Path.cwd(),
            stdin=subprocess.DEVNULL,
            stdout=stdout_handle,
            stderr=stderr_handle,
            text=True,
            creationflags=(
                creation_flags
            ),
        )

        wait_for_port(
            process
        )

        with httpx.Client(
            base_url=BASE_URL,
            timeout=httpx.Timeout(
                connect=5.0,
                read=15.0,
                write=10.0,
                pool=5.0,
            ),
            follow_redirects=True,
        ) as client:
            checks.append(
                request_result(
                    client,
                    "GET",
                    "/openapi.json",
                )
            )

            checks.append(
                request_result(
                    client,
                    "GET",
                    "/api/ugr/health",
                )
            )

            checks.append(
                request_result(
                    client,
                    "GET",
                    "/api/ugr/snapshot",
                )
            )

            checks.append(
                request_result(
                    client,
                    "GET",
                    "/api/ugr/preview",
                )
            )

            checks.append(
                request_result(
                    client,
                    "GET",
                    (
                        "/api/ugr/assets/"
                        "web/static/css/"
                        "ugr_dynamic_icons.css"
                    ),
                )
            )

            checks.append(
                request_result(
                    client,
                    "GET",
                    (
                        "/api/ugr/assets/"
                        "web/static/js/"
                        "ugr_dynamic_icons.js"
                    ),
                )
            )

            checks.append(
                request_result(
                    client,
                    "POST",
                    (
                        "/api/ugr/icons/"
                        "sys-001/state"
                    ),
                    json={
                        "durum": "calisiyor",
                        "neden": (
                            "Gerçek FastAPI fabrikası "
                            "canlı doğrulaması."
                        ),
                        "zorla": True,
                    },
                )
            )

            checks.append(
                request_result(
                    client,
                    "POST",
                    "/api/ugr/icons/bulk/state",
                    json={
                        "ikon_kimlikleri": [
                            "sys-001",
                            "sys-002",
                            "sys-003",
                        ],
                        "durum": "uyari",
                        "neden": (
                            "Gerçek FastAPI fabrikası "
                            "toplu canlı doğrulaması."
                        ),
                        "zorla": True,
                    },
                )
            )

        openapi_check = checks[
            0
        ]

        if (
            openapi_check[
                "status_code"
            ]
            != 200
        ):
            raise RuntimeError(
                "OpenAPI uç noktası 200 dönmedi."
            )

        openapi_json = (
            openapi_check[
                "json"
            ]
        )

        if not isinstance(
            openapi_json,
            dict,
        ):
            raise RuntimeError(
                "OpenAPI geçerli JSON dönmedi."
            )

        paths = sorted(
            openapi_json.get(
                "paths",
                {},
            ).keys()
        )

        ugr_paths = [
            path
            for path in paths
            if path.startswith(
                "/api/ugr"
            )
        ]

        required_paths = {
            "/api/ugr/health",
            "/api/ugr/snapshot",
            "/api/ugr/icons",
            "/api/ugr/icons/{ikon_kimligi}",
            "/api/ugr/icons/{ikon_kimligi}/state",
            "/api/ugr/icons/bulk/state",
            "/api/ugr/events",
            "/api/ugr/preview",
            "/api/ugr/assets/{goreli_yol}",
        }

        missing_paths = sorted(
            required_paths
            - set(
                ugr_paths
            )
        )

        if missing_paths:
            raise RuntimeError(
                "Canlı OpenAPI içinde zorunlu UGR yolları eksik: "
                + ", ".join(
                    missing_paths
                )
            )

        health = checks[
            1
        ]

        if (
            health[
                "status_code"
            ]
            != 200
        ):
            raise RuntimeError(
                "/api/ugr/health 200 dönmedi."
            )

        health_json = health[
            "json"
        ]

        if not isinstance(
            health_json,
            dict,
        ):
            raise RuntimeError(
                "UGR sağlık yanıtı JSON değil."
            )

        if (
            health_json.get(
                "toplam_ikon"
            )
            != 215
        ):
            raise RuntimeError(
                "UGR sağlık yanıtında 215 ikon doğrulanamadı."
            )

        snapshot = checks[
            2
        ]

        if (
            snapshot[
                "status_code"
            ]
            != 200
        ):
            raise RuntimeError(
                "/api/ugr/snapshot 200 dönmedi."
            )

        for check in checks[
            3:
        ]:
            if (
                check[
                    "status_code"
                ]
                != 200
            ):
                raise RuntimeError(
                    "Canlı UGR denetimi başarısız: "
                    f"{check['method']} "
                    f"{check['path']} "
                    f"STATUS={check['status_code']}"
                )

        result = {
            "schema": (
                "sykasif.real-fastapi-ugr-live-validation.v1"
            ),
            "app_import": app_import,
            "factory": factory,
            "host": HOST,
            "port": PORT,
            "base_url": BASE_URL,
            "toplam_denetim": len(
                checks
            ),
            "basarili_denetim": len(
                checks
            ),
            "basarisiz_denetim": 0,
            "openapi_toplam_yol": len(
                paths
            ),
            "openapi_ugr_yol_sayisi": len(
                ugr_paths
            ),
            "openapi_ugr_yollari": (
                ugr_paths
            ),
            "health_toplam_ikon": (
                health_json.get(
                    "toplam_ikon"
                )
            ),
            "checks": checks,
            "genel_durum": "basarili",
        }

        output_json = Path(
            arguments.output_json
        )

        output_text = Path(
            arguments.output_text
        )

        output_json.write_text(
            json.dumps(
                result,
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        text_lines = [
            "SPR-011 PAKET-007",
            "GERCEK FASTAPI UGR CANLI DOGRULAMA",
            "",
            f"APP_IMPORT={app_import}",
            f"FACTORY={factory}",
            f"HOST={HOST}",
            f"PORT={PORT}",
            (
                "TOPLAM_DENETIM="
                f"{len(checks)}"
            ),
            (
                "BASARILI_DENETIM="
                f"{len(checks)}"
            ),
            "BASARISIZ_DENETIM=0",
            (
                "OPENAPI_UGR_YOL_SAYISI="
                f"{len(ugr_paths)}"
            ),
            (
                "HEALTH_TOPLAM_IKON="
                f"{health_json.get('toplam_ikon')}"
            ),
            "",
            "DENETIMLER:",
        ]

        for check in checks:
            text_lines.append(
                (
                    f"{check['method']} "
                    f"{check['path']} "
                    f"STATUS={check['status_code']} "
                    f"SURE_MS={check['duration_ms']:.3f}"
                )
            )

        text_lines.extend(
            [
                "",
                "GENEL_DURUM=BASARILI",
                "GERCEK_FASTAPI_UGR_CANLI_DOGRULAMA=TAMAMLANDI",
                "",
            ]
        )

        output_text.write_text(
            "\n".join(
                text_lines
            ),
            encoding="utf-8",
        )

        print(
            "GERCEK_FASTAPI_UGR_CANLI_DOGRULAMA_TAMAMLANDI"
        )
        print(
            f"DOGRU_APP_IMPORT={app_import}"
        )
        print(
            f"DOGRU_FACTORY={factory}"
        )
        print(
            f"OPENAPI_UGR_YOL_SAYISI={len(ugr_paths)}"
        )
        print(
            "HEALTH_TOPLAM_IKON=215"
        )
        print(
            f"TOPLAM_CANLI_DENETIM={len(checks)}"
        )
        print(
            "BASARISIZ_CANLI_DENETIM=0"
        )

        return 0

    finally:
        if process is not None:
            stop_process(
                process
            )

        stdout_handle.close()
        stderr_handle.close()


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
