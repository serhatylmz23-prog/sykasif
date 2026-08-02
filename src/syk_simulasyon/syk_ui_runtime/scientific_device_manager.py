from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from .scientific_adapter import (
    ScientificAdapterRegistry,
    ingest_transport_packet,
)
from .scientific_transport import (
    BleScientificTransport,
    ScientificDevice,
    ScientificTransportError,
    SerialScientificTransport,
    TcpScientificTransport,
)


@dataclass(frozen=True)
class ScientificTransportInfo:
    id: str
    title: str
    discovery_supported: bool
    read_supported: bool


class ScientificDeviceManager:
    def __init__(
        self,
        *,
        adapters: ScientificAdapterRegistry,
        serial_transport: SerialScientificTransport,
        tcp_transport: TcpScientificTransport,
        ble_transport: BleScientificTransport,
    ) -> None:
        self._adapters = adapters

        self._serial = serial_transport
        self._tcp = tcp_transport
        self._ble = ble_transport

    def transports(self) -> list[dict[str, Any]]:
        return [
            asdict(
                ScientificTransportInfo(
                    id="serial",
                    title=self._serial.title,
                    discovery_supported=True,
                    read_supported=True,
                )
            ),
            asdict(
                ScientificTransportInfo(
                    id="tcp",
                    title=self._tcp.title,
                    discovery_supported=False,
                    read_supported=True,
                )
            ),
            asdict(
                ScientificTransportInfo(
                    id="ble",
                    title=self._ble.title,
                    discovery_supported=True,
                    read_supported=True,
                )
            ),
        ]

    def discover_serial(self) -> list[dict[str, Any]]:
        return self._serial.inventory()

    async def discover_ble(
        self,
        *,
        timeout: float = 5.0,
    ) -> list[dict[str, Any]]:
        return await self._ble.inventory(
            timeout=timeout
        )

    async def discover_all(
        self,
        *,
        ble_timeout: float = 5.0,
    ) -> dict[str, Any]:
        serial_error = None
        ble_error = None

        try:
            serial_devices = self.discover_serial()
        except ScientificTransportError as error:
            serial_devices = []
            serial_error = str(error)

        try:
            ble_devices = await self.discover_ble(
                timeout=ble_timeout
            )
        except ScientificTransportError as error:
            ble_devices = []
            ble_error = str(error)

        return {
            "transports": self.transports(),
            "devices": {
                "serial": serial_devices,
                "ble": ble_devices,
                "tcp": [],
            },
            "errors": {
                "serial": serial_error,
                "ble": ble_error,
                "tcp": None,
            },
        }

    def read_serial(
        self,
        *,
        port: str,
        baud_rate: int = 115200,
        timeout: float = 2.0,
    ) -> dict[str, Any]:
        packet = self._serial.read_packet(
            port=port,
            baud_rate=baud_rate,
            timeout=timeout,
        )

        return ingest_transport_packet(
            self._adapters,
            packet,
        )

    def read_tcp(
        self,
        *,
        host: str,
        port: int,
        timeout: float = 3.0,
    ) -> dict[str, Any]:
        packet = self._tcp.read_packet(
            host=host,
            port=port,
            timeout=timeout,
        )

        return ingest_transport_packet(
            self._adapters,
            packet,
        )

    async def read_ble(
        self,
        *,
        address: str,
        characteristic_uuid: str,
        timeout: float = 5.0,
    ) -> dict[str, Any]:
        packet = await self._ble.read_packet(
            address=address,
            characteristic_uuid=characteristic_uuid,
            timeout=timeout,
        )

        return ingest_transport_packet(
            self._adapters,
            packet,
        )