import asyncio

from terminal_v2.core.connection_registry import (
    ConnectionRegistry,
)


def test_connection_registry_lifecycle():
    async def scenario():
        registry = ConnectionRegistry()

        client = await registry.connect(
            host="192.168.1.20",
            user_agent="Tablet Browser",
        )

        first = await registry.snapshot()

        assert first["active_connections"] == 1
        assert first["total_connections"] == 1
        assert first["total_events"] == 0
        assert first["clients"][0]["client_id"] == client.client_id

        recorded = await registry.record_event(
            client.client_id,
        )

        assert recorded is True

        second = await registry.snapshot()

        assert second["total_events"] == 1
        assert second["clients"][0]["event_count"] == 1

        disconnected = await registry.disconnect(
            client.client_id,
        )

        assert disconnected is True

        final = await registry.snapshot()

        assert final["active_connections"] == 0
        assert final["total_connections"] == 1

    asyncio.run(scenario())


def test_connection_registry_unknown_client():
    async def scenario():
        registry = ConnectionRegistry()

        assert (
            await registry.record_event("unknown")
            is False
        )

        assert (
            await registry.disconnect("unknown")
            is False
        )

    asyncio.run(scenario())
