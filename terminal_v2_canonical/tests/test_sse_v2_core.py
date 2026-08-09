from terminal_v2.core.sse import (
    encode_sse,
    heartbeat_snapshot,
    initial_snapshot,
)


def test_sse_encoder():
    text = encode_sse(
        event="terminal.test",
        event_id=7,
        retry=2000,
        data={
            "status": "ok",
        },
    )

    assert "id: 7" in text
    assert "retry: 2000" in text
    assert "event: terminal.test" in text
    assert 'data: {"status":"ok"}' in text
    assert text.endswith("\n\n")


def test_sse_initial_snapshot():
    data = initial_snapshot()

    assert data["terminal"] == "v2"
    assert data["runtime"] == "ONLINE"
    assert data["port"] == 8013
    assert data["transport"] == "SSE"
    assert data["stream"] == "ONLINE"


def test_sse_heartbeat_snapshot():
    data = heartbeat_snapshot()

    assert data["type"] == "heartbeat"
    assert data["runtime"] == "ONLINE"
    assert data["stream"] == "ONLINE"
