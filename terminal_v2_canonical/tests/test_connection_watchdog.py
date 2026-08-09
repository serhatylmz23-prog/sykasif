import asyncio
from datetime import UTC, datetime, timedelta

from terminal_v2.core.connection_registry import (
    ConnectionRegistry,
    detect_device,
)


def test_detect_device_types():
    assert detect_device(
        "Mozilla Android SM-X920 Tablet"
    ) == "tablet"

    assert detect_device(
        "Mozilla iPad Safari"
    ) == "tablet"

    assert detect_device(
        "Mozilla Windows NT Chrome"
    ) == "desktop"

    assert detect_device(
        "Mozilla iPhone Mobile"
    ) == "mobile"


def test_registry_device_counts():
    async def scenario():
        registry = ConnectionRegistry()

        await registry.connect(
            host="192.168.1.10",
            user_agent="Windows Desktop",
        )

        await registry.connect(
            host="192.168.1.20",
            user_agent="Android SM-X920 Tablet",
        )

        snapshot = await registry.snapshot()

        assert snapshot["active_connections"] == 2
        assert snapshot["active_desktop"] == 1
        assert snapshot["active_tablet"] == 1
        assert snapshot["active_mobile"] == 0

    asyncio.run(scenario())


def test_registry_removes_stale_clients():
    async def scenario():
        registry = ConnectionRegistry(
            stale_after_seconds=5,
        )

        client = await registry.connect(
            host="192.168.1.20",
            user_agent="Android Tablet",
        )

        stale_time = (
            datetime.now(UTC)
            + timedelta(seconds=10)
        )

        removed = await registry.remove_stale(
            now=stale_time,
        )

        assert client.client_id in removed

        snapshot = await registry.snapshot()

        assert snapshot["active_connections"] == 0
        assert snapshot["total_stale_removed"] == 1

    asyncio.run(scenario())
