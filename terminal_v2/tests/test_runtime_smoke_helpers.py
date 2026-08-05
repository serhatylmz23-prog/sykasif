from terminal_v2.tests.runtime_smoke import (
    port_is_open,
)


def test_smoke_port_helper_returns_boolean():
    result = port_is_open(
        "127.0.0.1",
        1,
        timeout=0.05,
    )

    assert isinstance(result, bool)
