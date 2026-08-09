from terminal_v2.run_terminal import (
    RuntimeConfig,
    build_parser,
    local_ipv4,
)


def test_runtime_default_config():
    config = RuntimeConfig()

    assert config.host == "0.0.0.0"
    assert config.port == 8013
    assert config.reload is False
    assert config.keep_display_on is True


def test_runtime_argument_parser():
    parser = build_parser()

    args = parser.parse_args(
        [
            "--host",
            "127.0.0.1",
            "--port",
            "9000",
            "--reload",
            "--allow-display-sleep",
        ]
    )

    assert args.host == "127.0.0.1"
    assert args.port == 9000
    assert args.reload is True
    assert args.allow_display_sleep is True


def test_local_ipv4_returns_string():
    address = local_ipv4()

    assert isinstance(address, str)
    assert address
