from __future__ import annotations

from dataclasses import asdict, dataclass
from threading import RLock
from typing import Any, Protocol

from .scientific_runtime import ScientificRuntime
from .scientific_transport import ScientificTransportPacket


@dataclass(frozen=True)
class ScientificAdapterReading:
    module_id: str
    live_value: float | int | str
    confidence: float
    status: str
    source: str
    metadata: dict[str, Any]


class ScientificAdapter(Protocol):
    id: str
    title: str

    def supports(self, module_id: str) -> bool:
        ...

    def read(
        self,
        module_id: str,
        payload: dict[str, Any],
    ) -> ScientificAdapterReading:
        ...


@dataclass(frozen=True)
class AdapterInfo:
    id: str
    title: str
    kind: str
    enabled: bool
    supported_modules: tuple[str, ...]


class SimulatedScientificAdapter:
    id = "simulated"
    title = "Dijital Simülasyon Adaptörü"

    def __init__(
        self,
        supported_modules: list[str],
    ) -> None:
        self._supported_modules = tuple(
            supported_modules
        )

    def supports(self, module_id: str) -> bool:
        return module_id in self._supported_modules

    def read(
        self,
        module_id: str,
        payload: dict[str, Any],
    ) -> ScientificAdapterReading:
        if not self.supports(module_id):
            raise KeyError(module_id)

        if "live_value" not in payload:
            raise ValueError(
                "live_value alanı zorunludur."
            )

        return ScientificAdapterReading(
            module_id=module_id,
            live_value=payload["live_value"],
            confidence=float(
                payload.get("confidence", 50.0)
            ),
            status=str(
                payload.get("status", "preview")
            ),
            source=str(
                payload.get(
                    "source",
                    "simulated_adapter",
                )
            ),
            metadata=dict(
                payload.get("metadata", {})
            ),
        )


class ScientificAdapterRegistry:
    def __init__(
        self,
        runtime: ScientificRuntime,
    ) -> None:
        self._runtime = runtime
        self._lock = RLock()
        self._adapters: dict[
            str,
            ScientificAdapter,
        ] = {}

        simulated = SimulatedScientificAdapter(
            runtime.module_ids()
        )

        self.register(simulated)

    def register(
        self,
        adapter: ScientificAdapter,
    ) -> None:
        with self._lock:
            if adapter.id in self._adapters:
                raise ValueError(
                    f"Adapter already registered: "
                    f"{adapter.id}"
                )

            self._adapters[adapter.id] = adapter

    def exists(self, adapter_id: str) -> bool:
        return adapter_id in self._adapters

    def inventory(self) -> list[dict[str, Any]]:
        result = []

        for adapter in self._adapters.values():
            supported = tuple(
                module_id
                for module_id
                in self._runtime.module_ids()
                if adapter.supports(module_id)
            )

            info = AdapterInfo(
                id=adapter.id,
                title=adapter.title,
                kind=adapter.__class__.__name__,
                enabled=True,
                supported_modules=supported,
            )

            result.append(asdict(info))

        return result

    def ingest(
        self,
        adapter_id: str,
        module_id: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        if adapter_id not in self._adapters:
            raise KeyError(adapter_id)

        if not self._runtime.exists(module_id):
            raise KeyError(module_id)

        adapter = self._adapters[adapter_id]

        reading = adapter.read(
            module_id,
            payload,
        )

        updated = self._runtime.update(
            module_id,
            live_value=reading.live_value,
            confidence=reading.confidence,
            status=reading.status,
            source=reading.source,
        )

        updated["adapter"] = {
            "id": adapter.id,
            "title": adapter.title,
            "metadata": reading.metadata,
        }

        return updated

def ingest_transport_packet(
    registry: ScientificAdapterRegistry,
    packet: ScientificTransportPacket,
) -> dict[str, Any]:
    payload = {
        "live_value": packet.live_value,
        "confidence": packet.confidence,
        "status": packet.status,
        "source": packet.source,
        "metadata": packet.metadata,
    }

    return registry.ingest(
        "simulated",
        packet.module_id,
        payload,
    )