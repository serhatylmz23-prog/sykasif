import asyncio

from terminal_v2.core.sse import (
    metrics_snapshot,
)


def test_runtime_metrics_snapshot():
    data = asyncio.run(
        metrics_snapshot()
    )

    assert data["type"] == "metrics"
    assert data["runtime"] == "ONLINE"
    assert data["stream"] == "ONLINE"
    assert "active_connections" in data
    assert "active_tablet" in data
    assert "active_desktop" in data
    assert "total_events" in data
