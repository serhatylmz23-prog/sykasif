from __future__ import annotations

import argparse
import socket
from dataclasses import dataclass

import uvicorn

from terminal_v2.core.power_guard import PowerGuard


@dataclass(frozen=True, slots=True)
class RuntimeConfig:
    host: str = "0.0.0.0"
    port: int = 8013
    reload: bool = False
    keep_display_on: bool = True


def local_ipv4() -> str:
    sock = socket.socket(
        socket.AF_INET,
        socket.SOCK_DGRAM,
    )

    try:
        sock.connect(
            ("8.8.8.8", 80),
        )

        return str(
            sock.getsockname()[0]
        )
    except OSError:
        return "127.0.0.1"
    finally:
        sock.close()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="SyKaşif Terminal V2 Runtime Host",
    )

    parser.add_argument(
        "--host",
        default="0.0.0.0",
    )

    parser.add_argument(
        "--port",
        type=int,
        default=8013,
    )

    parser.add_argument(
        "--reload",
        action="store_true",
    )

    parser.add_argument(
        "--allow-display-sleep",
        action="store_true",
    )

    return parser


def main() -> int:
    args = build_parser().parse_args()

    config = RuntimeConfig(
        host=args.host,
        port=args.port,
        reload=args.reload,
        keep_display_on=not args.allow_display_sleep,
    )

    guard = PowerGuard(
        keep_display_on=config.keep_display_on,
    )

    guard_status = guard.enable()

    lan_ip = local_ipv4()

    print()
    print("=" * 58)
    print("SYK TERMINAL V2 RUNTIME HOST")
    print("=" * 58)
    print(f"PC URL          : http://127.0.0.1:{config.port}")
    print(f"TABLET URL      : http://{lan_ip}:{config.port}")
    print(f"HOST            : {config.host}")
    print(f"PORT            : {config.port}")
    print(f"POWER GUARD     : {guard_status.active}")
    print(f"DISPLAY ACTIVE  : {config.keep_display_on}")
    print("=" * 58)
    print()

    try:
        uvicorn.run(
            "terminal_v2.app.main:app",
            host=config.host,
            port=config.port,
            reload=config.reload,
            access_log=True,
        )
    finally:
        guard.disable()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
