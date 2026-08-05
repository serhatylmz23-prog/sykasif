from __future__ import annotations

from typing import Any

from syk_core.sensor_gateway import (
    SensorAuthority,
    SensorGateway,
    SensorHealth,
    SensorKind,
    SensorSource,
    sensor_gateway,
)


class SensorGatewayRuntime:
    def __init__(
        self,
        *,
        gateway: SensorGateway,
    ) -> None:
        self._gateway = gateway

    def reset(self) -> None:
        self._gateway.reset()

    def register_source(
        self,
        *,
        source_id: str,
        name: str,
        kind: SensorKind,
        authority: SensorAuthority,
        health: SensorHealth,
        real_device_data: bool,
        simulation_data: bool,
        metadata: dict[str, Any] | None = None,
    ) -> SensorSource:
        source = SensorSource(
            source_id=source_id,
            name=name,
            kind=kind,
            authority=authority,
            health=health,
            real_device_data=real_device_data,
            simulation_data=simulation_data,
            metadata=metadata or {},
        )

        return self._gateway.register_source(
            source
        )

    def ingest(
        self,
        source_id: str,
        *,
        payload: dict[str, Any],
        research_id: str | None = None,
        workspace_id: str | None = None,
        evidence_status: str = "candidate-unverified",
        confidence: float = 0.0,
    ):
        return self._gateway.ingest(
            source_id,
            payload=payload,
            research_id=research_id,
            workspace_id=workspace_id,
            evidence_status=evidence_status,
            confidence=confidence,
        )

    def snapshot(
        self,
    ) -> dict[str, Any]:
        snapshot = self._gateway.snapshot()

        snapshot["manifest_sha256"] = (
            self._gateway.manifest_digest()
        )

        return snapshot

    def list_envelopes(
        self,
        *,
        source_id: str | None = None,
        research_id: str | None = None,
        workspace_id: str | None = None,
    ) -> list[dict[str, Any]]:
        return [
            envelope.to_dict()
            for envelope in (
                self._gateway.list_envelopes(
                    source_id=source_id,
                    research_id=research_id,
                    workspace_id=workspace_id,
                )
            )
        ]


sensor_gateway_runtime = SensorGatewayRuntime(
    gateway=sensor_gateway
)